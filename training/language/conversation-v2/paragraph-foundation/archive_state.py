"""Archive own full state without changing tensors, optimizer or RNG."""
import pathlib,sys,hashlib,json,os,argparse
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent/'modern-corpus'))
from next_runtime import torch,digest,sha,write,legacy

def archive(raw,out):
 raw=pathlib.Path(raw);out=pathlib.Path(out);assert not(out/'checkpoint.json').exists();out.mkdir(parents=True,exist_ok=True)
 obj=torch.load(raw,map_location='cpu',weights_only=False);chunks=[];whole=hashlib.sha256()
 with raw.open('rb')as f:
  while b:=f.read(32*1024**2):
   name='part-%03d.bin'%len(chunks);pending=out/(name+'.pending');target=out/name
   with pending.open('wb')as g:g.write(b);g.flush();os.fsync(g.fileno())
   os.replace(pending,target);h=hashlib.sha256(b).hexdigest();assert sha(target)==h;whole.update(b);chunks.append(dict(path=name,bytes=len(b),sha256=h))
 m=dict(sha256=whole.hexdigest(),bytes=raw.stat().st_size,chunks=chunks,full_state_digest=digest(obj),trajectory_digest=digest(obj['trajectory']),cursor=obj.get('active_cursor',obj.get('cursor')),optimizer_steps=sorted({int(v['step'])for v in obj['trajectory']['optimizer']['state'].values()}),formal_adoption=False,contains='Own model/Adam/Torch/private Python/global Python/NumPy RNG/cursor/trace; schedule identified by frozen protocol or plan SHA',protocol_sha256=obj.get('protocol_sha256'),plan_sha256=obj.get('plan_sha256'))
 write(out/'checkpoint.json',m);check=legacy.loader.load_checkpoint(out/'checkpoint.json',m['sha256']);assert digest(check)==m['full_state_digest'];return m
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('raw');a.add_argument('out');args=a.parse_args();torch.set_num_threads(2);print(json.dumps(archive(args.raw,args.out)))
