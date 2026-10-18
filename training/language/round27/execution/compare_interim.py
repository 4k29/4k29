"""Read-only mid-run comparison; no model selection or condition adjustment."""
import pathlib,json,torch,hashlib,datetime
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());torch.set_num_threads(1)
cp=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);old=read(R.parent/'round25/continue-10000/metrics.json')['history'];history=cp['history'];assert cp['step']>=5000
by_step={r['step']:r for r in old};rows=[]
for row in history:
 previous=by_step[row['step']]
 if row['step']:
  assert previous['seenTargetTokens']==row['seenTargetTokens'] and previous['seenTargetUtf8Bytes']==row['seenTargetUtf8Bytes']
 rows.append(dict(step=row['step'],oldNll=previous['validation']['nllPerUtf8Byte'],newNll=row['validation']['nllPerUtf8Byte'],newMinusOld=row['validation']['nllPerUtf8Byte']-previous['validation']['nllPerUtf8Byte']))
record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),retainedActualUpdates=cp['step'],requestedUpdates=10000,completedRun=cp['step']==10000,matchedValidationPoints=len(rows),sameExposureEveryMatchedPoint=True,positiveValidationPointsBetter=sum(x['newMinusOld']<0 for x in rows if x['step']),positiveValidationPointsWorse=sum(x['newMinusOld']>0 for x in rows if x['step']),bestSelectedStepSoFar=cp['beststep'],bestNllSoFar=cp['bestloss'],seenTargetTokens=cp['seen_tokens'],seenTargetUtf8Bytes=cp['seen_bytes'],rolloutCalls=cp['rolloutCalls'],rolloutGeneratedTokens=cp['rolloutGeneratedTokens'],rolloutNegativePositions=cp['rolloutNegativePositions'],rows=rows,additionalOptimizerUpdates=0,conditionsChanged=False,semanticGenerationNotYetAssessed=True,noNewTestRead=True)
(E/'interim-comparison.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='rows'}))
