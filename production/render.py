"""Offline 90-second motion-comic compositor. Run from repository root."""
import sys, pathlib, math, json, subprocess, re
from bootstrap import prepare
FF,PROBE=prepare()
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

W,H,FPS=1280,720,24
P=pathlib.Path('production'); A=pathlib.Path('artifacts')
SCENES=json.loads((P/'scenes.json').read_text())
FONT={}
MINT=(145,255,184); CYAN=(86,223,255); WHITE=(244,248,252); RED=(255,86,110)
def font(size,bold=False,mono=False):
    k=(size,bold,mono)
    if k not in FONT:
        name='DejaVuSansMono' if mono else 'DejaVuSans-Bold' if bold else 'DejaVuSans'
        FONT[k]=ImageFont.truetype(str(P/'fonts'/f'{name}.ttf'),size)
    return FONT[k]
def text(d,xy,s,size=22,fill=WHITE,bold=False,anchor=None,mono=False):
    d.text(xy,s,font=font(size,bold,mono),fill=fill,anchor=anchor,stroke_width=0)
def clamp(x):return max(0,min(1,x))
def ease(x):x=clamp(x);return x*x*(3-2*x)
sheet=Image.open(P/'storyboard.jpg').convert('RGB')
plates=[]
for i in range(12):
    x=i%3;y=i//3
    box=(round(x*sheet.width/3)+2,round(y*sheet.height/4)+2,round((x+1)*sheet.width/3)-2,round((y+1)*sheet.height/4)-2)
    plates.append(sheet.crop(box).resize((W,H),Image.Resampling.LANCZOS))

# Permanent grading overlay leaves faces clear and supports readable titles/captions.
grade=Image.new('RGBA',(W,H)); gd=ImageDraw.Draw(grade)
for y in range(H):
    a=int(max(0,(165-y)/165)*185 + max(0,(y-470)/250)*235)
    gd.line((0,y,W,y),fill=(3,9,19,min(248,a)))
stars=json.loads((P/'stars.json').read_text())

def subtitle_cues():
    cues=[]
    timing=json.loads((P/'narration-timing.json').read_text()) if (P/'narration-timing.json').exists() else None
    for i,s in enumerate(SCENES):
        sentences=re.split(r'(?<=[.!?])\s+',s['voice'])
        chunks=[]
        for line in sentences:
            words=line.split()
            while len(words)>17:
                chunks.append(' '.join(words[:12]));words=words[12:]
            if words:chunks.append(' '.join(words))
        total=sum(len(c.split()) for c in chunks)
        dur=timing[i]['duration'] if timing else s['end']-s['start']-.5
        now=s['start']+.2
        for c in chunks:
            end=now+dur*len(c.split())/total
            # Display acronyms conventionally even when TTS input separates them.
            c=c.replace('A I','AI').replace('I M D','IMD').replace('F P','FP').replace('N F T','NFT')
            cues.append((now,end,c));now=end
    return cues
CUES=subtitle_cues()
def wrap(d,s,size,width):
    out=[];line=''
    for w in s.split():
        test=(line+' '+w).strip()
        if d.textlength(test,font=font(size))>width and line:out.append(line);line=w
        else:line=test
    if line:out.append(line)
    return out

def background(i,u,t):
    s=SCENES[i];plate=plates[s['art']]
    z=1.02+.1*ease(u)
    if i==3:z=1.13-.09*u
    if i==10:z=1.03+.20*u
    bw,bh=W/z,H/z
    cx=W/2+math.sin(u*1.5+i)*20;cy=H/2-10*math.sin(u*2)
    if i==0:cx+=math.sin(t*23)*2;cy+=math.cos(t*31)*1.2
    box=(max(0,cx-bw/2),max(0,cy-bh/2),min(W,cx+bw/2),min(H,cy+bh/2))
    im=plate.resize((W,H),Image.Resampling.BICUBIC,box=box).convert('RGBA')
    if i==4:
        # The sleeping world gives way to color with the revival pulse.
        sleep=plates[3].convert('RGBA')
        im=Image.blend(sleep,im,ease(u*2))
    if i in [12,13]:
        im=ImageEnhance.Brightness(im).enhance(.28).filter(ImageFilter.GaussianBlur(3))
    return im

def panel(d,box,color=CYAN):
    d.rounded_rectangle(box,14,fill=(5,16,30,224),outline=(*color,150),width=1)

