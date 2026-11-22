import json,subprocess,numpy as np,sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from align_full import norm
import os
A=os.environ.get("AUD","/home/claude/bloxbury/series/bloxbury/part2/voice/")
def env(f):
    x=np.frombuffer(subprocess.run(["ffmpeg","-loglevel","error","-i",A+f,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout,np.int16)/32768
    k=160; n=len(x)//k; return 20*np.log10(np.sqrt((x[:n*k].reshape(n,k)**2).mean(1))+1e-9)
def split(fname,words,lines):
    e=env(fname); out=[]; i=0
    for L in lines:
        n=len(norm(L)); ws=words[i:i+n]; i+=n
        assert [w[0] for w in ws]==norm(L),(L,ws)
        out.append({"text":L,"a":ws[0][1],"b":ws[-1][2],"words":ws})
    raw=[(o["a"],o["b"]) for o in out]
    for k in range(len(out)):
        a,b=raw[k]
        lo=max(raw[k-1][1]-0.05 if k else 0.0, a-0.4); hi=a+0.08
        f0=int(lo*100); f1=max(f0+1,int(hi*100)); out[k]["a"]=round((f0+int(np.argmin(e[f0:f1])))/100,2)
        hi2=min(raw[k+1][0]+0.05 if k+1<len(out) else len(e)/100, b+0.5); lo2=b-0.08
        f0=int(lo2*100); f1=max(f0+1,int(hi2*100)); out[k]["b"]=round((f0+int(np.argmin(e[f0:f1])))/100+0.01,2)
        out[k]["cut_db"]=(round(float(e[int(out[k]['a']*100)])),round(float(e[min(len(e)-1,int(out[k]['b']*100)-1)])))
    return out
M=["My mum finally came home last night.","I wish she hadn't.","She made my favourite pancakes.","She hummed my favourite song.","She hugged me for a really, really long time.","And she called me Milo.","Mum never calls me Milo.","My mum's back! But it's not... it's not her!","No... she had a key.","So who's in my kitchen?","It looked like Mum.","Then Mum stopped smiling.","Her reflection didn't.","I locked my door.","Then a voice came from inside my closet.","Mum?","Two mums. One door.","Which one would you open?","Comment below... Part Three depends on it."]
R=["Did she knock?","Then it doesn't need to knock anymore.","Milo...","your mum was the first name I crossed off.","Three weeks ago.","Check a mirror.","Mirrors don't lie."]
if __name__=="__main__":
    m=split("milo_p2.mp3",json.load(open("words_milo.json")),M); r=split("rae_p2.mp3",json.load(open("words_rae.json")),R)
    # sphinx put "Milo" (whispered, ~12.9-13.4 s) on the next line's onset; real gap is digital silence 13.45-13.75
    m[6]["b"]=13.60; m[7]["a"]=13.60; m[6]["words"][-1]=("milo",12.95,13.42); m[7]["words"][0]=("my",13.76,13.93)
    json.dump(m,open("lines_milo.json","w")); json.dump(r,open("lines_rae.json","w"))
    for o in m+r: print(f'{o["a"]:6.2f}-{o["b"]:6.2f} {o["cut_db"]} {o["text"]}')
