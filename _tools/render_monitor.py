#!/usr/bin/env python3
"""
Bloxbury Render Monitor
=======================
Watches every render you have going (on your laptop or on RunPod pods) and
shows one named progress bar per render: frames done, %, speed, time left and
the clock time it should finish. Renders that belong to the same episode can
share a "group" so you also get one combined bar for the whole episode.

Needs only a normal Python 3 install (tkinter comes with it on Windows).

  python render_monitor.py            -> opens the window
  python render_monitor.py --text     -> same info in the terminal instead
  python render_monitor.py --once     -> print status once and exit

Renders are found three ways:
  1. Watch folders: any folder (up to 3 levels down) containing a
     render_job.json file, e.g. {"name": "Part 1 - pod A", "group": "Part 1",
     "total": 1322}. Frames are counted in that folder (or in its "frames"
     sub-path if the file says so).
  2. RunPod pods: give the pod id + Jupyter token ("Add RunPod pod" button).
     The pod's /workspace/render_job.json says what it is rendering.
  3. Manual jobs in render_jobs.json (created next to this script).
"""
import argparse, datetime, json, os, re, sys, threading, time, urllib.request
from collections import deque

IMG_EXT = {".png", ".exr", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "render_jobs.json")
DEFAULT_CONFIG = {
    "watch_folders": [],          # e.g. ["C:/Users/frimp/Downloads/robloxshorts/series"]
    "jobs": [],                   # manual / RunPod jobs
    "poll_seconds": 5,            # local folders
    "remote_poll_seconds": 20,    # RunPod pods
}

# ---------------------------------------------------------------- config ---
def load_config(path=CONFIG_PATH):
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            print("Could not read", path, "-", e)
    else:
        save_config(cfg, path)
    return cfg

