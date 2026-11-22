"""Builds part1_audio.wav from the cue sheet. If music.mp3 exists it is laid under
everything and ducked automatically whenever someone speaks."""
import subprocess, sys, os, json
sys.path.insert(0, '.')
from cues import VOICE, SFX, SFX_FILES, TOTAL
MUSIC = 'music_loop.wav' if os.path.exists('music_loop.wav') else None
MUSIC_VOL = 0.26
MUSIC_OFFSET = 0.0     # looped intro of "Numbers" (built by the loop step)
# music level over the video (time, gain): out for "it went quiet", back for the creep, dead on the cut to black
MUSIC_ENV = [(0, 0.75), (2.3, 1.0), (63.3, 1.0), (63.9, 0.0), (69.8, 0.0), (71.8, 0.6), (73.4, 0.6), (73.9, 0.22), (78.45, 0.22), (78.5, 0.0),
             (80.55, 0.0), (80.7, 0.8), (84.4, 0.8), (84.7, 0.25), (85.95, 0.25), (86.0, 0.0), (88.1, 0.0)]


def env_expr(pts):
    parts = []
    for (t0, g0), (t1, g1) in zip(pts, pts[1:]):
        parts.append(f"between(t,{t0},{t1})*({g0}+({g1}-{g0})*(t-{t0})/({t1}-{t0}+0.0001))")
    return '(' + '+'.join(parts) + ')'
inputs, chains, sfx_labels, voice_labels = [], [], [], []
count = [0]
def add_input(path, loop=False):
    if loop: inputs.extend(['-stream_loop', '-1'])
    inputs.extend(['-i', path]); count[0] += 1; return count[0] - 1
idx = {'milo': add_input('milo.mp3'), 'rae': add_input('rae.mp3'), 'closet': add_input('closet.mp3'), 'outro': add_input('outro.mp3')}
sfx_idx = {k: add_input(f, loop=(k == 'drone')) for k, f in SFX_FILES.items()}
mus_idx = add_input(MUSIC, loop=True) if MUSIC else None
n = 0
for f, a, b, dest, text, style, fx in VOICE:
    if f is None: continue
    gain = 0.95 if f == 'rae' else 1.0
    if 'whisper' in text or fx == 'echo' or text.startswith('Never'):
        gain *= 1.8
    if text.startswith(('went off', 'Except')):
        gain *= 1.3
    extra = ',aecho=0.8:0.7:180|360:0.45|0.3,apad=pad_dur=1.2' if fx == 'echo' else ''
    d = int(dest * 1000)
    chains.append(f"[{idx[f]}:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,"
                  f"afade=t=out:st={max(b-a-0.05,0):.3f}:d=0.05,volume={gain}{extra},adelay={d}|{d}[v{n}]")
    voice_labels.append(f"[v{n}]"); n += 1
for key, dest, ln, vol, fi, fo, flt in SFX:
    i = sfx_idx[key]; d = int(dest * 1000)
    c = f"[{i}:a]atrim=0:{ln},asetpts=PTS-STARTPTS"
    if flt == 'muffled': c += ",lowpass=f=900,volume=1.6"
    if fi: c += f",afade=t=in:d={fi}"
    if fo: c += f",afade=t=out:st={max(ln-fo,0):.3f}:d={fo}"
    c += f",volume={vol},adelay={d}|{d}[s{n}]"
    chains.append(c); sfx_labels.append(f"[s{n}]"); n += 1
# voice bus (also used as the ducking key)
chains.append(''.join(voice_labels) + f"amix=inputs={len(voice_labels)}:normalize=0,apad=whole_dur={TOTAL},asplit=2[vox][key]")
chains.append(''.join(sfx_labels) + f"amix=inputs={len(sfx_labels)}:normalize=0,apad=whole_dur={TOTAL}[fx]")
if MUSIC:
    chains.append(f"[{mus_idx}:a]atrim={MUSIC_OFFSET}:{MUSIC_OFFSET+TOTAL},asetpts=PTS-STARTPTS,"
                  f"volume='{MUSIC_VOL}*{env_expr(MUSIC_ENV)}':eval=frame[mraw]")
    chains.append("[mraw][key]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500[mus]")
    chains.append("[vox][fx][mus]amix=inputs=3:normalize=0,atrim=0:%s[pre]" % TOTAL)
else:
    chains.append("[key]anullsink")
    chains.append("[vox][fx]amix=inputs=2:normalize=0,atrim=0:%s[pre]" % TOTAL)
fc = ';'.join(chains)
base = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex']
# pass 1: measure loudness
r = subprocess.run(['ffmpeg', '-v', 'info', '-y'] + inputs + ['-filter_complex'] + [fc + ';[pre]acompressor=threshold=0.1:ratio=3:attack=5:release=120,alimiter=limit=0.5[pc];[pc]loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json[out]', '-map', '[out]', '-f', 'null', '-'],
                   capture_output=True, text=True)
j = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
ln = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
      "measured_thresh={input_thresh}:offset={target_offset}:linear=true").format(**j)
# pass 2: render
r = subprocess.run(base + [fc + f';[pre]acompressor=threshold=0.1:ratio=3:attack=5:release=120,alimiter=limit=0.5[pc];[pc]{ln}[out]', '-map', '[out]', '-ar', '48000', '-ac', '2', 'part1_audio.wav'],
                   capture_output=True, text=True)
print(r.stderr[-1500:] or ('ok (music: %s)' % (MUSIC or 'none yet')))