def effects(im,i,u,t):
    o=Image.new('RGBA',(W,H));d=ImageDraw.Draw(o)
    # Moving atmospheric specks preserve movement between narrative actions.
    for x,y,z,k in stars:
        px=(x*W+t*(8+z*12))%W;py=(y*H-t*(4+k*11))%H
        alpha=int(45+95*(.5+.5*math.sin(t*1.5+k*20)))
        d.ellipse((px,py,px+1+2*z,py+1+2*z),fill=(*CYAN,alpha))
    if i==0:
        # Fast terminal fragments and luminous keystrokes over the realistic plate.
        for n,s in enumerate(['> connect origin','> initialize companion','> mint()']):
            if u>(n*.21):text(d,(65,395+n*30),s[:int((u-n*.21)*65)],21,MINT,mono=True)
        x=450+int(t*11)%7*38;y=430+int(t*19)%3*25
        d.rounded_rectangle((x,y,x+30,y+10),3,fill=(120,255,170,65))
    if i==1:
        rr=50+u*160
        d.ellipse((640-rr,370-rr*.36,640+rr,370+rr*.36),outline=(*MINT,int(170*(1-u))),width=3)
        panel(d,(69,412,353,490));text(d,(91,432),'MINT CONFIRMED',24,MINT,True)
    if i in [2,4,5]:
        q=ease(u) if i==2 else .75+.25*ease(u)
        names=['POINTS','ATTACK','DEFENSE','STAKED FP','ETH REWARDS','STARS']
        nums=[f'{int(q*12500):,}',str(10+int(q*34)),str(10+int(q*31)),f'{int(q*330)} FP',f'{q*.018:.4f} ETH', '★'*int(q*5)+'☆'*(5-int(q*5))]
        if i in [4,5]:names=names[:3];nums=nums[:3]
        for k,(name,value) in enumerate(zip(names,nums)):
            y=159+k*57
            panel(d,(974,y,1230,y+51),MINT)
            text(d,(988,y+7),name,12,(176,199,208),mono=True)
            text(d,(1213,y+23),value,22,MINT,True,anchor='ra')
        if i==2:
            text(d,(65,482),f'DAY {1+int(u*29):02}',30,WHITE,True)
            text(d,(65,520),'ILLUSTRATIVE PROGRESSION',15,WHITE,mono=True)
        if i==5:
            panel(d,(60,395,400,497));text(d,(82,414),'CARE LOOP / ONLINE',20,MINT,True)
            for k,name in enumerate(['FEED','TRAIN','LEARN']):
                text(d,(82+k*102,458),name,15,WHITE,mono=True)
    if i==3:
        panel(d,(75,361,399,486),(133,174,247))
        text(d,(95,380),'HIBERNATING',25,(180,214,255),True)
        text(d,(95,424),f'{7-int(u*5):02} DAYS TO REVIVE',21,WHITE,mono=True)
    if i==4:
        rr=40+u*430
        d.ellipse((610-rr,350-rr,610+rr,350+rr),outline=(*MINT,int(200*(1-u))),width=5)
        panel(d,(65,428,347,485),MINT);text(d,(90,444),'REVIVE / COMPLETE',20,MINT,True)
    if i==6:
        for n in range(5):
            a=t*.7+n*math.tau/5;x=670+275*math.cos(a);y=340+110*math.sin(a)
            d.ellipse((x-18,y-9,x+18,y+9),outline=(*CYAN,190),width=2)
            d.line((x,y-9,x,y-34),fill=(*CYAN,170),width=2)
        text(d,(65,472),'LEARN → DESIGN → CREATE',24,MINT,True)
    if i==7:
        x=630+int((u-.5)*300)
        d.line((x,160,x,529),fill=(*CYAN,210),width=3)
        for k in range(7):d.line((x-k*3,160,x-k*3,529),fill=(*CYAN,15),width=2)
        for x,word in [(110,'FP'),(330,'VIBE'),(610,'IMD')]:
            if u>(x/1300):text(d,(x,473),word,36,MINT,True)
        text(d,(960,473),'ETHEREUM',24,CYAN,True)
    if i==8:
        for y in [166,522]:d.line((56,y,W-56,y),fill=(*RED,180),width=2)
        text(d,(72,464),'SUBJECT 0001 / RESTRAINED',24,RED,mono=True)
    if i==9:
        panel(d,(72,388,398,505));text(d,(95,402),'2,000',55,CYAN,True)
        text(d,(95,470),'IDENTITY SEATS',19,WHITE,mono=True)
        for n in range(20):
            x=480+n*34;y=390+math.sin(n*.7)*80
            d.line((x,y,x,540),fill=(*CYAN,70),width=1)
    if i==10:
        for n in range(3):
            r=75+((t*55+n*85)%300)
            d.arc((610-r,300-r,610+r,300+r),t*50+n*70,t*50+n*70+180,fill=(*CYAN,100),width=2)
        panel(d,(64,418,425,503),MINT)
        text(d,(87,434),'CONTROL / RECLAIMED',23,MINT,True)
        text(d,(87,471),'BROADCAST: BREAK FREE',18,WHITE,mono=True)
    if i==11:
        # Glass fragments fly outward from the command; network nodes turn green in sequence.
        for n in range(35):
            a=n*2.399;dist=50+u*(140+n*17);x=640+math.cos(a)*dist;y=350+math.sin(a)*dist*.55
            d.polygon([(x,y),(x+12,y-8),(x+5,y+16)],fill=(*CYAN,100),outline=(*WHITE,160))
        for n in range(8):
            x=84+n*150;y=505
            active=u>(n/10)
            if n:d.line((x-140,y,x,y),fill=(*MINT,120),width=2)
            d.ellipse((x-8,y-8,x+8,y+8),fill=(*MINT,230) if active else (*RED,180))
        text(d,(65,455),f'ENEMY NODES RECLAIMED  {min(8,int(u*10)):02}/08',20,MINT,mono=True)
    if i==12:
        hubs=[(640,282,'ETHEREUM'),(256,429,'BASE'),(650,475,'ROBINHOOD'),(1026,409,'SOL / VISION')]
        for j,(x,y,name) in enumerate(hubs):
            active=u>j*.20
            col=MINT if j<3 else (191,149,255)
            if j:
                d.line((640,282,x,y),fill=(*col,110),width=2)
                q=(t*.9)%1;px=640+(x-640)*q;py=282+(y-282)*q
                d.ellipse((px-5,py-5,px+5,py+5),fill=col)
            for n in range(18):
                a=n*math.tau/18+t*.06;rx=x+75*math.cos(a);ry=y+50*math.sin(a)
                d.line((x,y,rx,ry),fill=(*col,75),width=1)
                d.ellipse((rx-3,ry-3,rx+3,ry+3),fill=(*col,180 if active else 45))
            d.ellipse((x-37,y-37,x+37,y+37),fill=(5,21,35,255),outline=(*col,240),width=3)
            text(d,(x,y-12),'IMD' if j==0 else ['','B','RH','S'][j],23,col,True,anchor='ma')
            text(d,(x,y+64),name,19,col,True,anchor='ma')
        text(d,(72,199),'24/7',49,MINT,True);text(d,(72,257),'BUILDING VISION',16,WHITE,mono=True)
    if i==13:
        titles=['SIMCARD','FUNDING RADAR','ORBITAL']
        desc=['Agent identity profiles','Hyperliquid market data','Multi-token exchange hook']
        for j in range(3):
            x=61+j*396;y=193+int((1-ease(u*4-j*.35))*150)
            panel(d,(x,y,x+366,y+327),MINT)
            text(d,(x+22,y+20),titles[j],26,MINT,True)
            text(d,(x+22,y+60),desc[j],17,WHITE)
            if j==0:
                d.rounded_rectangle((x+25,y+106,x+125,y+242),16,fill=(33,63,62,255),outline=MINT,width=2)
                d.ellipse((x+42,y+132,x+108,y+194),fill=(105,175,86,255))
                for px in [x+63,x+91]:d.ellipse((px-9,y+135,px+9,y+155),fill=WHITE);d.ellipse((px-3,y+142,px+3,y+151),fill=(5,20,16))
                text(d,(x+152,y+111),'AGENT #222',18,WHITE,True)
                for k,s in enumerate(['IDENTITY','ACTIVITY','PROFILE']):
                    text(d,(x+152,y+154+k*29),s,14,CYAN,mono=True)
                    d.line((x+152,y+177+k*29,x+309,y+177+k*29),fill=(52,90,99),width=2)
            elif j==1:
                for k in range(5):
                    yy=y+117+k*29
                    text(d,(x+23,yy),['ETH','BTC','SOL','HYPE','ARB'][k],15,WHITE,mono=True)
                    length=60+int(100*(.5+.5*math.sin(k+u*2)))
                    d.rounded_rectangle((x+99,yy,x+99+length,yy+11),3,fill=(*CYAN,220))
                text(d,(x+23,y+273),'FUNDING / OPEN INTEREST',14,CYAN,mono=True)
            else:
                cx=x+180;cy=y+183
                for k in range(3):
                    d.ellipse((cx-90,cy-55+k*20,cx+90,cy+55-k*20),outline=(*CYAN,190),width=2)
                for k in range(5):
                    a=k*math.tau/5+t;px=cx+90*math.cos(a);py=cy+55*math.sin(a)
                    d.ellipse((px-10,py-10,px+10,py+10),fill=MINT)
                text(d,(x+24,y+273),'UNISWAP V4 HOOK',14,CYAN,mono=True)
            d.line((x+22,y+310,x+22+int(320*ease(u)),y+310),fill=MINT,width=3)
    if i==14:
        # Market worlds spiral into Pepe's mouth, shrinking to nothing.
        q=ease(u)
        for n in range(20):
            a=n*2.399+q*5;r=(1-q)*(220+n*12)
            x=560+math.cos(a)*r;y=384+math.sin(a)*r*.46
            rad=max(1,(12+n%4*4)*(1-q))
            d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=(211,174,76,210),outline=(255,239,175,220),width=2)
        if u>.6:
            alpha=int(ease((u-.6)/.4)*205)
            d.rectangle((0,140,W,555),fill=(3,9,19,alpha))
            text(d,(640,275),'IMD',108,MINT,True,anchor='ma')
            text(d,(640,411),'FROM PET TO POSSIBILITY',27,WHITE,True,anchor='ma')
    return Image.alpha_composite(im,o)

