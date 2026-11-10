"""Reconstruct this study's full state from Git, verify each chunk, atomic output. Zero updates."""
import argparse,pathlib,subprocess,json,hashlib,os
ap=argparse.ArgumentParser();ap.add_argument('--revision',default='HEAD');ap.add_argument('--cursor',required=True,type=int,choices=[4,205,401]);ap.add_argument('--output',required=True);a=ap.parse_args();root=pathlib.Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip());prefix=f'training/language/conversation-v2/mixed-volume-study/artifacts/VOLUME-{a.cursor}/';blob=lambda path:subprocess.check_output(['git','show',f'{a.revision}:{prefix}{path}'],cwd=root);meta=json.loads(blob('checkpoint.json'));dest=pathlib.Path(a.output).resolve();tmp=dest.with_name(dest.name+'.partial');assert not dest.exists() and not tmp.exists(),'Refuse overwrite';dest.parent.mkdir(parents=True,exist_ok=True);assert os.statvfs(dest.parent).f_bavail*os.statvfs(dest.parent).f_frsize>meta['bytes']+64*1024**2,'Insufficient atomic output reserve';h=hashlib.sha256()
with tmp.open('xb') as f:
 for c in meta['chunks']:
  b=blob(c['path']);assert hashlib.sha256(b).hexdigest()==c['sha256'];f.write(b);h.update(b)
 f.flush();os.fsync(f.fileno())
assert h.hexdigest()==meta['sha256'];os.replace(tmp,dest);fd=os.open(dest.parent,os.O_DIRECTORY);os.fsync(fd);os.close(fd);print(json.dumps(dict(output=str(dest),sha256=h.hexdigest(),cursor=a.cursor,optimizer_calls=0,model_forwards=0)))
