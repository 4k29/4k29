"""Archive complete new states losslessly; inherited checkpoints remain untouched."""
import argparse,hashlib,json,os,pathlib
from common import N,torch,digest
from runtime import loader
def main():
 p=argparse.ArgumentParser();p.add_argument('names',nargs='+');a=p.parse_args()
 for name in a.names:
  raw=N/'run'/name/'checkpoint.pt';out=N/'run'/name/'archive';out.mkdir(parents=True,exist_ok=True);s=torch.load(raw,map_location='cpu',weights_only=False);assert s['active_cursor']==len(s['trace']);st=s['trajectory'];steps={int(v['step'])for v in st['optimizer']['state'].values()};assert steps=={st['uniqueUpdates']}
  whole=hashlib.sha256();chunks=[]
  with raw.open('rb')as f:
   while b:=f.read(32*1024**2):
    q=out/('part-%03d.bin'%len(chunks))
    with q.with_suffix('.pending').open('wb')as target:target.write(b);target.flush();os.fsync(target.fileno())
    os.replace(q.with_suffix('.pending'),q);sha=hashlib.sha256(b).hexdigest();assert hashlib.sha256(q.read_bytes()).hexdigest()==sha;whole.update(b);chunks.append(dict(path=q.name,bytes=len(b),sha256=sha))
  m=dict(sha256=whole.hexdigest(),bytes=raw.stat().st_size,chunks=chunks,active_cursor=s['active_cursor'],optimizer_step=st['uniqueUpdates'],trajectory_digest=digest(st),contains='full own model/Adam/Torch RNG/private RNG/legacy sampler provenance/active cursor/full trace',formal_adoption=False)
  manifest=out/'checkpoint.json'
  with manifest.with_suffix('.pending').open('w')as target:target.write(json.dumps(m,indent=2)+'\n');target.flush();os.fsync(target.fileno())
  os.replace(manifest.with_suffix('.pending'),manifest);fd=os.open(out,os.O_RDONLY);os.fsync(fd);os.close(fd)
  restored=loader.load_checkpoint(manifest,m['sha256']);assert digest(restored['trajectory'])==m['trajectory_digest']and restored['trace']==s['trace'];(N/'run'/(name+'-trace.json')).write_text(json.dumps(s['trace'],indent=2)+'\n');raw.unlink();fd=os.open(raw.parent,os.O_RDONLY);os.fsync(fd);os.close(fd);print(name,m['sha256'],'full state verified',flush=True)
if __name__=='__main__':main()