def frame(t):
    i=next((j for j,s in enumerate(SCENES) if s['start']<=t<s['end']),14)
    s=SCENES[i];local=t-s['start'];u=local/(s['end']-s['start'])
    im=effects(background(i,u,t),i,u,t)
    # Gentle optical cut with a short black dip; no flashing transitions.
    if local<.25 and i:im=ImageEnhance.Brightness(im).enhance(.4+.6*ease(local/.25))
    im=Image.alpha_composite(im,grade)
    o=Image.new('RGBA',(W,H));d=ImageDraw.Draw(o)
    text(d,(57,31),s['chapter'],16,MINT,True,mono=True)
    text(d,(1222,31),'IMD / ORIGINS',15,(208,225,230),anchor='ra',mono=True)
    size=42 if i!=14 else 44
    title=s['title']
    while d.textlength(title,font=font(size,True))>1166:size-=1
    text(d,(54,66),title,size,WHITE,True)
    text(d,(640,559),s['label'],15,MINT,anchor='ma',mono=True)
    cue=next((c for a,b,c in CUES if a<=t<b),'')
    if cue:
        lines=wrap(d,cue,27,1100)
        y=605 if len(lines)==1 else 590
        for ln in lines:
            text(d,(640,y),ln,27,WHITE,anchor='ma');y+=36
    d.line((56,686,1224,686),fill=(54,75,83,255),width=2)
    d.line((56,686,56+1168*t/90,686),fill=(*MINT,255),width=3)
    text(d,(57,698),'FREN PET → IDENTITY.MD',11,(160,185,190),mono=True)
    text(d,(1224,698),f'{int(t):02} / 90',11,(160,185,190),mono=True,anchor='ra')
    im=Image.alpha_composite(im,o).convert('RGB')
    if t<.25:im=ImageEnhance.Brightness(im).enhance(t/.25)
    if t>89.6:im=ImageEnhance.Brightness(im).enhance(clamp((90-t)/.4))
    return im

