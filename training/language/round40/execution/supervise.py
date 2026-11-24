"""Detached training/evaluation plus checkpoint monitors; no duplicate controller."""
import datetime,fcntl,json,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';REPO=R.parents[2];OUT=R/'continue-10000'
def main():
 OUT.mkdir(exist_ok=True)
 with (OUT/'.controller.lock').open('a+b') as owner:
  try:fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise ValueError('Controller already running; do not duplicate')
  with (OUT/'.training.lock').open('a+b') as training:
   try:fcntl.flock(training,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise ValueError('Trainer already running; do not duplicate or publish its live state')
  result=OUT/'result.json'
  if result.exists() and json.loads(result.read_text()).get('completedRun'):raise ValueError('Completed trial; do not restart it. Run any missing evaluations separately.')
  cp=OUT/'checkpoint.pt'
  if cp.exists():
   import torch
   torch.set_num_threads(1);saved=torch.load(cp,map_location='cpu',weights_only=False)
   if saved['step']>=10000:raise ValueError('10000 updates already saved; do not mutate the completed trial')
  handles=[];monitors=[]
  try:
   for script,log in [('capture_milestones.py','milestone-monitor.log'),('watch_resume.py','watch-resume.log'),('archive_best_aligned.py','best-archive-monitor.log')]:
    f=(E/log).open('a');handles.append(f);monitors.append(subprocess.Popen([sys.executable,str(E/script)],cwd=REPO,stdout=f,stderr=subprocess.STDOUT))
   (E/'monitor-processes.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pids':[p.pid for p in monitors]},indent=2)+'\n')
   with (E/'pipeline.log').open('a') as log:
    status=subprocess.run(['bash',str(E/'pipeline.sh'),*sys.argv[1:]],cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
  finally:
   for p in monitors:
    if p.poll() is None:p.terminate()
   for p in monitors:p.wait()
   for f in handles:f.close()
  if cp.exists():
   with (E/'best-archive-monitor.log').open('a') as log:
    archive_status=subprocess.run([sys.executable,str(E/'archive_best_aligned.py'),'--once'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
   if archive_status and status==0:status=archive_status
   with (E/'selected-optimizer-verification.log').open('a') as log:
    verify_status=subprocess.run([sys.executable,str(E/'verify_best_archive.py')],cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
   if verify_status and status==0:status=verify_status
  with (E/'automatic-publish.log').open('a') as log:
   publish=subprocess.run([sys.executable,str(E/'publish_mechanical.py'),str(status)],cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
  return publish or status
if __name__=='__main__':
 try:raise SystemExit(main())
 except ValueError as e:print(str(e),file=sys.stderr);raise SystemExit(2)
