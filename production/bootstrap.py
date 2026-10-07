"""Expand the bundled Linux x86_64 / Python 3.12 media runtime, offline."""
import hashlib,pathlib,sys,tarfile,shutil

def prepare():
    root=pathlib.Path('test/scratch/runtime-slim')
    archive_path=pathlib.Path('production/runtime.tar.xz')
    digest=hashlib.sha256(archive_path.read_bytes()).hexdigest()
    marker=root/'.complete'
    if not marker.exists() or marker.read_text()!=digest:
        if root.exists():shutil.rmtree(root)
        root.mkdir(parents=True,exist_ok=True)
        with tarfile.open(archive_path,'r:xz') as archive:
            archive.extractall(root,filter='data')
        marker.write_text(digest)
    sys.path.insert(0,str(root.resolve()))
    return str(root/'bin'/'ffmpeg'),str(root/'bin'/'ffprobe')
