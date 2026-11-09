"""Lossless fixed chunks plus SHA; no model updates. Git-only restore is separate."""
import argparse
from mix_runtime import *
a=argparse.ArgumentParser();a.add_argument('cursor',type=int);n=a.parse_args().cursor
src=SCRATCH/f'MIX-{n}.pt';obj=torch.load(src,map_location='cpu',weights_only=False);assert integrity(obj)==obj['integrity'];out=P/'artifacts'/f'MIX-{n}';out.mkdir(parents=True,exist_ok=True);parts=[]
with src.open('rb') as f:
 i=0
 while b:=f.read(32*1024**2):
  p=out/f'part-{i:03d}.bin';assert not p.exists();p.write_bytes(b);parts.append(dict(path=p.name,bytes=len(b),sha256=sha(p)));i+=1
write(out/'checkpoint.json',dict(sha256=sha(src),bytes=src.stat().st_size,chunks=parts,cursor=n,integrity=obj['integrity'],plan_sha256=obj['plan_sha256'],optimizer_steps=sorted({int(v['step']) for v in obj['trajectory']['optimizer']['state'].values()}),formal_adoption=False))
print(str(out),sha(src))
