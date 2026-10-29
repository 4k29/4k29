import sys,pathlib,json,hashlib,gzip
P=pathlib.Path(__file__).resolve().parent;V=P.parent;H=V/'foundation-stage';N=V/'boundary-study';ROOT=V.parents[2]
sys.path.insert(0,str(H));sys.path.insert(0,str(V))
from runtime import torch,initial,save,record,sha,restore_isolated,trajectory,digest,causal_ce,clip_grad_accurate,pack,loader
from core import decoder
from new_tokenizer import Encoder

def write(p,d):
 p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def read(p):return json.loads(p.read_text())
def gzrows(p):return list(map(json.loads,gzip.open(p,'rt')))
def gzipwrite(p,rows):
 with p.open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,filename='')as z:
   for r in rows:z.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
def rank(s):return hashlib.sha256(('jp-pretrain-scale-v1|'+s).encode()).hexdigest()
def canon(s):return ''.join(s.split()).casefold()
