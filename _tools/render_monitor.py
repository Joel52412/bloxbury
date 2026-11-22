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
    "local_poll_s": 2,            # laptop folders (just counts files: costs nothing)
    "remote_poll_s": 5,           # RunPod pods: reads the pod's tiny render_progress.json (a few hundred bytes)
}
# older settings files used poll_seconds / remote_poll_seconds (5 / 20); the new keys above replace them

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

POD_URL_FMT = "https://%s-8888.proxy.runpod.net"     # tests point this at a local mock pod
def pod_url(pod_id):
    return POD_URL_FMT.replace("%s", pod_id.strip())

def _jupyter_get(pod_id, token, path, timeout=30):
    url = pod_url(pod_id) + "/api/contents/%s?content=1&token=%s" % (
        urllib.request.quote(path.strip("/")), token.strip())
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

def remote_progress(pod_id, token):
    """The pod's /workspace/render_progress.json, written every 2 s by _pipeline/pod_progress.py (tiny)."""
    d = _jupyter_get(pod_id, token, "workspace/render_progress.json", timeout=8)
    return json.loads(d.get("content") or "{}")

def remote_output(pod_id, token):
    """The pod's /workspace/render_output.json (pod_finish.sh): stage rendering/checking/assembling/ready/received..."""
    d = _jupyter_get(pod_id, token, "workspace/render_output.json", timeout=8)
    return json.loads(d.get("content") or "{}")

ROOT = os.path.dirname(HERE)          # the robloxshorts folder (this script lives in robloxshorts/_tools)

def download_file(pod_id, token, remote, dest, expect_size, progress=None):
    """Streams https://<pod>-8888.proxy.runpod.net/files/<remote> to dest (via dest.part). Returns bytes written."""
    url = pod_url(pod_id) + "/files/%s?token=%s" % (urllib.request.quote(remote.strip("/")), token.strip())
    req = urllib.request.Request(url, headers={"User-Agent": "bloxbury-render-monitor"})
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    tmp, n = dest + ".part", 0
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b); n += len(b)
            if progress: progress(n)
    if expect_size and n != int(expect_size):
        os.remove(tmp)
        raise IOError("download was %d bytes, pod says %d" % (n, int(expect_size)))
    os.replace(tmp, dest)
    return n

