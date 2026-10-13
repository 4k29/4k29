"""Read only finished sibling results against the prospective continuation criterion."""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
policy=json.loads((ROOT/'policy.json').read_text());threshold=policy['nllSuccessThreshold'];rows=[]
for n in (13,14,15):
 r=ROOT.parent/f'round{n}';audit=json.loads((r/'execution/optimizer-audit.json').read_text());comparison=json.loads((r/'execution/comparison.json').read_text())
 assert audit['actualCompletedUpdates']==comparison['actualCompletedUpdates']==10000 and audit['completedRun']
 rows.append(dict(round=n,retainedActualUpdates=10000,bestCommonDevelopmentNll=audit['bestWeightedDevelopmentNllPerByte'],strictDevelopmentGatePassed=comparison['models']['new']['gatePassed'],comparisonSha256=hashlib.sha256((r/'execution/comparison.json').read_bytes()).hexdigest()))
met=any(r['bestCommonDevelopmentNll']<threshold or r['strictDevelopmentGatePassed'] for r in rows)
record=dict(threshold=threshold,criterion='Common development NLL strictly below Round11 best OR unchanged strict development language gate',checkedResults=rows,criterionMet=met,round16Decision='skip' if met else 'run',nllImprovementDoesNotEstablishNaturalLanguage=True,newTestGenerated=False)
(ROOT/'execution/goal-before-round16.json').write_text(json.dumps(record,indent=2)+'\n')
print(record['round16Decision'])
