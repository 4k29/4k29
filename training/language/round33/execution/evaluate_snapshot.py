"""Read-only additional exposed-DEV evaluation of an already saved snapshot."""
import pathlib,json,subprocess,sys,datetime,argparse
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';repo=R.parents[2];p=argparse.ArgumentParser();p.add_argument('--snapshot',type=pathlib.Path,required=True);a=p.parse_args();D=a.snapshot.resolve();m=json.loads((D/'snapshot.json').read_text());assert 0<m['actualRetainedUpdatesAtSnapshot']<10000
if (D/'mechanical-complete.json').exists():raise ValueError('Existing diagnostic; inspect instead of duplicating')
model=D/'model.js';statuses={}
def run(label,args,log):
 with (D/log).open('ab',buffering=0)as f:code=subprocess.run(args,cwd=repo,stdout=f,stderr=subprocess.STDOUT).returncode
 statuses[label]=code;return code
for label,script in [('daily',E/'evaluate_daily.py'),('native',E/'content-native-dev/evaluate.py')]:
 gen=D/f'{label}-python.json'
 if run(label+'Generation',[sys.executable,str(script),'--model',str(model),'--out',str(gen)],f'{label}-generation.log')==0:
  run(label+'JavaScript',['node',str(R.parent/'round10/evaluate_js.mjs'),str(model),str(gen),str(D/f'{label}-javascript.json')],f'{label}-parity.log')
  run(label+'RawExport',[sys.executable,str(E/'check_snapshot_rounding.py'),'--snapshot',str(D),'--generation',str(gen),'--out',str(D/f'{label}-unrounded.json')],f'{label}-rounding.log')
run('humanDevelopmentLikelihood',[sys.executable,str(E/'daily_human_likelihood.py'),'--model',str(model),'--out',str(D/'human-dev-likelihood.json')],'human-dev-likelihood.log')
(D/'mechanical-complete.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualRetainedAtInferenceSnapshot=m['actualRetainedUpdatesAtSnapshot'],selectedStep=m['selectedStep'],allMidpointMechanicalsFinished=not any(statuses.values()),exitCodes=statuses,semanticReadingPending=True,additionalOptimizerUpdates=0,liveTrainingNotSignaled=True,notNewTest=True),indent=2)+'\n');print(json.dumps(statuses));raise SystemExit(int(any(statuses.values())))
