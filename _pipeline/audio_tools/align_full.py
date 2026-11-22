import subprocess, re, sys, json
from pocketsphinx import Decoder
def norm(t): return re.sub(r"[^a-z' ]"," ",t.lower().replace("…"," ")).split()
def align(path, text):
    raw=subprocess.run(["ffmpeg","-loglevel","error","-i",path,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
    d=Decoder(samprate=16000,bestpath=False)
    d.add_word("bloxbury","B L AA K S B ER IY",True); d.add_word("hummed","HH AH M D",True)
    d.set_align_text(" ".join(norm(text))); d.start_utt(); d.process_raw(raw,full_utt=True); d.end_utt()
    return [(re.sub(r"\(\d\)","",x.word),round(x.start_frame/100,3),round((x.end_frame+1)/100,3)) for x in d.seg() if x.word not in("<s>","</s>","<sil>")]
if __name__=="__main__":
    out=align(sys.argv[1], open(sys.argv[2]).read()); json.dump(out,open(sys.argv[3],"w"))
    print(" ".join(f"{w}@{s}" for w,s,e in out))
