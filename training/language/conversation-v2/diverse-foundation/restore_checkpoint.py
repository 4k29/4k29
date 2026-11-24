"""Byte-exact archived checkpoint restoration from working chunks or preserved committed Git blobs."""
import pathlib,json,hashlib,subprocess,os,sys
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3]
def restore(manifest,target):
 assert not target.exists(),'Preserve existing complete checkpoint'
 m=json.loads(manifest.read_text());tmp=target.with_suffix('.pending');h=hashlib.sha256();size=0
 with tmp.open('wb')as f:
  for c in m['chunks']:
   p=manifest.parent/c['path'];b=p.read_bytes()if p.exists()else subprocess.check_output(['git','show','HEAD:'+str(p.relative_to(ROOT))],cwd=ROOT);assert len(b)==c['bytes']and hashlib.sha256(b).hexdigest()==c['sha256'];f.write(b);h.update(b);size+=len(b)
  f.flush();os.fsync(f.fileno())
 assert h.hexdigest()==m['sha256']and size==m['bytes'];os.replace(tmp,target);fd=os.open(target.parent,os.O_RDONLY);os.fsync(fd);os.close(fd);return m['sha256']
if __name__=='__main__':print(restore(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve()))
