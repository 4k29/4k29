"""Lossless chunk restore and guarded execution; never restart a completed model."""
import pathlib,sys,json,hashlib,datetime,subprocess,fcntl,signal
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from checkpoint_chunks import restore

def retained_log(text,step):
 rows=[]
 for line in text.splitlines():
  try:row=json.loads(line)
  except json.JSONDecodeError:continue
  if row.get('step',step+1)<=step and ('validation' in row or 'trainingLoss' in row):rows.append(row)
 updates=[r['step'] for r in rows if 'trainingLoss' in r]
 if updates!=list(range(100,step+1,100)):raise ValueError('Retained training loss events missing or duplicated; recover original log before resume')
 return ''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows)

def require_resume(step,resume):
 if step>=10000:raise ValueError('Completed10000 updates already; refuse duplicate training or mutation')
 if not resume:raise ValueError('Existing partial checkpoint requires exact --resume')

def main():
 out=ROOT/'continue-10000';out.mkdir(exist_ok=True);log=ROOT/'execution/train.log';resume='--resume' in sys.argv[1:]
 with (out/'.training.lock').open('a+b') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise ValueError('Training process already holds this run lock; do not duplicate')
  data=ROOT/'multiview/train.tokens.bin';data_manifest=data.with_name(data.name+'.chunks.json')
  if not data.exists():
   if not data_manifest.exists():raise ValueError('Missing frozen training data and lossless parts')
   restore(data_manifest)
  for name in ['checkpoint.pt','checkpoint-0.pt']:
   raw=out/name;manifest=out/(name+'.chunks.json')
   if not raw.exists() and manifest.exists():restore(manifest)
  cp=out/'checkpoint.pt'
  if cp.exists():
   import torch
   torch.set_num_threads(1);saved=torch.load(cp,map_location='cpu',weights_only=False);require_resume(saved['step'],resume)
   assert sorted({int(s['step']) for s in saved['optimizer']['state'].values()})==[10000+saved['step']]
   original=log.read_text() if log.exists() else '';kept=retained_log(original,saved['step']);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
   archive=log.with_name('train-before-resume-'+stamp+'.log');archive.write_text(original);log.write_text(kept)
   with (ROOT/'execution/resume-records.jsonl').open('a') as f:f.write(json.dumps(dict(utc=stamp,retainedActualUpdates=saved['step'],archivedLog=archive.name,archiveSha256=hashlib.sha256(original.encode()).hexdigest(),exactRngAndOptimizerRestoredByFrozenTrainer=True,unretainedLogEventsArchived=True))+'\n')
  elif resume:raise ValueError('No raw or reconstructable checkpoint for requested resume')
  elif log.exists() or (out/'result.json').exists():raise ValueError('Existing run evidence without checkpoint; investigate before any new training')
  args=[sys.executable,str(ROOT/'train.py'),'--merges','512','--steps','10000','--dim','192','--layers','8','--heads','4','--batch','8','--threads','2','--seed','2049','--lr','2.2499999999999998e-05','--validation-every','500','--run','continue-10000','--precision','float32',*sys.argv[1:]]
  with log.open('ab',buffering=0) as output:
   child=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),))
   def forward(signum,frame):
    if child.poll() is None:child.send_signal(signum)
   signal.signal(signal.SIGTERM,forward);signal.signal(signal.SIGINT,forward);return child.wait()
if __name__=='__main__':
 try:sys.exit(main())
 except (ValueError,AssertionError) as e:print(str(e),file=sys.stderr);sys.exit(2)
