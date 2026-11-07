"""Own numerical stack and independent finite experiment paths."""
import sys,pathlib,json,gzip,hashlib,random,copy,math
D=pathlib.Path(__file__).resolve().parent;V=D.parent;H=V/'foundation-stage';P=V/'pretraining-scale';ROOT=V.parents[2]
sys.path.insert(0,str(H));sys.path.insert(0,str(V))
from runtime import torch,initial,save,record,sha,restore_isolated,trajectory,digest,causal_ce,clip_grad_accurate,loader
from core import decoder
from new_tokenizer import Encoder

def read(p):return json.loads(pathlib.Path(p).read_text())
def write(p,r):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def gzrows(p):
 with gzip.open(p,'rt')as f:return [json.loads(l)for l in f]
def gzwrite(p,rows):
 with pathlib.Path(p).open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,filename='')as z:
   for r in rows:z.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
def rank(s):return hashlib.sha256(('diverse-foundation-v1|'+s).encode()).hexdigest()
def canon(s):return ''.join(s.split()).casefold()
def pack(rows):
 x=torch.zeros((len(rows),256),dtype=torch.long);y=torch.full_like(x,-100)
 for i,r in enumerate(rows):
  t=r['tokens'];assert 2<=len(t)<=257 and 0 not in t and 1 not in t[1:] and 5 not in t
  n=len(t)-1;x[i,:n]=torch.tensor(t[:-1]);y[i,:n]=torch.tensor(t[1:])
 return x,y
