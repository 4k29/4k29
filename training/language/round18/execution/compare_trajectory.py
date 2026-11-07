"""Same-parent, same-update-budget exposed-DEV curve comparison; not causal proof."""
import pathlib,json,csv
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';models={}
for name in ['round16','round17','round18']:
 p=R.parent/name/'continue-10000/metrics.json';m=json.loads(p.read_text());models[name]={x['step']:x for x in m['history']}
initial=[m[0]['validation'] for m in models.values()];assert initial[0]==initial[1]==initial[2]
rows=[]
for step in sorted(models['round18']):
 if step not in models['round16'] or step not in models['round17']:continue
 row={'step':step}
 for n,m in models.items():
  x=m[step];row[n+'Nll']=x['validation']['nllPerUtf8Byte'];row[n+'TargetTokens']=x.get('seenTargetTokens',0);row[n+'TargetBytes']=x.get('seenTargetUtf8Bytes',0)
 row['round18MinusRound16']=row['round18Nll']-row['round16Nll'];row['round18MinusRound17']=row['round18Nll']-row['round17Nll'];rows.append(row)
(E/'paired-trajectory.json').write_text(json.dumps({'sameInitialValidationExactly':True,'exposedDevelopmentOnly':True,'observedThroughStep':max(models['round18']),'otherTrainingConditionsFixed':True,'sameUpdatesNotSameTokenOrByteExposure':True,'singleSeedNoStatisticalCausalProof':True,'rows':rows},indent=2)+'\n')
with (E/'paired-trajectory.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print(json.dumps(rows[-1]))
