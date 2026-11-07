"""Export actual logged losses; instantaneous batches are not full-TRAIN means."""
import pathlib,json,csv,hashlib,math
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());events=[json.loads(x)for x in (E/'train.log').read_text().splitlines()];train=[x for x in events if 'trainingLoss'in x];valid=read(R/'continue-10000/metrics.json')['history'];assert [x['step']for x in train]==list(range(100,10001,100));assert [x['step']for x in valid]==list(range(0,10001,500))
keys=list(train[0]);keys.remove('event')
with(E/'training-loss-events.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(train)
rows=[dict(step=x['step'],validationNllPerOriginalUtf8Byte=x['validation']['nllPerUtf8Byte'],seenTargetTokens=x.get('seenTargetTokens',0),seenTargetUtf8Bytes=x.get('seenTargetUtf8Bytes',0),elapsedSeconds=x['elapsedSeconds'])for x in valid]
with(E/'loss-history.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
a=dict(actualOptimizerUpdates=10000,loggedTrainingBatches=100,fullMixedViewValidationEvents=21,trainValuesAreInstantaneousLoggedBatchesNotAllTrainMeans=True,combinedTrainingObjectiveDifferentFromPureValidationCe=True,originalTargetByteDenominatorUnchanged=True,codeSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest());(E/'loss-curve-scope.json').write_text(json.dumps(a,indent=2)+'\n');print(a)
