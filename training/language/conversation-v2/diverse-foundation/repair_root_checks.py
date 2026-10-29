"""Temporarily restore only absent tracked Git blobs for unchanged legacy tests, then omit copies again."""
import pathlib,json,subprocess,hashlib,shutil,re,time
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3]
def main():
 initial=json.loads((D/'ROOT_ENVIRONMENT_FAILURES.json').read_text());records=[]
 for test in initial['affected_test_files']:
  restored={};attempts=[]
  try:
   for attempt in range(30):
    t=time.monotonic();r=subprocess.run(['node','--test',test],cwd=ROOT,capture_output=True,text=True);log=r.stdout+r.stderr;out=D/'root-repair'/f'{pathlib.Path(test).stem}-{attempt}.log';out.parent.mkdir(exist_ok=True);out.write_text(log);attempts.append(dict(log=str(out.relative_to(D)),returncode=r.returncode,seconds=time.monotonic()-t))
    if r.returncode==0:break
    missing=sorted(set(re.findall(r"ENOENT[^\n]*open '([^']+)'",log)));assert missing,log[-1500:]
    for raw_path in missing:
     path=pathlib.Path(raw_path).resolve();rel=str(path.relative_to(ROOT));assert not path.exists()and rel not in restored
     blob=subprocess.check_output(['git','rev-parse','HEAD:'+rel],cwd=ROOT,text=True).strip();size=int(subprocess.check_output(['git','cat-file','-s',blob],cwd=ROOT));assert shutil.disk_usage(D).free-size>850*1024**2,'Preserve atomic checkpoint reserve during temporary restore'
     raw=subprocess.check_output(['git','cat-file','blob',blob],cwd=ROOT);assert len(raw)==size;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest();assert hashlib.sha256(path.read_bytes()).hexdigest()==digest;restored[rel]=dict(git_blob=blob,sha256=digest,bytes=size)
   else:raise RuntimeError('Legacy restoration attempt bound exceeded')
   records.append(dict(test=test,passed=r.returncode==0,attempts=attempts,temporary_Git_restorations=restored))
  finally:
   for rel,m in restored.items():
    path=ROOT/rel;assert hashlib.sha256(path.read_bytes()).hexdigest()==m['sha256'];path.unlink()
  (D/'ROOT_REPAIR.json').write_text(json.dumps(dict(affected_test_files=records,all_affected_passed=len(records)==len(initial['affected_test_files'])and all(r['passed']for r in records),scope='Original tests unchanged. Temporarily absent working files restored by exact HEAD blob only, SHA checked before removing temporary copies. Initial full-run935passes/27ENOENT remain in ROOT_CHECKS_INITIAL. Not a single complete rerun.',optimizer_updates=0),indent=2)+'\n')
 # Independent remaining commands were not reached by the original fail-fast wrapper.
 commands=[['node','evaluation/evaluate-japanese.mjs']]
 for line in(ROOT/'.github/workflows/check-site.yml').read_text().splitlines():
  if line.strip().startswith('node --check '):commands.append(line.strip().split())
 final=[]
 with(D/'ROOT_REMAINING.log').open('w')as f:
  for c in commands:
   r=subprocess.run(c,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT);final.append(dict(command=c,returncode=r.returncode))
 (D/'ROOT_REMAINING.json').write_text(json.dumps(dict(commands=final,all_passed=all(r['returncode']==0 for r in final),optimizer_updates=0),indent=2)+'\n')
 assert all(r['returncode']==0 for r in final);print('All affected unchanged legacy tests restored and passed; remaining root checks passed')
if __name__=='__main__':main()