def save_config(cfg, path=CONFIG_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

# -------------------------------------------------------- frame counting ---
_num = re.compile(r"(\d+)(?!.*\d)")

def frame_number(fname):
    m = _num.search(os.path.splitext(fname)[0])
    return int(m.group(1)) if m else None

def in_range(fname, fs, fe):
    if fs is None and fe is None:
        return True
    n = frame_number(fname)
    if n is None:
        return False
    return (fs is None or n >= fs) and (fe is None or n <= fe)

def count_local(folder, fs=None, fe=None):
    n = 0
    newest = 0.0
    with os.scandir(folder) as it:
        for e in it:
            if not e.is_file():
                continue
            if os.path.splitext(e.name)[1].lower() not in IMG_EXT:
                continue
            st = e.stat()
            if st.st_size == 0:          # Blender placeholder for a frame in progress
                continue
            if in_range(e.name, fs, fe):
                n += 1
                newest = max(newest, st.st_mtime)
    return n, newest

def _jupyter_get(pod_id, token, path, timeout=15):
    url = "https://%s-8888.proxy.runpod.net/api/contents/%s?content=1&token=%s" % (
        pod_id, urllib.request.quote(path.strip("/")), token)
    req = urllib.request.Request(url, headers={"User-Agent": "bloxbury-render-monitor"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def remote_job_info(pod_id, token):
    """Reads /workspace/render_job.json on the pod (written by our render scripts)."""
    try:
        d = _jupyter_get(pod_id, token, "workspace/render_job.json")
        return json.loads(d.get("content") or "{}")
    except Exception:
        return {}

def count_remote(pod_id, token, remote_dir, fs=None, fe=None):
    d = _jupyter_get(pod_id, token, remote_dir)
    n = 0
    for e in d.get("content") or []:
        if e.get("type") != "file":
            continue
        name = e.get("name", "")
        if os.path.splitext(name)[1].lower() not in IMG_EXT:
            continue
        if (e.get("size") or 0) == 0:
            continue
        if in_range(name, fs, fe):
            n += 1
    return n

# ------------------------------------------------------------------ jobs ---
class Job:
    def __init__(self, spec):
        self.spec = dict(spec)
        self.done = 0
        self.status = "waiting"        # waiting / rendering / stalled / done / offline / error
        self.error = ""
        self.samples = deque(maxlen=400)   # (time, frames done)
        self.last_change = None
        self.first_seen = time.time()
        self.finished_at = None
        self.alerted = False
        self.next_poll = 0.0

    # spec helpers
    @property
    def key(self):
        s = self.spec
        return s.get("path") or "%s:%s" % (s.get("pod_id"), s.get("remote_dir", ""))
    @property
    def name(self):
        return self.spec.get("name") or os.path.basename(str(self.spec.get("path", ""))) or self.spec.get("pod_id", "render")
    @property
    def group(self):
        return self.spec.get("group") or ""
    @property
    def total(self):
        s = self.spec
        if s.get("total"):
            return int(s["total"])
        if s.get("frame_start") is not None and s.get("frame_end") is not None:
            return int(s["frame_end"]) - int(s["frame_start"]) + 1
        return 0
    @property
    def kind(self):
        return self.spec.get("kind") or ("runpod" if self.spec.get("pod_id") else "local")

    def poll(self, cfg):
        now = time.time()
        if now < self.next_poll:
            return
        s = self.spec
        fs, fe = s.get("frame_start"), s.get("frame_end")
        try:
            if self.kind == "runpod":
                self.next_poll = now + cfg.get("remote_poll_seconds", 20)
                if not s.get("_info_loaded"):
                    info = remote_job_info(s["pod_id"], s["token"])
                    for k, v in info.items():
                        if not s.get(k):         # what you typed wins over the pod's file
                            s[k] = v
                    s["_info_loaded"] = True
                    fs, fe = s.get("frame_start"), s.get("frame_end")
                n = count_remote(s["pod_id"], s["token"], s.get("remote_dir", "workspace/frames"), fs, fe)
            else:
                self.next_poll = now + cfg.get("poll_seconds", 5)
                folder = s["path"]
                if s.get("frames"):
                    folder = os.path.join(folder, s["frames"])
                if not os.path.isdir(folder):
                    self.status, self.error = "waiting", "folder not created yet"
                    return
                n, _ = count_local(folder, fs, fe)
            self.error = ""
            self._update(n, now)
        except Exception as e:
            if self.kind == "runpod":
                self.status = "done" if self.total and self.done >= self.total else "offline"
                self.error = "pod not reachable (stopped or deleted?)"
            else:
                self.status, self.error = "error", str(e)[:80]

    def _update(self, n, now):
        if n != self.done or not self.samples:
            if self.samples and n > self.done:
                self.last_change = now
            self.done = n
            self.samples.append((now, n))
        tot = self.total
        if tot and n >= tot:
            if self.status != "done":
                self.finished_at = now
            self.status = "done"
            return
        spf = self.sec_per_frame()
        if self.last_change is None:
            self.status = "waiting" if n == 0 else "rendering"
        else:
            quiet = now - self.last_change
            limit = max(120.0, (spf or 0) * 6)
            self.status = "stalled" if quiet > limit else "rendering"

    def sec_per_frame(self):
        """Recent speed: frames over the last ~3 minutes (falls back to all samples)."""
        if len(self.samples) < 2:
            return None
        t1, n1 = self.samples[-1]
        t0, n0 = self.samples[0]
        for t, n in self.samples:
            if t1 - t <= 180:
                t0, n0 = t, n
                break
        if n1 - n0 <= 0:
            t0, n0 = self.samples[0]
        if n1 - n0 <= 0 or t1 - t0 <= 0:
            return None
        return (t1 - t0) / (n1 - n0)

    def eta_seconds(self):
        if self.status == "done":
            return 0
        if self.status in ("stalled", "offline", "error"):
            return None                              # no honest countdown while it isn't moving
        spf = self.sec_per_frame()
        if not spf or not self.total:
            return None
        left = max(self.total - self.done, 0) * spf
        if self.last_change:                       # count time already spent on the next frame
            left = max(left - (time.time() - self.last_change), spf * 0.1 * (self.total - self.done))
        return left

    def fraction(self):
        return min(self.done / self.total, 1.0) if self.total else 0.0

# ------------------------------------------------------------- discovery ---
def discover(cfg):
    specs = []
    for root in cfg.get("watch_folders", []):
        root = os.path.expanduser(root)
        if not os.path.isdir(root):
            continue
        base_depth = root.rstrip("\\/").count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - base_depth >= 3:
                dirnames[:] = []
            if "render_job.json" in filenames:
                try:
                    with open(os.path.join(dirpath, "render_job.json"), encoding="utf-8") as f:
                        d = json.load(f)
                    d["path"] = dirpath
                    d.setdefault("kind", "local")
                    specs.append(d)
                except Exception:
                    pass
    for j in cfg.get("jobs", []):
        specs.append(dict(j))
    return specs

class Monitor:
    def __init__(self, cfg_path=CONFIG_PATH):
        self.cfg_path = cfg_path
        self.cfg = load_config(cfg_path)
        self.jobs = {}
        self.lock = threading.Lock()
        self.refresh_jobs()

    def refresh_jobs(self):
        self.cfg = load_config(self.cfg_path)
        specs = discover(self.cfg)
        with self.lock:
            seen = set()
            for s in specs:
                j = Job(s)
                if j.key in self.jobs:
                    old = self.jobs[j.key]
                    for k, v in s.items():       # keep live data, take new names/totals
                        old.spec[k] = v
                else:
                    self.jobs[j.key] = j
                seen.add(j.key)
            for k in list(self.jobs):
                if k not in seen:
                    del self.jobs[k]

    def poll_all(self):
        for j in list(self.jobs.values()):
            j.poll(self.cfg)

    def add_job(self, spec):
        self.cfg.setdefault("jobs", []).append(spec)
        save_config(self.cfg, self.cfg_path)
        self.refresh_jobs()

    def remove_job(self, key):
        self.cfg["jobs"] = [s for s in self.cfg.get("jobs", []) if Job(s).key != key]
        save_config(self.cfg, self.cfg_path)
        self.refresh_jobs()

    def rows(self):
        """Ordered list of ('group', name, members) and ('job', job) for display."""
        with self.lock:
            jobs = list(self.jobs.values())
        groups = {}
        for j in jobs:
            groups.setdefault(j.group, []).append(j)
        out = []
        for g in sorted(groups, key=lambda x: (x == "", x)):
            members = sorted(groups[g], key=lambda j: j.name)
            if g and len(members) > 1:
                out.append(("group", g, members))
            for j in members:
                out.append(("job", j))
        return out

# ----------------------------------------------------------- formatting ---
def fmt_dur(sec):
    if sec is None:
        return "--"
    sec = int(round(sec))
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    if h:
        return "%dh %02dm" % (h, m)
    if m:
        return "%dm %02ds" % (m, s)
    return "%ds" % s

def fmt_clock(sec_from_now):
    if sec_from_now is None:
        return "--:--"
    return (datetime.datetime.now() + datetime.timedelta(seconds=sec_from_now)).strftime("%H:%M")

def group_summary(members):
    total = sum(j.total for j in members)
    done = sum(min(j.done, j.total) if j.total else j.done for j in members)
    etas = [j.eta_seconds() for j in members]
    # pods run side by side, so the slowest one decides when the episode is done
    eta = max(etas) if all(e is not None for e in etas) else None
    def short(j):                      # "Part 1 - pod A (frames 1-880)" -> "pod A"
        n = re.sub(r"\s*\(.*?\)", "", j.name)
        g = re.escape(j.group)
        return re.sub(r"^%s\s*[-:]\s*" % g, "", n) or n
    waiting_on = [short(j) for j in members if j.status != "done"]
    return total, done, eta, waiting_on

def job_line(j):
    spf = j.sec_per_frame()
    eta = j.eta_seconds()
    pct = j.fraction() * 100
    parts = ["%s/%s" % (format(j.done, ","), format(j.total, ",") if j.total else "?"),
             "%.0f%%" % pct]
    if j.status == "done":
        parts.append("DONE")
    else:
        parts += ["%.1f s/frame" % spf if spf else "speed: measuring...",
                  "%s left" % fmt_dur(eta), "finish ~%s" % fmt_clock(eta),
                  j.status.upper()]
    if j.error:
        parts.append("(%s)" % j.error)
    return "   ·   ".join(parts)

# ------------------------------------------------------------- text mode ---
def bar(frac, width=30):
    full = int(round(frac * width))
    return "[" + "#" * full + "-" * (width - full) + "]"

def text_mode(mon, once=False):
    while True:
        mon.refresh_jobs()
        mon.poll_all()
        if not once:
            os.system("cls" if os.name == "nt" else "clear")
        print("BLOXBURY RENDER MONITOR   %s" % datetime.datetime.now().strftime("%H:%M:%S"))
        rows = mon.rows()
        if not rows:
            print("No renders found. Add watch_folders or jobs to", mon.cfg_path)
        for r in rows:
            if r[0] == "group":
                total, done, eta, waiting = group_summary(r[2])
                frac = done / total if total else 0
                print("\n== %s  %s %.0f%%  %s left, finish ~%s" % (r[1], bar(frac), frac * 100, fmt_dur(eta), fmt_clock(eta)))
                if waiting:
                    print("   waiting on: " + ", ".join(waiting))
            else:
                j = r[1]
                print("  %-24s %s %s" % (j.name[:24], bar(j.fraction()), job_line(j)))
        if once:
            return
        time.sleep(2)

# --------------------------------------------------------------- window ----
def gui_mode(mon):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    BG, FG, SUB = "#16181d", "#e8e8ea", "#9aa0aa"
    COL = {"rendering": "#3b82f6", "done": "#22c55e", "stalled": "#f59e0b",
           "waiting": "#6b7280", "offline": "#6b7280", "error": "#ef4444"}

    root = tk.Tk()
    root.title("Bloxbury Render Monitor")
    root.configure(bg=BG)
    root.geometry("820x480")
    style = ttk.Style(root)
    style.theme_use("clam")
    for st, c in COL.items():
        style.configure("%s.Horizontal.TProgressbar" % st, troughcolor="#2a2e36",
                        background=c, bordercolor="#2a2e36", lightcolor=c, darkcolor=c)

    top = tk.Frame(root, bg=BG)
    top.pack(fill="x", padx=12, pady=(10, 4))
    tk.Label(top, text="Renders", bg=BG, fg=FG, font=("Segoe UI", 15, "bold")).pack(side="left")
    clock = tk.Label(top, text="", bg=BG, fg=SUB, font=("Segoe UI", 10))
    clock.pack(side="left", padx=10)

    def add_folder():
        d = filedialog.askdirectory(title="Folder the frames are saved into")
        if not d:
            return
        form(d)

    def form(folder=None):
        w = tk.Toplevel(root, bg=BG)
        w.title("Add render")
        fields = [("Name", "name", os.path.basename(folder) if folder else ""),
                  ("Group (episode)", "group", ""), ("Total frames", "total", "")]
        if not folder:
            fields += [("Pod id", "pod_id", ""), ("Jupyter token", "token", ""),
                       ("Frames folder on pod", "remote_dir", "workspace/frames")]
        ents = {}
        for i, (lab, key, val) in enumerate(fields):
            tk.Label(w, text=lab, bg=BG, fg=FG).grid(row=i, column=0, sticky="w", padx=8, pady=3)
            e = tk.Entry(w, width=36)
            e.insert(0, val)
            e.grid(row=i, column=1, padx=8, pady=3)
            ents[key] = e
        if not folder:
            tk.Label(w, text="Name / group / total can stay empty if the pod has render_job.json",
                     bg=BG, fg=SUB).grid(row=len(fields), column=0, columnspan=2, padx=8)

        def ok():
            spec = {k: e.get().strip() for k, e in ents.items() if e.get().strip()}
            if "total" in spec:
                try:
                    spec["total"] = int(spec["total"])
                except ValueError:
                    messagebox.showerror("Add render", "Total frames must be a number")
                    return
            if folder:
                spec.update(kind="local", path=folder)
            else:
                if not spec.get("pod_id") or not spec.get("token"):
                    messagebox.showerror("Add render", "Pod id and token are needed")
                    return
                spec["kind"] = "runpod"
            mon.add_job(spec)
            w.destroy()
        tk.Button(w, text="Add", command=ok).grid(row=len(fields) + 1, column=1, sticky="e", padx=8, pady=8)

    def open_cfg():
        if os.name == "nt":
            os.startfile(mon.cfg_path)
        else:
            messagebox.showinfo("Config", mon.cfg_path)

    for txt, cmd in (("Settings file", open_cfg), ("Add RunPod pod", lambda: form(None)),
                     ("Add local folder", add_folder)):
        tk.Button(top, text=txt, command=cmd).pack(side="right", padx=3)

    canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
    sb = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    body = tk.Frame(canvas, bg=BG)
    body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=body, anchor="nw")
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True, padx=(12, 0))
    sb.pack(side="right", fill="y")

    widgets = {}   # row key -> (frame, title, bar, info)

    def make_row(key, title_font):
        f = tk.Frame(body, bg=BG)
        t = tk.Label(f, text="", bg=BG, fg=FG, font=title_font, anchor="w")
        t.pack(fill="x")
        b = ttk.Progressbar(f, orient="horizontal", length=760, mode="determinate", maximum=1000)
        b.pack(fill="x", pady=2)
        i = tk.Label(f, text="", bg=BG, fg=SUB, font=("Segoe UI", 9), anchor="w")
        i.pack(fill="x")
        widgets[key] = (f, t, b, i)
        return widgets[key]

    def poller():
        while True:
            try:
                mon.refresh_jobs()
                mon.poll_all()
            except Exception as e:
                print("poll error:", e)
            time.sleep(2)

    threading.Thread(target=poller, daemon=True).start()

    def alert(j):
        try:
            root.bell()
            if os.name == "nt":
                import winsound
                winsound.MessageBeep()
        except Exception:
            pass
        root.title("✔ %s finished - Bloxbury Render Monitor" % j.name)

    def tick():
        clock.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
        rows = mon.rows()
        order = []
        for r in rows:
            if r[0] == "group":
                key = "g:" + r[1]
                total, done, eta, waiting = group_summary(r[2])
                fr = done / total if total else 0
                f, t, b, i = widgets.get(key) or make_row(key, ("Segoe UI", 12, "bold"))
                st = "done" if not waiting else ("stalled" if any(j.status == "stalled" for j in r[2]) else "rendering")
                b.configure(value=fr * 1000, style="%s.Horizontal.TProgressbar" % st)
                t.config(text="%s   %.0f%%" % (r[1], fr * 100))
                i.config(text=("All parts done" if not waiting else
                               "%s/%s frames   ·   %s left   ·   finish ~%s   ·   waiting on: %s" % (
                                   format(done, ","), format(total, ","), fmt_dur(eta), fmt_clock(eta), ", ".join(waiting))))
            else:
                j = r[1]
                key = "j:" + j.key
                f, t, b, i = widgets.get(key) or make_row(key, ("Segoe UI", 10, "bold"))
                b.configure(value=j.fraction() * 1000, style="%s.Horizontal.TProgressbar" % j.status)
                t.config(text="   " + j.name if j.group else j.name)
                i.config(text=("   " if j.group else "") + job_line(j))
                if j.status == "done" and not j.alerted:
                    j.alerted = True
                    if time.time() - j.first_seen > 10:     # don't beep for renders already done at start
                        alert(j)
            order.append(key)
        for key in list(widgets):
            if key not in order:
                widgets.pop(key)[0].destroy()
        for key in order:
            widgets[key][0].pack_forget()
        for key in order:
            widgets[key][0].pack(fill="x", pady=(8 if key.startswith("g:") else 3, 3))
        if not order:
            if "empty" not in widgets:
                f = tk.Frame(body, bg=BG)
                tk.Label(f, text="No renders yet. Use 'Add local folder' or 'Add RunPod pod',\n"
                                 "or add watch folders in the settings file.", bg=BG, fg=SUB,
                         justify="left").pack(anchor="w")
                f.pack(fill="x", pady=20)
                widgets["empty"] = (f, None, None, None)
        elif "empty" in widgets:
            widgets.pop("empty")[0].destroy()
        root.after(1000, tick)

    tick()
    root.mainloop()

# ------------------------------------------------------------------ main ---
def main():
    ap = argparse.ArgumentParser(description="Bloxbury Render Monitor")
    ap.add_argument("--text", action="store_true", help="show in the terminal instead of a window")
    ap.add_argument("--once", action="store_true", help="print status once and exit")
    ap.add_argument("--config", default=CONFIG_PATH, help="settings file (default: render_jobs.json next to this script)")
    a = ap.parse_args()
    mon = Monitor(a.config)
    if a.text or a.once:
        text_mode(mon, once=a.once)
    else:
        gui_mode(mon)

if __name__ == "__main__":
    main()