def send_receipt(pod_id, token, size):
    """Writes /workspace/received.json on the pod: pod_finish.sh sees it and deletes the pod."""
    url = pod_url(pod_id) + "/api/contents/workspace/received.json?token=%s" % token.strip()
    body = json.dumps({"type": "file", "format": "text",
                       "content": json.dumps({"size": int(size), "at": time.time()})}).encode()
    req = urllib.request.Request(url, data=body, method="PUT",
                                 headers={"Content-Type": "application/json", "User-Agent": "bloxbury-render-monitor"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status

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
        self.pod = None                    # last render_progress.json from the pod
        self.pod_rx = 0.0                  # when we received it (laptop clock)
        self.next_listing = 0.0            # fallback folder listing, at most every 30 s
        self.out = {}                      # last render_output.json (pod_finish.sh)
        self.delivery = ""                 # "" / downloading / saved / failed
        self.dl_bytes = 0
        self.saved_path = ""

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
                self.next_poll = now + cfg.get("remote_poll_s", 5)
                if not s.get("_info_loaded"):
                    info = remote_job_info(s["pod_id"], s["token"])
                    for k, v in info.items():
                        if not s.get(k):         # what you typed wins over the pod's file
                            s[k] = v
                    if info:                     # keep retrying until the pod's render_job.json is readable
                        s["_info_loaded"] = True
                    fs, fe = s.get("frame_start"), s.get("frame_end")
                prog = None
                try:
                    prog = remote_progress(s["pod_id"], s["token"])
                except Exception:
                    prog = None
                if (prog and prog.get("finished")) or self.out:
                    self._check_output(s)
                if prog and "done" in prog:
                    self.pod, self.pod_rx = prog, now
                    n = int(prog["done"])
                    if prog.get("total") and not s.get("total"):
                        s["total"] = int(prog["total"])
                elif now >= self.next_listing:          # older pods without the progress file: list the folder, slowly
                    self.next_listing = now + 30
                    n = count_remote(s["pod_id"], s["token"], s.get("remote_dir", "workspace/frames"), fs, fe)
                else:
                    return
            else:
                self.next_poll = now + cfg.get("local_poll_s", 2)
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
                self.error = "" if self.delivery == "saved" else "pod not reachable (stopped or deleted?)"
            else:
                self.status, self.error = "error", str(e)[:80]

    def _check_output(self, s):
        """Finished render: follow pod_finish.sh, download the video when it is ready, then send the receipt."""
        try:
            self.out = remote_output(s["pod_id"], s["token"]) or self.out
        except Exception:
            return
        if self.out.get("stage") == "ready" and self.delivery in ("", "failed") and s.get("auto_download", True):
            self.delivery = "downloading"
            threading.Thread(target=self._deliver, args=(dict(s), dict(self.out)), daemon=True).start()

    def _deliver(self, s, out):
        remote = out.get("file") or ""
        rel = s.get("download_to") or os.path.join("series", s.get("group_dir", "bloxbury"), os.path.basename(remote))
        dest = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
        if os.path.exists(dest):                       # never overwrite an earlier version
            b, e = os.path.splitext(dest); dest = "%s_%s%s" % (b, datetime.datetime.now().strftime("%H%M"), e)
        for attempt in range(3):
            try:
                def prog(n): self.dl_bytes = n
                download_file(s["pod_id"], s["token"], remote, dest, out.get("size"), prog)
                self.saved_path = dest
                send_receipt(s["pod_id"], s["token"], out.get("size") or os.path.getsize(dest))
                self.delivery = "saved"
                return
            except Exception as e:
                self.error = "download: %s" % str(e)[:70]
                time.sleep(5)
        self.delivery = "failed"

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
        """Recent speed. Pods report it themselves (all GPUs together); otherwise frames over the last ~90 s."""
        if self.pod and self.pod.get("fps_60s") and time.time() - self.pod_rx < 60:
            return 1.0 / self.pod["fps_60s"]
        if len(self.samples) < 2:
            return None
        t1, n1 = self.samples[-1]
        t0, n0 = self.samples[0]
        for t, n in self.samples:
            if t1 - t <= 90:
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
        if self.pod and self.pod.get("eta_s") is not None and time.time() - self.pod_rx < 60:
            # the pod knows each GPU's speed; the slowest GPU decides when it is really finished
            return max(0.0, float(self.pod["eta_s"]) - (time.time() - self.pod_rx))
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
    hidden = set(cfg.get("hidden", []))
    return [d for d in specs if Job(d).key not in hidden]

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
        before = len(self.cfg.get("jobs", []))
        self.cfg["jobs"] = [s for s in self.cfg.get("jobs", []) if Job(s).key != key]
        if len(self.cfg["jobs"]) == before:      # found by a watch folder: hide it instead
            self.cfg.setdefault("hidden", []).append(key)
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

GBP_PER_USD = 0.79

def job_cost(j):
    """(spent_usd, estimated_total_usd) from cost_per_hr + pod_started in render_job.json."""
    rate, started = j.spec.get("cost_per_hr"), j.spec.get("pod_started")
    if not rate or not started:
        return None
    try:
        t0 = datetime.datetime.fromisoformat(str(started).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None
    spent = max(0.0, time.time() - t0) / 3600 * float(rate)
    eta = j.eta_seconds()
    total = spent + (eta / 3600 * float(rate) if eta and j.status != "done" else 0)
    return spent, total

def money(usd):
    return "$%.2f (~%.0fp)" % (usd, usd * GBP_PER_USD * 100) if usd * GBP_PER_USD < 1 else \
           "$%.2f (~£%.2f)" % (usd, usd * GBP_PER_USD)

def job_started(j):
    """Start time: the pod's createdAt (render_job.json pod_started) if known, else when the monitor first saw the job."""
    st = j.spec.get("render_started") or j.spec.get("pod_started")
    if st:
        try:
            return datetime.datetime.fromisoformat(str(st).replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return j.first_seen

def job_elapsed(j):
    if j.status == "done":
        if not getattr(j, "done_at", None):
            j.done_at = time.time()
        end = j.done_at
    else:
        j.done_at = None
        end = time.time()
    return max(0.0, end - job_started(j))

def job_line(j):
    spf = j.sec_per_frame()
    eta = j.eta_seconds()
    pct = j.fraction() * 100
    parts = ["%s/%s" % (format(j.done, ","), format(j.total, ",") if j.total else "?"),
             "%.0f%%" % pct]
    if j.status == "done":
        parts += ["DONE", "took %s" % fmt_dur(job_elapsed(j))]
    else:
        parts.append("running %s" % fmt_dur(job_elapsed(j)))
        parts += ["%.1f s/frame" % spf if spf else "speed: measuring...",
                  "%s left" % fmt_dur(eta), "finish ~%s" % fmt_clock(eta),
                  j.status.upper()]
    c = job_cost(j)
    if c:
        parts.append("spent %s" % money(c[0]))
        if j.status != "done":
            parts.append("est. total %s" % money(c[1]))
    if j.delivery == "downloading":
        parts.append("downloading video %.1f MB" % (j.dl_bytes / 1e6))
    elif j.delivery == "saved":
        parts.append("SAVED %s, pod deleting itself" % j.saved_path)
    elif j.out.get("stage") and j.out.get("stage") not in ("rendering", "received"):
        parts.append("pod: %s" % j.out["stage"])
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
        time.sleep(1)

# --------------------------------------------------------------- window ----
def pod_link(j):
    s = j.spec
    if j.kind != "runpod" or not s.get("pod_id"):
        return None
    return "https://%s-8888.proxy.runpod.net/tree/%s?token=%s" % (s["pod_id"].strip(), s.get("remote_dir", "workspace/frames"), s["token"].strip())

def gui_mode(mon):
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import webbrowser

    BG, CARD, LINE, FG, SUB, DIM = "#101217", "#191c23", "#262a33", "#eceef2", "#a3a9b4", "#6b7280"
    COL = {"rendering": "#3b82f6", "done": "#22c55e", "stalled": "#f59e0b",
           "waiting": "#6b7280", "offline": "#6b7280", "error": "#ef4444"}
    LABEL = {"rendering": "RENDERING", "done": "DONE", "stalled": "STALLED", "waiting": "WAITING",
             "offline": "OFFLINE", "error": "ERROR"}
    F = lambda size, w="normal": ("Segoe UI", size, w)

    root = tk.Tk()
    root.title("Bloxbury Render Monitor")
    root.configure(bg=BG)
    root.geometry("980x560")
    root.minsize(640, 300)

    top = tk.Frame(root, bg=BG)
    top.pack(fill="x", padx=16, pady=(12, 6))
    tk.Label(top, text="Renders", bg=BG, fg=FG, font=F(16, "bold")).pack(side="left")
    clock = tk.Label(top, text="", bg=BG, fg=DIM, font=F(10))
    clock.pack(side="left", padx=10, pady=(6, 0))

    def btn(parent, text, cmd, fg=FG):
        b = tk.Label(parent, text=text, bg=LINE, fg=fg, font=F(9, "bold"), padx=10, pady=4, cursor="hand2")
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>", lambda e: b.config(bg="#333846")); b.bind("<Leave>", lambda e: b.config(bg=LINE))
        return b

    def add_folder():
        d = filedialog.askdirectory(title="Folder the frames are saved into")
        if d:
            form(d)

    def form(folder=None):
        w = tk.Toplevel(root, bg=BG)
        w.title("Add RunPod pod" if not folder else "Watch laptop folder")
        fields = [("Name", "name", os.path.basename(folder)), ("Total frames", "total", "")] if folder else \
                 [("Pod id", "pod_id", ""), ("Jupyter token", "token", "")]
        ents = {}
        for i, (lab, key, val) in enumerate(fields):
            tk.Label(w, text=lab, bg=BG, fg=FG, font=F(10)).grid(row=i, column=0, sticky="w", padx=10, pady=4)
            e = tk.Entry(w, width=38, bg=CARD, fg=FG, insertbackground=FG, relief="flat")
            e.insert(0, val); e.grid(row=i, column=1, padx=10, pady=4); ents[key] = e
        tk.Label(w, text=("Claude sends both of these the moment a render starts." if not folder else
                          "Total frames is optional (gives % and time left)."), bg=BG, fg=SUB,
                 font=F(9)).grid(row=len(fields), column=0, columnspan=2, padx=10)

        def ok():
            spec = {k: e.get().strip() for k, e in ents.items() if e.get().strip()}
            if "total" in spec:
                try: spec["total"] = int(spec["total"])
                except ValueError:
                    messagebox.showerror("Add render", "Total frames must be a number"); return
            if folder:
                spec.update(kind="local", path=folder)
            else:
                if not spec.get("pod_id") or not spec.get("token"):
                    messagebox.showerror("Add render", "Pod id and token are needed"); return
                spec["kind"] = "runpod"
            mon.add_job(spec); w.destroy()
        btn(w, "Add", ok).grid(row=len(fields) + 1, column=1, sticky="e", padx=10, pady=10)

    def open_cfg():
        if os.name == "nt": os.startfile(mon.cfg_path)
        else: messagebox.showinfo("Settings", mon.cfg_path)

    for txt, cmd in (("Settings", open_cfg), ("+ RunPod pod", lambda: form(None)), ("+ Laptop folder", add_folder)):
        btn(top, txt, cmd).pack(side="right", padx=4)

    canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
    sb = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    body = tk.Frame(canvas, bg=BG)
    body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    win = canvas.create_window((0, 0), window=body, anchor="nw")
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=(0, 12))
    sb.pack(side="right", fill="y")

    cards = {}

    class Card:
        def __init__(self, key, j):
            self.key = key
            self.f = tk.Frame(body, bg=CARD, highlightthickness=1, highlightbackground=LINE)
            hdr = tk.Frame(self.f, bg=CARD); hdr.pack(fill="x", padx=14, pady=(12, 4))
            self.title = tk.Label(hdr, text="", bg=CARD, fg=FG, font=F(13, "bold"), anchor="w")
            self.title.pack(side="left")
            self.pill = tk.Label(hdr, text="", bg=CARD, fg="white", font=F(8, "bold"), padx=8, pady=1)
            self.pill.pack(side="left", padx=10)
            def remove(k=key):
                if messagebox.askyesno("Remove", "Stop watching \"%s\"?\n(This doesn't touch the render itself.)" % self.title.cget("text")):
                    mon.remove_job(k)
            btn(hdr, "✕", remove, fg=SUB).pack(side="right", padx=(6, 0))
            self.open_b = btn(hdr, "Open frames", lambda: webbrowser.open(pod_link(self.j)) if pod_link(self.j) else None)
            self.open_b.pack(side="right")
            self.vid_b = btn(hdr, "Open video", lambda: self.j.saved_path and (os.startfile(self.j.saved_path) if os.name == "nt"
                                                                            else webbrowser.open(self.j.saved_path)), fg="#22c55e")
            self.bar = tk.Canvas(self.f, height=26, bg=CARD, highlightthickness=0)
            self.bar.pack(fill="x", padx=14, pady=(4, 8))
            stats = tk.Frame(self.f, bg=CARD); stats.pack(fill="x", padx=14, pady=(0, 8))
            self.tiles = {}
            for k_, cap in (("done", "FRAMES"), ("left", "TIME LEFT"), ("finish", "FINISH"), ("speed", "SPEED"),
                            ("running", "RUNNING"), ("cost", "COST")):
                t = tk.Frame(stats, bg=CARD); t.pack(side="left", expand=True, fill="x")
                tk.Label(t, text=cap, bg=CARD, fg=DIM, font=F(8, "bold"), anchor="w").pack(fill="x")
                v = tk.Label(t, text="--", bg=CARD, fg=FG, font=F(14, "bold"), anchor="w"); v.pack(fill="x")
                sub = tk.Label(t, text="", bg=CARD, fg=SUB, font=F(8), anchor="w"); sub.pack(fill="x")
                self.tiles[k_] = (v, sub)
            self.gpu = tk.Frame(self.f, bg=CARD); self.gpu.pack(fill="x", padx=14, pady=(0, 12))
            self.gpu_rows = []
            self.note = tk.Label(self.f, text="", bg=CARD, fg="#f59e0b", font=F(9), anchor="w")
            self.deliv = tk.Label(self.f, text="", bg=CARD, fg="#22c55e", font=F(10, "bold"), anchor="w")
            self.j = j

        def draw_bar(self, frac, col):
            c = self.bar; c.delete("all"); w = max(c.winfo_width(), 50); h = 26
            c.create_rectangle(0, 0, w, h, fill=LINE, width=0)
            c.create_rectangle(0, 0, int(w * frac), h, fill=col, width=0)
            c.create_text(w / 2, h / 2, text="%.1f%%" % (frac * 100), fill="white", font=F(10, "bold"))

        def update(self, j):
            self.j = j
            st = j.status; col = COL.get(st, "#6b7280")
            self.title.config(text=j.name)
            self.pill.config(text=LABEL.get(st, st.upper()), bg=col)
            if pod_link(j): self.open_b.pack(side="right")
            else: self.open_b.pack_forget()
            self.draw_bar(j.fraction(), col)
            eta, spf = j.eta_seconds(), j.sec_per_frame()
            T = self.tiles
            T["done"][0].config(text="%s / %s" % (format(j.done, ","), format(j.total, ",") if j.total else "?"))
            T["done"][1].config(text="%s to go" % format(max(j.total - j.done, 0), ",") if j.total else "")
            if st == "done":
                T["left"][0].config(text="finished", fg="#22c55e"); T["left"][1].config(text="")
                T["finish"][0].config(text=datetime.datetime.fromtimestamp(j.finished_at or time.time()).strftime("%H:%M"))
                T["finish"][1].config(text="done at")
            else:
                T["left"][0].config(text=fmt_dur(eta), fg=FG)
                T["left"][1].config(text="updates live from the pod" if j.pod else "from recent speed")
                T["finish"][0].config(text="~" + fmt_clock(eta)); T["finish"][1].config(text="estimated")
            if spf:
                T["speed"][0].config(text="%.2f fps" % (1 / spf)); T["speed"][1].config(text="%.2f s per frame" % spf)
            else:
                T["speed"][0].config(text="measuring"); T["speed"][1].config(text="")
            T["running"][0].config(text=fmt_dur(job_elapsed(j))); T["running"][1].config(text="since pod start" if j.spec.get("pod_started") else "")
            c = job_cost(j)
            if c:
                T["cost"][0].config(text=money(c[0]).split(" ")[0]); T["cost"][1].config(
                    text=("est. total %s" % money(c[1])) if st != "done" else money(c[0]))
            else:
                T["cost"][0].config(text="free" if j.kind == "local" else "--"); T["cost"][1].config(text="")
            # per-GPU lanes (from the pod's progress file)
            lanes = (j.pod or {}).get("per_gpu") or []
            shared = bool((j.pod or {}).get("shared_queue"))      # all GPUs pull from one frame queue (no slowest lane)
            slowest = None
            etas = [g.get("eta_s") for g in lanes]
            if not shared and lanes and all(e is not None for e in etas) and len(lanes) > 1:
                slowest = etas.index(max(etas))
            while len(self.gpu_rows) < len(lanes):
                r = tk.Frame(self.gpu, bg=CARD); r.pack(fill="x", pady=1)
                lab = tk.Label(r, text="", bg=CARD, fg=SUB, font=F(9), width=7, anchor="w"); lab.pack(side="left")
                cv = tk.Canvas(r, height=8, bg=CARD, highlightthickness=0); cv.pack(side="left", fill="x", expand=True, padx=6)
                txt = tk.Label(r, text="", bg=CARD, fg=SUB, font=F(9), width=34, anchor="w"); txt.pack(side="left")
                self.gpu_rows.append((r, lab, cv, txt))
            for i, (r, lab, cv, txt) in enumerate(self.gpu_rows):
                if i >= len(lanes):
                    r.pack_forget(); continue
                g = lanes[i]
                share = (j.total / len(lanes)) if j.total else 0     # shared queue: bar = this GPU's frames vs an even share
                fr = g["done"] / g["total"] if g.get("total") else (min(g["done"] / share, 1.0) if share else 0)
                gc = "#22c55e" if j.status == "done" else ("#f59e0b" if i == slowest else col)
                lab.config(text="GPU %d" % g["gpu"])
                cv.delete("all"); w = max(cv.winfo_width(), 40)
                cv.create_rectangle(0, 0, w, 8, fill=LINE, width=0); cv.create_rectangle(0, 0, int(w * fr), 8, fill=gc, width=0)
                parts = ["%d/%d" % (g["done"], g["total"]) if g.get("total") else "%d frames" % g["done"]]
                if g.get("fps"): parts[-1] += " (%.1f s each)" % (1 / g["fps"])
                if not shared and fr < 1 and g.get("eta_s") is not None: parts.append(fmt_dur(g["eta_s"]))
                if i == slowest and fr < 1: parts.append("slowest")
                txt.config(text="  ·  ".join(parts), fg="#f59e0b" if i == slowest and fr < 1 else SUB)
            STAGE = {"checking": "Checking every frame on the pod...", "assembling": "Putting the video together on the pod...",
                     "ready": "Video ready on the pod, starting download...", "needs_claude": "Pod stopped at a problem: tell Claude",
                     "stopped_no_download": "Not downloaded in 60 min: pod STOPPED (disk kept). Tell Claude."}
            dtext = ""
            if j.delivery == "downloading":
                mb = (j.out.get("size") or 0) / 1e6
                dtext = "Downloading video... %.1f / %.1f MB" % (j.dl_bytes / 1e6, mb) if mb else "Downloading video..."
            elif j.delivery == "saved":
                dtext = "Saved to %s  ·  pod is deleting itself (no more cost)" % j.saved_path
            elif j.delivery == "failed":
                dtext = "Download failed 3 times: use Open frames, or tell Claude"
            elif j.out.get("stage") in STAGE:
                dtext = STAGE[j.out["stage"]]
            if dtext:
                self.deliv.config(text=dtext, fg="#ef4444" if j.delivery == "failed" or "Claude" in dtext else "#22c55e")
                self.deliv.pack(fill="x", padx=14, pady=(0, 10))
            else:
                self.deliv.pack_forget()
            if j.saved_path: self.vid_b.pack(side="right", padx=4)
            else: self.vid_b.pack_forget()
            if j.error:
                self.note.config(text=j.error); self.note.pack(fill="x", padx=14, pady=(0, 10))
            else:
                self.note.pack_forget()

    def poller():
        last_refresh = 0
        while True:
            try:
                if time.time() - last_refresh > 10:          # re-scan watch folders / settings every 10 s, not every tick
                    mon.refresh_jobs(); last_refresh = time.time()
                mon.poll_all()                               # each job throttles itself (2 s local, 5 s pod)
            except Exception as e:
                print("poll error:", e)
            time.sleep(1)

    threading.Thread(target=poller, daemon=True).start()

    def alert(j):
        try:
            root.bell()
            if os.name == "nt":
                import winsound; winsound.MessageBeep()
            root.deiconify(); root.lift(); root.attributes("-topmost", True); root.after(1500, lambda: root.attributes("-topmost", False))
        except Exception:
            pass

    def tick():
        clock.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
        with mon.lock:
            jobs = sorted(mon.jobs.values(), key=lambda j: (j.status == "done", j.group, j.name))
        seen = []
        for j in jobs:
            key = j.key
            card = cards.get(key) or Card(key, j)
            cards[key] = card
            card.update(j)
            seen.append(key)
            if j.delivery == "saved" and not getattr(j, "alerted_saved", False):
                j.alerted_saved = True; alert(j)
            if j.status == "done" and not j.alerted:
                j.alerted = True
                if time.time() - j.first_seen > 10:
                    alert(j)
        for k in list(cards):
            if k not in seen:
                cards.pop(k).f.destroy()
        for k in seen:
            cards[k].f.pack_forget()
        for k in seen:
            cards[k].f.pack(fill="x", pady=6, padx=(0, 12))
        live = [j for j in jobs if j.status != "done"]
        if live:
            j = live[0]; eta = j.eta_seconds()
            root.title("%s · %.0f%% · %s left · finish ~%s" % (j.name, j.fraction() * 100, fmt_dur(eta), fmt_clock(eta)))
        elif jobs:
            root.title("✔ %s done - Bloxbury Render Monitor" % jobs[0].name)
        else:
            root.title("Bloxbury Render Monitor")
        if not jobs and "empty" not in cards:
            f = tk.Label(body, text="No renders yet. Claude sends a pod id + token when a render starts:\n"
                                    "click '+ RunPod pod' and paste them, or watch a laptop folder.",
                         bg=BG, fg=SUB, font=F(10), justify="left")
            f.pack(anchor="w", pady=20)
            class _E: pass
            e = _E(); e.f = f; cards["empty"] = e
        elif jobs and "empty" in cards:
            cards.pop("empty").f.destroy()
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
