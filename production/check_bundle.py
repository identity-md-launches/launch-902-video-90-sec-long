"""Count delivered source and auxiliary assets separately from the named MP4."""
import json,pathlib
root=pathlib.Path('.')
files=[root/'README.md']
files += [p for p in (root/'production').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files += [p for p in (root/'artifacts').rglob('*') if p.is_file() and p.name not in ('video.mp4','bundle-verification.json')]
size=sum(p.stat().st_size for p in files)
report={'status':'passed' if size<8*1024*1024 else 'failed', 'source_and_auxiliary_bytes':size,
        'limit_bytes':8*1024*1024,'excluded':'Named video.mp4, this report, scratch tests, interpreter caches and environment metadata',
        'largest_files':sorted([{'path':str(p),'bytes':p.stat().st_size} for p in files],key=lambda x:x['bytes'],reverse=True)[:8]}
pathlib.Path('artifacts/bundle-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert size+pathlib.Path('artifacts/bundle-verification.json').stat().st_size<8*1024*1024
