"""Read-only verified own-checkpoint chunk loading in RAM."""
import pathlib,json,io,hashlib,torch,sys
BASE=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE))
from core import sha
def read(p):return json.loads(pathlib.Path(p).read_text())

def load_chunks(manifest):
    manifest=pathlib.Path(manifest);m=read(manifest);b=io.BytesIO();h=hashlib.sha256()
    for row in m['chunks']:
        p=manifest.parent/row['path']
        if sha(p)!=row['sha256'] or p.stat().st_size!=row['bytes']:raise ValueError('Corrupt archive part')
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1048576),b''):b.write(block);h.update(block)
    if b.tell()!=m['bytes'] or h.hexdigest()!=m['sha256']:raise ValueError('Corrupt concatenation')
    b.seek(0);v=torch.load(b,map_location='cpu',weights_only=False);b.close();return v

