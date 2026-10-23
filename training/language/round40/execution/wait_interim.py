"""Post-launch read-only planned milestone diagnostics; never adjust the trial."""
import pathlib,json,subprocess,time,hashlib,sys
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';repo=R.parents[2]
def run(args):subprocess.run([sys.executable,*map(str,args)],cwd=repo,check=True)
for step in [1000,5000]:
 cp=E/f'retained-snapshots/{step}/checkpoint.pt'
 while not cp.exists():time.sleep(20)
 out=E/f'paired-human-dev-{step}';out.mkdir(exist_ok=True);script=E/('raw_interim_human_likelihood.py' if step==1000 else 'raw_midpoint_human_likelihood.py')
 old=R.parent/f'round39/execution/retained-snapshots/{step}/checkpoint.pt'
 for label,path in [('old',old),('new',cp)]:
  dest=out/f'{label}.json'
  if not dest.exists():run([script,'--model',path,'--out',dest])
 a=json.loads((out/'old.json').read_text());b=json.loads((out/'new.json').read_text());assert a['targetTokensIncludingEos']==b['targetTokensIncludingEos'] and a['identity']['orderedCanonicalTokensSha256']==b['identity']['orderedCanonicalTokensSha256']
 (out/'comparison.json').write_text(json.dumps(dict(actualUpdatesEach=step,oldHumanDevNll=a['nllPerSerializedUtf8Byte'],newHumanDevNll=b['nllPerSerializedUtf8Byte'],newMinusOld=b['nllPerSerializedUtf8Byte']-a['nllPerSerializedUtf8Byte'],allCanonicalTargetsAndWindowsExactlyMatched=True,rawFp32PythonOnly=True,notUsedForSelection=True,meaningImprovementEstablished=False),indent=2)+'\n')
 for label,path in [('old',old),('new',cp)]:
  dest=out/f'context-{label}.json'
  if not dest.exists():run([E/'context_diagnostic.py','evaluate','--model',path,'--out',dest])
 if step==1000 and not (E/'paired-daily-generation-1000/complete.json').exists():run([E/'diagnose_paired_1000_daily.py'])
 print('Interim milestone completed',step,flush=True)
