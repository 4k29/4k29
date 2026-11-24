"""Copy a newly saved best-aligned full state without altering the live trainer.
Never invent moments/RNG for a past selected step that was not captured.
"""
import datetime,hashlib,io,json,pathlib,time,torch,sys
R=pathlib.Path(__file__).resolve().parents[1];OUT=R/'continue-10000';E=R/'execution';torch.set_num_threads(1)
seen=None
while True:
 p=OUT/'checkpoint.pt'
 if not p.exists():time.sleep(5);continue
 stamp=p.stat().st_mtime_ns
 if stamp==seen:time.sleep(5);continue
 raw=p.read_bytes();cp=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False);seen=stamp
 if cp['step']==cp['beststep']:
  assert all(torch.equal(v,cp['beststate'][k]) for k,v in cp['model'].items())
  assert sorted({int(s['step']) for s in cp['optimizer']['state'].values()})==[10000+cp['step']]
  target=OUT/'best-aligned-checkpoint.pt';tmp=target.with_suffix('.tmp');tmp.write_bytes(raw);tmp.replace(target)
  record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualSnapshotUpdates=cp['step'],selectedStep=cp['beststep'],nll=cp['bestloss'],checkpointSha256=hashlib.sha256(raw).hexdigest(),alignedModelOptimizerAndTorchPrivatePythonRng=True,additionalOptimizerUpdates=0,liveTrainerNotModified=True)
  (E/'best-aligned-archive.json').write_text(json.dumps(record,indent=2)+'\n')
  with (E/'best-aligned-archives.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
  print(json.dumps(record),flush=True)
 if cp['step']==10000:
  info=E/'best-aligned-archive.json';target=OUT/'best-aligned-checkpoint.pt';captured=False
  if info.exists() and target.exists():
   saved=json.loads(info.read_text());captured=saved['actualSnapshotUpdates']==cp['beststep'] and hashlib.sha256(target.read_bytes()).hexdigest()==saved['checkpointSha256']
  print(json.dumps(dict(event='archive-monitor-finished',actualTrainingUpdates=10000,selectedStep=cp['beststep'],selectedOptimizerArchiveCaptured=captured,pastUncapturedSelectedMomentsNotInvented=True)),flush=True);break
 if '--once' in sys.argv:break
 time.sleep(5)
