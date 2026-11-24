"""Paired frozen DEV checks, descriptive only; added data changes exposure."""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
old=read(R.parent/'round19/continue-10000/metrics.json');new=read(R/'continue-10000/metrics.json')
a={x['step']:x for x in old['history']};rows=[]
for b in new['history']:
 x=a[b['step']];u=x['validation']['nllPerUtf8Byte'];v=b['validation']['nllPerUtf8Byte']
 rows.append(dict(step=b['step'],oldNllPerUtf8Byte=u,newNllPerUtf8Byte=v,differenceNewMinusOld=v-u))
threshold=read(R/'policy.json')['nllSuccessThreshold']
out=dict(control='Round19 pure CE, same aligned Round11 parent',rows=rows,predeclaredNllSuccessThreshold=threshold,bestNewNll=min(x['newNllPerUtf8Byte'] for x in rows),nllThresholdPassed=min(x['newNllPerUtf8Byte'] for x in rows)<threshold,postUpdateChecksBetterThanControl=sum(x['step']>0 and x['differenceNewMinusOld']<0 for x in rows),postUpdateChecks=sum(x['step']>0 for x in rows),statisticalSignificanceEstablished=False,limitation='One seed, exposed DEV; new TRAIN lengths alter sampling and actual target exposure. No pure semantic coverage effect or fresh generalization claim.')
(R/'execution/paired-loss-comparison.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
