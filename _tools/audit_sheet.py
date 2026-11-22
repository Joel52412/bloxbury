import sys,glob,os
from PIL import Image,ImageDraw
src,out,cols=sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 8
fs=sorted(glob.glob(src+'/*.png'),key=os.path.getmtime);W=H=Image.open(fs[0]).size[0]
rows=(len(fs)+cols-1)//cols;im=Image.new('RGB',(W*cols,(H+16)*rows),(15,15,15));d=ImageDraw.Draw(im)
for i,f in enumerate(fs):
  x,y=(i%cols)*W,(i//cols)*(H+16);im.paste(Image.open(f).convert('RGB').resize((W,W)),(x,y+16));d.text((x+3,y+2),os.path.basename(f)[:-4],fill=(255,255,0))
im.save(out,quality=85);print(im.size)
