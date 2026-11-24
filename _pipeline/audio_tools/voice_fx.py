# voice_fx.py - viral TikTok voice sound (Joel 23 Nov): speed up + pitch up each voice file BEFORE alignment,
# so word timings, captions and lip-sync all follow the sped-up audio. ffmpeg rubberband, high-quality pitch.
# Usage: python3 voice_fx.py <voice_dir> <who>:<semitones>[:kid] ... [--tempo 1.1] [--id hm1]
#   reads  <voice_dir>/<who>_<id>.mp3 (Joel's originals, untouched)
#   writes <voice_dir>/fx/<who>_<id>.mp3 (pass voice_dir=<voice_dir>/fx/ to Mix and align on these)
#   kid = shift formants too (adult voice designed for a child character); otherwise formants are kept.
import os, subprocess, sys

def fx(src, dst, tempo=1.1, semis=1.0, kid=False):
    p = 2 ** (semis / 12)
    f = "rubberband=tempo=%.4f:pitch=%.4f:pitchq=quality:formant=%s" % (tempo, p, "shifted" if kid else "preserved")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", f, "-ar", "44100", "-b:a", "192k", dst], check=True)

if __name__ == "__main__":
    a = sys.argv[1:]; tempo = 1.1; pid = None
    if "--tempo" in a: i = a.index("--tempo"); tempo = float(a[i + 1]); del a[i:i + 2]
    if "--id" in a: i = a.index("--id"); pid = a[i + 1]; del a[i:i + 2]
    vd = a[0].rstrip("/") + "/"; os.makedirs(vd + "fx", exist_ok=True)
    for spec in a[1:]:
        who, semis, *k = spec.split(":")
        name = "%s_%s.mp3" % (who, pid) if pid else who
        fx(vd + name, vd + "fx/" + name, tempo, float(semis), bool(k))
        print("fx", name, "tempo", tempo, "semis", semis, "kid" if k else "")
