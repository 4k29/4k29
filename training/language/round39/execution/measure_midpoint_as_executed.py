import pathlib,json,hashlib,time,subprocess,sys
R=pathlib.Path('/workspace/4k29/training/language/round39');E=R/'execution';repo=R.parents[2];O=E/'paired-human-dev-5000';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
assert not(O/'comparison.json').exists(),'Already measured; inspect saved results'
while not(E/'retained-snapshots/5000/identity.json').exists():time.sleep(10)
paths={f'round{n}':R.parent/f'round{n}/execution/retained-snapshots/5000/checkpoint.pt'for n in [38,39]}
for n,p in paths.items():assert sha(p)==read(p.parent/'identity.json')['checkpointSha256']
f=E/'raw_midpoint_human_likelihood.py';assert not f.exists();s=(E/'raw_interim_human_likelihood.py').read_text().replace("checkpoint['step'] == 1000","checkpoint['step'] == 5000").replace('{21000}','{25000}').replace('rawCheckpointStep=1000','rawCheckpointStep=5000');f.write_text(s);O.mkdir(exist_ok=True)
a=dict(posthoc=True,actualUpdatesEach=5000,reason='Midpoint check of everyday source-dilution hypothesis after tiny raw1000 change; running10k condition and selector unchanged',checkpoints={k:sha(p)for k,p in paths.items()},canonicalHumanDev99Unchanged=True,rawFp32PythonOnly=True,noInterimExportOrJavascriptParityClaim=True,notUsedForSelection=True,notNewTest=True,additionalOptimizerUpdates=0,evaluatorSha256=sha(f));(O/'plan.json').write_text(json.dumps(a,indent=2)+'\n')
for label,p in paths.items():
 with(O/f'{label}.log').open('ab',buffering=0)as log:subprocess.run([sys.executable,str(f),'--model',str(p),'--out',str(O/f'{label}.json')],cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True)
a,b=[read(O/f'round{n}.json')for n in [38,39]]
for k in ['foldPolicySha256','tokenizerSha256','orderedCanonicalTokensSha256','serialization','window','evaluationThreads','batchSize']:assert a['identity'][k]==b['identity'][k]
d=[]
for x,y in zip(a['rows'],b['rows'],strict=True):
 assert x['dialogueId']==y['dialogueId']and x['serializedTextSha256']==y['serializedTextSha256'];d.append((y['negativeLogLikelihoodSum']-x['negativeLogLikelihoodSum'])/x['serializedUtf8Bytes'])
report=dict(actualUpdatesEach=5000,oldHumanDevNll=a['nllPerSerializedUtf8Byte'],newHumanDevNll=b['nllPerSerializedUtf8Byte'],newMinusOld=b['nllPerSerializedUtf8Byte']-a['nllPerSerializedUtf8Byte'],nominalFilesNewLower=sum(x<0 for x in d),nominalFilesNewHigher=sum(x>0 for x in d),correlatedAndOneDuplicateNotIndependentPopulation=True,allCanonicalTargetsAndWindowsExactlyMatched=True,rawFp32PythonOnly=True,notUsedForSelection=True,notNewTest=True,additionalOptimizerUpdates=0,meaningNotJudgedByNll=True,resultSha256={n:sha(O/n)for n in ['round38.json','round39.json','plan.json']});(O/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
