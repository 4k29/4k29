"""Read-only matched-update DEV curves; never score language or select a model."""
import pathlib,json,hashlib,datetime,time,sys
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
def read_events(p):
 raw=p.read_bytes();events=[]
 for line in raw.splitlines():
  try:events.append(json.loads(line))
  except json.JSONDecodeError:continue
 return raw,events

def compare():
 curves={};sources={};new_events=[]
 for n in [34,35,36]:
  p=R.parent/f'round{n}/execution/train.log';raw,events=read_events(p)
  curves[n]={e['step']:e for e in events if 'validation'in e}
  sources[f'round{n}']=dict(path=str(p.relative_to(R.parent)),observedLogSha256=hashlib.sha256(raw).hexdigest(),observedLogBytes=len(raw),liveTrainingLog=n==36 and not any(e.get('event')=='finished'for e in events))
  if n==36:new_events=events
 rows=[]
 for step,new in sorted(curves[36].items()):
  assert step in curves[34]and step in curves[35]
  records={}
  for n in [34,35,36]:
   e=curves[n][step];v=e['validation'];records[f'round{n}']=dict(nllPerUtf8Byte=v['nllPerUtf8Byte'],perView={key:dict(nllPerUtf8Byte=x['nllPerUtf8Byte'],tokens=x['tokens'],utf8Bytes=x['utf8Bytes'],sites={s:z['nllPerUtf8Byte']for s,z in x['sites'].items()})for key,x in v['views'].items()},auxiliaryEosPositions=e.get('endEosPositions'),rolloutGeneratedTokens=e.get('rolloutGeneratedTokens'),rolloutNegativePositions=e.get('rolloutNegativePositions'))
  for view,x in records['round36']['perView'].items():
   for n in [34,35]:
    old=records[f'round{n}']['perView'][view]
    assert x['tokens']==old['tokens']and x['utf8Bytes']==old['utf8Bytes']and x['sites'].keys()==old['sites'].keys()
  if step:assert records['round36']['auxiliaryEosPositions']==records['round35']['auxiliaryEosPositions']
  a,b,c=[records[f'round{n}']['nllPerUtf8Byte']for n in [34,35,36]]
  rows.append(dict(actualUpdatesEach=step,models=records,newMinusCoefficientOne=c-b,newMinusCoefficientZero=c-a))
 finished=any(e.get('event')=='finished'for e in new_events)
 out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),latestValidatedActualUpdates=rows[-1]['actualUpdatesEach'],completedRun=finished,sourceLogs=sources,rows=rows,coefficients={'round34':0,'round35':1,'round36':.3},notAdditionalTrainingConditions=True,additionalOptimizerUpdates=0,notUsedForCheckpointSelection=True,notNewTest=True,noAutomaticLanguageOrAdoptionConclusion=True,limitations=['Previously exposed common DEV; excludes expanded human-chat DEV','Weighted segmentation diagnostic is not probability of independent text','No independent seed replication or significance claim','Autoregressive negative targets change as models differ, despite paired data RNG and prefix histories'],codeSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest())
 target=E/'paired-validation-progress.json';tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(target)
 lines=['# Matched actual-update DEV curves','','Same aligned Round28 model/optimizer/RNG; only EOS coefficient differs across these existing rounds. These are exposed common DEV diagnostics, excluding expanded human-chat DEV. No semantic/adoption conclusion and no additional training.','','| Actual updates each | R34 coef0 | R35 coef1 | R36 coef0.3 | R36−R35 | R36−R34 |','|---:|---:|---:|---:|---:|---:|']
 for x in rows:lines.append('| '+str(x['actualUpdatesEach'])+' | '+' | '.join(f"{x['models'][f'round{n}']['nllPerUtf8Byte']:.12f}"for n in [34,35,36])+f" | {x['newMinusCoefficientOne']:+.12f} | {x['newMinusCoefficientZero']:+.12f} |")
 (E/'PAIRED_VALIDATION_PROGRESS.md').write_text('\n'.join(lines)+'\n');return out
if __name__=='__main__':
 while True:
  x=compare();print(json.dumps(dict(latestValidatedActualUpdates=x['latestValidatedActualUpdates'],completedRun=x['completedRun'],additionalOptimizerUpdates=0)),flush=True)
  if '--watch'not in sys.argv or x['completedRun']:break
  time.sleep(30)
