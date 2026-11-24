"""Restore only from Git blobs; verify each chunk and whole file before atomic rename."""
import argparse,pathlib,subprocess,json,hashlib,os,shutil
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3]
a=argparse.ArgumentParser();a.add_argument('--model',required=True,choices=['initial','control-LF2','LF1-4','LF1-289','LF1-579']);a.add_argument('--commit',default='HEAD');a.add_argument('--destination',required=True);args=a.parse_args()
paths={'initial':'training/language/conversation-v2/modern-corpus/next-foundation/artifacts/B-6361','control-LF2':'training/language/conversation-v2/paragraph-foundation/artifacts/B-579'};rel=paths.get(args.model,str(P.relative_to(ROOT)/'artifacts'/args.model))
def blob(n):return subprocess.check_output(['git','show',args.commit+':'+n],cwd=ROOT)
m=json.loads(blob(rel+'/checkpoint.json'));dest=pathlib.Path(args.destination);dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists(),'Never overwrite existing checkpoint';assert shutil.disk_usage(dest.parent).free>m['bytes']+256*1024**2
h=hashlib.sha256();n=0;temp=dest.with_suffix('.pending');assert not temp.exists(),'Inspect existing incomplete file first'
with temp.open('wb') as f:
 for c in m['chunks']:
  b=blob(rel+'/'+c['path']);assert len(b)==c['bytes'] and hashlib.sha256(b).hexdigest()==c['sha256'];f.write(b);h.update(b);n+=len(b)
 f.flush();os.fsync(f.fileno())
assert h.hexdigest()==m['sha256'] and n==m['bytes'];os.replace(temp,dest);fd=os.open(dest.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
print(json.dumps(dict(model=args.model,commit=args.commit,sha256=h.hexdigest(),bytes=n,source='Git blobs only')))
