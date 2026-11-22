# make_animatic.py N [out.mp4] - audio animatic for Joel's pacing check: dark frame, timecode, scene labels,
# "music out" markers and the real captions, over OUT_DIR/partN_audio.wav. Send it in chat; don't store it.
import json, subprocess, sys, os
N = sys.argv[1]; T = os.environ.get("OUT_DIR", "/home/claude/talk/"); R = os.path.abspath(os.path.dirname(__file__) + "/..")
out = sys.argv[2] if len(sys.argv) > 2 else f"/home/claude/Bloxbury_Part{N}_animatic.mp4"
e = json.load(open(f"{T}env_p{N}.json")); F = R + "/assets/fonts/Poppins-Bold.ttf"
dt = [f"drawtext=fontfile={F}:text='{s.replace('_', ' ').upper()}':x=(w-tw)/2:y=170:fontsize=44:fontcolor=0xBBBBBB:enable='between(t,{a},{b})'"
      for s, a, b in e["scenes"]]
dt.append(f"drawtext=fontfile={F}:text='%{{pts\\:hms}}':x=(w-tw)/2:y=90:fontsize=52:fontcolor=white")
dt += [f"drawtext=fontfile={F}:text='music out':x=(w-tw)/2:y=250:fontsize=34:fontcolor=0xFF6666:enable='between(t,{a},{b})'" for a, b in e["mutes"]]
vf = ",".join(dt) + f",ass={T}captions_p{N}.ass:fontsdir={R}/assets/fonts"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x101418:s=1080x1920:r=24:d={e['total']}", "-i",
                f"{T}part{N}_audio.wav", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-c:a", "aac", "-b:a", "160k",
                "-shortest", out], check=True)
print("WROTE", out)
