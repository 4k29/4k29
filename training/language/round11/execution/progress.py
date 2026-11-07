"""Read confirmed logs and last fixed development validation; never alters training."""
import pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
rows=[]
for name in ['train-0000-0500.log','train-0500-1000.log','train-1000-10000.log']:
 p=ROOT/'execution'/name
 if p.exists():
  for line in p.read_text().splitlines():
   try:rows.append(json.loads(line))
   except json.JSONDecodeError:pass # Trainer may currently be writing this line.
last=max((r for r in rows if 'step' in r or 'completedUpdates' in r),key=lambda r:r.get('step',r.get('completedUpdates')))
report={k:last[k] for k in ['event','step','completedUpdates','trainingLoss','elapsedSeconds'] if k in last}
m=json.loads((ROOT/'continue-10000/metrics.json').read_text());v=m['history'][-1]
report.update(lastValidationStep=v['step'],bestSelectedStep=m['bestStep'],weightedDevelopmentNllPerByte=v['validation']['nllPerUtf8Byte'],views={k:x['nllPerUtf8Byte'] for k,x in v['validation']['views'].items()})
print(json.dumps(report))
