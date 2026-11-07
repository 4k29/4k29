"""Read-only operational monitor; never changes or signals the live trainer."""
import pathlib,sys,subprocess,json,time,datetime,hashlib,io,torch,os
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';REPO=R.parents[2];torch.set_num_threads(1);write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,log):
 with log.open('ab',buffering=0) as f:subprocess.run(args,cwd=REPO,stdout=f,stderr=subprocess.STDOUT,check=True)
for target in [2000,5000]:
 laststamp=None
 while True:
  time.sleep(5)
  cp=R/'continue-10000/checkpoint.pt'
  if not cp.exists():continue
  stamp=cp.stat().st_mtime_ns
  if stamp==laststamp:continue
  laststamp=stamp
  raw=cp.read_bytes();s=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False)
  if s['step']>=10000:raise SystemExit('Final state reached before midpoint capture; do not mislabel final as interim')
  if s['step']>=target:break
 try:
  captured=subprocess.check_output([sys.executable,str(E/'snapshot_live_selected.py')],cwd=REPO,text=True).strip();D=pathlib.Path(captured);meta=json.loads((D/'snapshot.json').read_text());assert target<=meta['actualRetainedUpdatesAtSnapshot']<10000;model=D/'model.js';write(D/'prospective-target.json',dict(target=target,actualSnapshot=meta['actualRetainedUpdatesAtSnapshot'],selectedStep=meta['selectedStep'],trainingConditionsChanged=False,comparisonBaseline='round28 parent final, child additional local dose; not equal cumulative progress',supplementaryNativeProbeSha256=sha(E/'content-native-dev/probes.json')))
  # Independent full resume-state backup, its own actual count recorded by helper.
  latest=torch.load(io.BytesIO(cp.read_bytes()),map_location='cpu',weights_only=False)['step']
  if not (E/f'retained-progress-{latest}').exists():run([sys.executable,str(E/'save_live_progress.py')],D/'resume-backup.log')
  run([sys.executable,str(E/'evaluate_daily.py'),'--model',str(model),'--out',str(D/'daily-python.json')],D/'daily-generation.log')
  run(['node',str(R.parent/'round10/evaluate_js.mjs'),str(model),str(D/'daily-python.json'),str(D/'daily-javascript.json')],D/'daily-parity.log')
  run([sys.executable,str(E/'check_snapshot_rounding.py'),'--snapshot',str(D),'--generation',str(D/'daily-python.json'),'--out',str(D/'daily-unrounded.json')],D/'rounding.log')
  run([sys.executable,str(E/'content-native-dev/evaluate.py'),'--model',str(model),'--out',str(D/'native-python.json')],D/'native-generation.log')
  run(['node',str(R.parent/'round10/evaluate_js.mjs'),str(model),str(D/'native-python.json'),str(D/'native-javascript.json')],D/'native-parity.log')
  run([sys.executable,str(E/'check_snapshot_rounding.py'),'--snapshot',str(D),'--generation',str(D/'native-python.json'),'--out',str(D/'native-unrounded.json')],D/'native-rounding.log')
  run([sys.executable,str(E/'daily_human_likelihood.py'),'--model',str(model),'--out',str(D/'human-dev-likelihood.json')],D/'human-dev-likelihood.log')
  write(D/'mechanical-complete.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualRetainedAtInferenceSnapshot=meta['actualRetainedUpdatesAtSnapshot'],selectedStep=meta['selectedStep'],allMidpointMechanicalsFinished=True,semanticReadingPending=True,additionalOptimizerUpdates=0,liveTrainingNotSignaled=True));print('Midpoint mechanics complete',D,flush=True)
 except Exception as exc:
  write(E/f'midpoint-error-{target}.json',dict(error=str(exc),target=target,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),mainTrainingNotStopped=True));print('Midpoint failure; inspect explicit evidence',target,str(exc),flush=True)