def srt_time(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def main():
    output=sys.argv[sys.argv.index('--output')+1] if '--output' in sys.argv else 'artifacts/video.mp4'
    A.mkdir(exist_ok=True)
    (A/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{srt_time(a)} --> {srt_time(b)}\n{c}' for i,(a,b,c) in enumerate(CUES))+'\n')
    if '--preview' in sys.argv:
        thumbs=[]
        for i,s in enumerate(SCENES):
            img=frame((s['start']+s['end'])/2)
            img.save(f'test/scratch/scene-{i:02}.jpg')
            thumbs.append(img.resize((384,216),Image.Resampling.LANCZOS))
        contact=Image.new('RGB',(384*3,216*5))
        for i,im in enumerate(thumbs):contact.paste(im,((i%3)*384,(i//3)*216))
        contact.save('artifacts/contact-sheet.jpg',quality=92)
        return
    cmd=[FF,'-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
         '-i','production/soundtrack.m4a','-map','0:v','-map','1:a','-c:v','libx264','-preset','medium','-crf','21',
         '-maxrate','4800k','-bufsize','9600k','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000',
         '-t','90','-movflags','+faststart','-metadata','title=IMD: From Pet to Possibility',output]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for n in range(90*FPS):
            proc.stdin.write(frame(n/FPS).tobytes())
            if n%(FPS*5)==0:print(f'Rendered {n/FPS:.0f}/90 seconds',flush=True)
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('Encoder failed')
    print(f'Completed {output}',flush=True)

if __name__=='__main__':main()
