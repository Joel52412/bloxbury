# prep2.py - audio + envelope for test 2 (Milo outro 6.75 s, then coffee scene 8 s) at 24 fps
import numpy as np, subprocess, json, wave

FPS = 24
SR = 48000
A_LEN = 6.75          # Milo shot
B_LEN = 8.0           # coffee shot
LEAD = 0.25           # outro starts 0.25 s into the clip
TOT = A_LEN + B_LEN
N = int(round(TOT * FPS))

raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "/home/claude/audio/outro.mp3", "-ac", "1", "-ar", str(SR),
                      "-f", "s16le", "-"], capture_output=True).stdout
vox = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
mix = np.zeros(int(TOT * SR) + SR, np.float32)
o = int(LEAD * SR); mix[o:o + len(vox)] += vox

# ---- envelope for lip-sync (frame-based)
rms, cen = [], []
for f in range(N):
    a = int(f / FPS * SR); b = int((f + 1) / FPS * SR)
    seg = mix[a:b]
    rms.append(float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0)
    if len(seg) and rms[-1] > 1e-4:
        sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        fr = np.fft.rfftfreq(len(seg), 1 / SR)
        cen.append(float((sp * fr).sum() / (sp.sum() + 1e-9)))
    else:
        cen.append(0.0)

# ---- foley for the coffee shot (synthesised, quiet) -------------------------
rng = np.random.default_rng(3)
B0 = A_LEN


def add(sig, t):
    i = int((B0 + t) * SR); mix[i:i + len(sig)] += sig[:max(0, len(mix) - i)]


def noise(d): return rng.standard_normal(int(d * SR)).astype(np.float32)


def env(n, a, r):
    t = np.arange(n) / SR; e = np.minimum(t / max(a, 1e-4), 1) * np.exp(-np.maximum(t - a, 0) / r); return e.astype(np.float32)


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same").astype(np.float32)


def step(t, vol=0.18):
    n = noise(0.12); s = lowpass(n, 60) * env(len(n), 0.004, 0.03)
    thump = np.sin(2 * np.pi * 85 * np.arange(len(n)) / SR) * env(len(n), 0.003, 0.04)
    add((s * 3 + thump) * vol, t)


def rustle(t, d, vol=0.06):
    n = noise(d); k = (np.abs(np.sin(np.linspace(0, d * 37, len(n)))) ** 4)
    add((n - lowpass(n, 6)) * k * env(len(n), 0.02, d * 0.6) * vol, t)


def whoosh(t, d=0.3, vol=0.12):
    n = noise(d); w = lowpass(n, 25) * np.sin(np.linspace(0, np.pi, len(n))) ** 2
    add(w * vol * 4, t)


def slurp(t, d=0.45, vol=0.05):
    n = noise(d); m = 0.5 + 0.5 * np.sin(np.linspace(0, d * 60, len(n)))
    add(lowpass(n, 12) * m * env(len(n), 0.05, 0.25) * vol * 3, t)


def thunk(t, vol=0.25):
    n = int(0.25 * SR); tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 140 * tt) + 0.5 * np.sin(2 * np.pi * 230 * tt)) * np.exp(-tt / 0.06)
    add((s + lowpass(noise(0.25), 8) * np.exp(-tt / 0.03)) * vol, t)


import os
TIM = json.load(open("/home/claude/talk/timing2.json")) if os.path.exists("/home/claude/talk/timing2.json") else None
for t in (TIM or {}).get("steps", []): step(t)
if TIM: slurp(TIM["sip"][0], TIM["sip"][1] - TIM["sip"][0])
if TIM: slurp(TIM["sip2"], 0.3, 0.035)
if TIM: rustle(TIM["grab"], 0.25, 0.08); rustle(TIM["grab"] + 0.3, 0.35, 0.05); rustle(TIM["read_shake"], 0.3, 0.05)
if TIM: whoosh(TIM["throw"] - 0.05, 0.32, 0.12)
if TIM: thunk(TIM["bin"], 0.22)
# soft room tone so the second shot isn't dead silent
mix[int(B0 * SR):] += lowpass(noise(len(mix) / SR - B0)[:len(mix) - int(B0 * SR)], 40) * 0.004

mix = mix[:int(TOT * SR)]
mix /= max(1.0, np.abs(mix).max() / 0.95)
w = wave.open("/home/claude/talk/test2_audio.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes()); w.close()
json.dump({"rms": rms, "cen": cen, "fps": FPS, "lead": LEAD, "a_len": A_LEN, "b_len": B_LEN},
          open("/home/claude/talk/env2.json", "w"))
print("frames", N, "dur", TOT)
