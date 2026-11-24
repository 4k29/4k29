"""Lossless <=32MiB chunks, atomic manifest, reread full model/Adam/RNG before optional raw removal."""
import argparse,os,hashlib
from common import *
def archive(raw,out,remove=False):
 out.mkdir(exist_ok=True,parents=True);obj=torch.load(raw,map_location='cpu',weights_only=False);whole=hashlib.sha256();chunks=[]
 with raw.open('rb')as f:
  while b:=f.read(32*1024**2):
   p=out/('part-%03d.bin'%len(chunks));tmp=p.with_suffix('.pending')
   with tmp.open('wb')as dest:dest.write(b);dest.flush();os.fsync(dest.fileno())
   os.replace(tmp,p);h=hashlib.sha256(b).hexdigest();assert sha(p)==h;whole.update(b);chunks.append(dict(path=p.name,bytes=len(b),sha256=h))
 st=obj['trajectory'];manifest=dict(sha256=whole.hexdigest(),bytes=raw.stat().st_size,chunks=chunks,active_cursor=obj['active_cursor'],optimizer_step_values=sorted({int(v['step'])for v in st['optimizer']['state'].values()}),model_retained_update_counter=st['uniqueUpdates'],trajectory_digest=digest(st),plan_sha256=obj['plan_sha256'],formal_adoption=False,contains='full model/Adam/Torch RNG/private RNG/sampler cursor/trace')

 manifest_path=out/'checkpoint.json';pending=out/'checkpoint.pending'
 with pending.open('w')as f:f.write(json.dumps(manifest,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(pending,manifest_path);fd=os.open(out,os.O_RDONLY);os.fsync(fd);os.close(fd)
 check=loader.load_checkpoint(out/'checkpoint.json',manifest['sha256']);assert digest(check)==digest(obj)
 if remove:
  raw.unlink();fd=os.open(raw.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
 print(str(out),manifest['sha256'],flush=True)
 return manifest
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('raw');a.add_argument('folder');a.add_argument('--remove',action='store_true');args=a.parse_args();torch.set_num_threads(2);archive(P/args.raw,P/args.folder,args.remove)
