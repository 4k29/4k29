"""Predeclared read-only equal-update diagnostics; no trainer/policy changes."""
import pathlib,json,subprocess,sys,time,datetime,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';repo=R.parents[2];read=lambda p:json.loads(p.read_text())
def run(args,log):
 with log.open('ab',buffering=0)as f:subprocess.run(args,cwd=repo,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,check=True)
for step in [1000,5000]:
 new=E/f'retained-snapshots/{step}/checkpoint.pt'
 while not new.exists():time.sleep(30)
 O=E/f'paired-human-dev-{step}';O.mkdir(exist_ok=True)
 assert not(O/'complete.json').exists(),'Inspect existing result instead of duplicate diagnostics'
 for label,cp in [('old',R.parent/f'round42/execution/retained-snapshots/{step}/checkpoint.pt'),('new',new)]:
  script='raw_interim_human_likelihood.py'if step==1000 else 'raw_midpoint_human_likelihood.py'
  run([sys.executable,str(E/script),'--model',str(cp),'--out',str(O/f'{label}-human.json')],O/'evaluation.log')
  run([sys.executable,str(E/'context_diagnostic.py'),'evaluate','--model',str(cp),'--out',str(O/f'{label}-context.json')],O/'evaluation.log')
 a,b=read(O/'old-human.json'),read(O/'new-human.json');assert a['orderedCanonicalTokensSha256']==b['orderedCanonicalTokensSha256'] if 'orderedCanonicalTokensSha256'in a else a['identity']['orderedCanonicalTokensSha256']==b['identity']['orderedCanonicalTokensSha256']
 if step==1000:run([sys.executable,str(E/'diagnose_paired_1000_daily_corrected.py')],O/'evaluation.log')
 (O/'complete.json').write_text(json.dumps(dict(actualUpdatesEach=step,oldHumanNllPerByte=a['nllPerSerializedUtf8Byte'],newHumanNllPerByte=b['nllPerSerializedUtf8Byte'],noTrainingOrSelectionChange=True,notNewTest=True,rawPythonFp32Only=True,fullDailyReadingPending=step==1000,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
 print('Finished predeclared equal-update diagnostics',step,flush=True)
