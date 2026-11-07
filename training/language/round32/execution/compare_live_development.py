"""Read-only common-step DEV comparison; never changes training or selection."""
import csv,json,pathlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
def validations(path):
 rows={}
 for line in path.read_text().splitlines():
  try:r=json.loads(line)
  except json.JSONDecodeError:continue
  if 'validation'in r:
   step=r['step'];assert step not in rows;rows[step]=r
 return rows
old=validations(R.parent/'round25/execution/train.log');new=validations(E/'train.log');out=[]
for step in sorted(new):
 assert step in old
 a,b=old[step],new[step];p=a['validation']['nllPerUtf8Byte'];q=b['validation']['nllPerUtf8Byte'];tokens=a.get('seenTargetTokens',0);byt=a.get('seenTargetUtf8Bytes',0)
 assert tokens==b.get('seenTargetTokens',0) and byt==b.get('seenTargetUtf8Bytes',0)
 out.append(dict(actualUpdatesEach=step,round25NllPerByte=p,round32NllPerByte=q,newMinusOld=q-p,maskedTargetsEach=tokens,utf8TargetBytesEach=byt))
assert out
with (E/'interim-development-comparison.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print(json.dumps(dict(latestCompletedValidation=out[-1],languageImprovementAssessed=False,additionalOptimizerUpdates=0,notTest=True)))
