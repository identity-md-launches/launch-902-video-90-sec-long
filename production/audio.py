"""Offline procedural score rebuild using bundled narration and Python's standard library.
Random noise differs from the original NumPy-generated master. No voice service required.
"""
import pathlib,json,subprocess,wave,math,random,io
from array import array
from bootstrap import prepare
FF,PROBE=prepare()
ROOT=pathlib.Path('production')
SCENES=json.loads((ROOT/'scenes.json').read_text())
SR=48000

def build():
    rng=random.Random(1804)
    mix=[array("f", [0])* (90*SR), array("f", [0])* (90*SR)]
    def put(start, data, gain=1, pan=0):
        a=int(start*SR)
        for j,v in enumerate(data):
            if a+j >= len(mix[0]): break
            mix[0][a+j]+=v*gain*(1-pan*.5)
            mix[1][a+j]+=v*gain*(1+pan*.5)
    def times(dur): return (n/SR for n in range(int(dur*SR)))
    def tone(freq,dur,amp=.1):
        return (amp*min(1,t/.03)*math.exp(-t/max(.1,dur*.45))*(math.sin(2*math.pi*freq*t)+.3*math.sin(4*math.pi*freq*t)) for t in times(dur))
    # Original minor-key score: spacious pad, restrained pulse, triumphant final build.
    roots=[55,43.6535,65.4064,48.9994]
    for block in range(23):
        start=block*4; dur=min(4.2,90-start)
        root=roots[block%4]
        for ratio,pan in [(1,-.4),(2,.4),(2**(3/12),-.7),(2**(7/12),.7)]:
            pad=((math.sin(2*math.pi*root*ratio*t)+.35*math.sin(2*math.pi*root*ratio*1.003*t))*.014*min(1,t/.5)*min(1,(dur-t)/.65) for t in times(dur))
            put(start,pad,pan=pan)
    for beat in (5+n*.5 for n in range(168)):
        if 20<=beat<25: continue
        intensity=.65 if beat<61 else 1
        kick=(math.sin(2*math.pi*(48*t+2.6*(1-math.exp(-t*25))))*math.exp(-t*23)*.09*intensity for t in times(.22))
        put(beat,kick)
        step=int((beat-5)*2)
        freq=roots[int(beat//4)%4]*4*2**([0,7,10,12,7,3,10,7][step%8]/12)
        put(beat,tone(freq,.38,.021*intensity),pan=math.sin(step)*.7)
        if step%2:
            samples=[rng.gauss(0,1) for _ in range(int(.11*SR))]
            noise=((v-(samples[n-1] if n else 0))*math.exp(-n/SR*55)*.016*intensity for n,v in enumerate(samples))
            put(beat,noise,pan=.4)
    # Mechanical keyboard, UI pings, reviving pulse, glass break, and scene impacts.
    for at in (.1+n*.105 for n in range(42)):
        click=((rng.gauss(0,1)*.4+math.sin(2*math.pi*1900*t))*math.exp(-t*150)*.075 for t in times(.035))
        put(at,click,pan=float(rng.uniform(-.6,.6)))
    for at in [5,11,25,30,36,42,49,55,61,67,73,79,85]:
        hit=(math.sin(2*math.pi*(42*t+1.5*(1-math.exp(-t*15))))*math.exp(-t*5)*.095 for t in times(1))
        put(at,hit)
        if at in [5,25,30,36]: put(at+.15,tone(880,1,.055))
    for at in [67,67.18,67.4]:
        crack=(rng.gauss(0,1)*math.exp(-t*9)*.06 for t in times(.7))
        put(at,crack,pan=float(rng.uniform(-1,1)))
    voice_report=[]
    for i,s in enumerate(SCENES):
        raw=subprocess.check_output([FF,'-v','error','-i',str(ROOT/f'voice/{i:02}.mp3'),'-f','wav','-c:a','pcm_s16le','-ac','1','-ar',str(SR),'-'])
        data=array('h',wave.open(io.BytesIO(raw)).readframes(90*SR))
        # Fit each entire sentence; never truncate narration.
        target=s['end']-s['start']-.5
        speed=max(1,len(data)/SR/target)
        if speed>1:
            raw=subprocess.check_output([FF,'-v','error','-i',str(ROOT/f'voice/{i:02}.mp3'),'-af',f'atempo={speed:.6f}', '-f','wav','-c:a','pcm_s16le','-ac','1','-ar',str(SR),'-'])
            data=array('h',wave.open(io.BytesIO(raw)).readframes(90*SR))
        peak=max(.001,max(abs(v) for v in data))
        put(s['start']+.2,data,.63/peak)
        voice_report.append({'scene':i,'duration':len(data)/SR,'speed':speed})
    pcm=array('h')
    for n,(l,r) in enumerate(zip(*mix)):
        fade=min(1,n/SR/.5)*min(1,(len(mix[0])-n)/SR/.8)
        pcm.extend((int(math.tanh(l*fade*1.1)*.91*32767),int(math.tanh(r*fade*1.1)*.91*32767)))
    with wave.open('test/scratch/mix.wav','wb') as out:
        out.setparams((2,2,SR,0,'NONE','not compressed'));out.writeframes(pcm.tobytes())
    (ROOT/'narration-timing.json').write_text(json.dumps(voice_report,indent=2))
    subprocess.run([FF,'-y','-v','error','-i','test/scratch/mix.wav','-c:a','aac','-b:a','160k','production/soundtrack.m4a'],check=True)
    print('Soundtrack complete',flush=True)

if __name__=='__main__':
    build()
