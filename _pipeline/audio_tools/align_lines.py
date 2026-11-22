import subprocess, json, re, sys
from pocketsphinx import Decoder
NUM={"3":"three","2:57":"two fifty seven","2":"two"}
def norm(t):
    t=t.replace("2:57","two fifty seven").replace("3 AM","three a m").replace("PART 2","part two")
    return re.sub(r"[^a-z' ]"," ",t.lower()).split()
def load(f):
    raw=subprocess.run(["ffmpeg","-loglevel","error","-i",f,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
    return raw
def align(raw,a,b,text):
    pad=0.15; s=max(0,a-pad); e=b+pad
    seg=raw[int(s*16000)*2:int(e*16000)*2]
    d=Decoder(samprate=16000,bestpath=False)
    words=norm(text)
    d.add_word("bloxbury","B L AA K S B ER IY",True)
    try:
        d.set_align_text(" ".join(words)); d.start_utt(); d.process_raw(seg,full_utt=True); d.end_utt()
        segs=d.seg()
        out=[(re.sub(r"\(\d\)","",x.word),round(s+x.start_frame/100,3),round(s+(x.end_frame+1)/100,3)) for x in segs if x.word not in("<s>","</s>","<sil>")]
        if out: return out
    except Exception as ex: pass
    # fallback: spread evenly by character count
    tot=sum(len(w) for w in words); t=a; out=[]
    for w in words:
        dt=(b-a)*len(w)/tot; out.append((w,round(t,3),round(t+dt,3))); t+=dt
    print("FALLBACK",text,file=sys.stderr); return out
lines=[l for l in open(sys.argv[1]).read().splitlines()]
