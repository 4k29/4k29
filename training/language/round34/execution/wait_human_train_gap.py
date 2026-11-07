"""Final same-model human TRAIN/DEV diagnostics only; no selection or learning."""
import pathlib,json,time,subprocess,sys,datetime,hashlib
E=pathlib.Path(__file__).resolve().parent;R=E.parent;O=E/'human-train-gap';read=lambda p:json.loads(p.read_text());repo=R.parents[2]
while True:
 time.sleep(45)
 try:
  p=E/'automatic-publish-complete.json';t=E/'terminal-state-diagnostic/mechanical-complete.json'
  if p.exists()and t.exists()and read(p)['actualRetainedAdditionalUpdates']==10000 and all((E/n).exists()for n in ['daily-human-old-likelihood.json','daily-human-new-likelihood.json']):break
 except (json.JSONDecodeError,FileNotFoundError):continue
O.mkdir(exist_ok=True)
if (O/'complete.json').exists():raise SystemExit('Existing gap diagnostic; do not duplicate')
def run(args):
 with (O/'evaluation.log').open('ab',buffering=0)as log:subprocess.run(args,cwd=repo,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,check=True)
records={}
for label,model,dev in [('parent',R.parent/'round33/continue-10000/model.js',E/'daily-human-old-likelihood.json'),('selected',R/'continue-10000/model.js',E/'daily-human-new-likelihood.json')]:
 train=O/f'{label}-train.json';run([sys.executable,str(E/'human_train_sample_likelihood.py'),'--model',str(model),'--out',str(train),'--reuse-exact']);a,b=read(train),read(dev);assert a['identity']['modelSha256']==b['identity']['modelSha256'];records[label]=dict(modelSha256=a['identity']['modelSha256'],evaluatedStep=a['sourceModelEvaluatedStep'],trainSampleNllPerByte=a['nllPerSerializedUtf8Byte'],devNllPerByte=b['nllPerSerializedUtf8Byte'],devMinusTrainSampleNll=b['nllPerSerializedUtf8Byte']-a['nllPerSerializedUtf8Byte'],trainUnits=a['documents'],devFiles=b['documents'])
terminal=read(E/'terminal-state-diagnostic/mechanical-complete.json')
if terminal['terminalAndSelectedWeightsExactlyEqual']:records['terminal']=dict(sameWeightsAsSelected=True,duplicateLossMeasurementAvoided=True,sourceProof='terminal-state-diagnostic/mechanical-complete.json')
else:
 model=E/'terminal-state-diagnostic/model.js';train=O/'terminal-train.json';dev=O/'terminal-dev.json';run([sys.executable,str(E/'human_train_sample_likelihood.py'),'--model',str(model),'--out',str(train),'--reuse-exact']);run([sys.executable,str(E/'daily_human_likelihood.py'),'--model',str(model),'--out',str(dev),'--reuse-exact']);a,b=read(train),read(dev);assert a['identity']['modelSha256']==b['identity']['modelSha256'];records['terminal']=dict(modelSha256=a['identity']['modelSha256'],evaluatedStep=a['sourceModelEvaluatedStep'],trainSampleNllPerByte=a['nllPerSerializedUtf8Byte'],devNllPerByte=b['nllPerSerializedUtf8Byte'],devMinusTrainSampleNll=b['nllPerSerializedUtf8Byte']-a['nllPerSerializedUtf8Byte'],trainUnits=99,devFiles=99)
report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),models=records,sourceTrainPlanSha256=hashlib.sha256((E/'human-train-gap-plan.json').read_bytes()).hexdigest(),sameCanonicalSerializationAndWindowing=True,notEntireExpandedTrainMean=True,trainSplitDoesNotImplyEveryTargetDirectlySeen=True,devIncludesOneExactDuplicatePair=True,trainAndDevContentLengthTopicsNotMatched=True,notUsedForCheckpointOrConditionSelection=True,notNewTest=True,noAutomaticOverfitOrLanguageConclusion=True,additionalOptimizerUpdates=0)
(O/'complete.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
