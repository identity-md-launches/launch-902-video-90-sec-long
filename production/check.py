"""Validate the actual encoded deliverable and save machine-readable evidence."""
import json,subprocess,pathlib,struct,hashlib,argparse
from bootstrap import prepare
FF,PROBE=prepare()
parser=argparse.ArgumentParser()
parser.add_argument('--video',default='artifacts/video.mp4')
parser.add_argument('--report',default='artifacts/verification.json')
args=parser.parse_args()
p=pathlib.Path(args.video)
meta=json.loads(subprocess.check_output([PROBE,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
v=next(s for s in meta['streams'] if s['codec_type']=='video')
a=next(s for s in meta['streams'] if s['codec_type']=='audio')
assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p'
assert (v['width'],v['height'])==(1280,720)
assert v['r_frame_rate']=='24/1' and int(v['nb_read_frames'])==2160
assert abs(float(meta['format']['duration'])-90)<.05
assert a['codec_name']=='aac' and a['channels']==2 and a['sample_rate']=='48000'
assert p.stat().st_size<64*1024*1024
atoms=[]
with p.open('rb') as f:
    while True:
        offset=f.tell();h=f.read(8)
        if len(h)<8:break
        size,typ=struct.unpack('>I4s',h)
        if size==1:size=struct.unpack('>Q',f.read(8))[0]
        atoms.append({'type':typ.decode('ascii'),'offset':offset,'size':size})
        if size==0:break
        f.seek(offset+size)
assert next(x['offset'] for x in atoms if x['type']=='moov')<next(x['offset'] for x in atoms if x['type']=='mdat')
decode=subprocess.run([FF,'-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
assert decode.returncode==0 and not decode.stderr,decode.stderr
vol=subprocess.run([FF,'-hide_banner','-i',str(p),'-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True)
report={'status':'passed','duration_seconds':float(meta['format']['duration']),'video':v,'audio':a,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'atoms':atoms,'full_decode':'passed with no reported errors','audio_levels':[l.strip() for l in vol.stderr.splitlines() if 'mean_volume:' in l or 'max_volume:' in l]}
pathlib.Path(args.report).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','duration_seconds','bytes','full_decode','audio_levels']},indent=2))
