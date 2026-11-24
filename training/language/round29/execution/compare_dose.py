"""Compare frozen30% and10% doses at identical conditions; never guess semantics."""
import pathlib,json,hashlib,re,csv
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round28';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=read(P/'policy.json');b=read(R/'policy.json')
for k in ['seed','requestedUpdates','views','validationViews','learningRate','schedule','unlikelihood','sequenceUnlikelihood','parentCheckpointSha256','sourcePolicySha256','newSourceManifestSha256','newSourceDocumentsSha256','codeHashes']:assert a[k]==b[k],k
assert a['genreSampling']['human-chat']==.3 and b['genreSampling']['human-chat']==.1
for n in ['data.json','train.index.json','train.tokens.bin','tokenizer.json','validation.index.json','validation.tokens.bin']:assert sha(P/'multiview'/n)==sha(R/'multiview'/n),n
out=['# Unabridged dose comparison:30% vs10% human TRAIN mass','','Both are unadopted experiments until scored against last adoptedRound25. Same inputs/greedy192/trueEOS. ExposedDEV only, no TEST or rewriting. Semantic judgments are not guessed here.','']
for label,filename in [('Original17','new-validation.json'),('Daily12','daily-new-python.json')]:
 old=read(P/'execution'/filename);new=read(E/filename)
 for x,y in zip(old['rows'],new['rows'],strict=True):
  assert all(x[k]==y[k] for k in ['id','prefix','inputTokens'])
  fence='`'*max(3,max((len(t) for t in re.findall(r'`+',x['prefix']+x['text']+y['text'])),default=0)+1)
  out.extend(['## '+label+' / '+x['id'],'','Prefix:',fence+'text',x['prefix'],fence,'','Round28 mass30%:',fence+'text',x['text'],fence,'','Round29 mass10%:',fence+'text',y['text'],fence,''])
(E/'DOSE_FULL_GENERATIONS.md').write_text('\n'.join(out)+'\n')
old=read(P/'continue-10000/metrics.json')['history'];new=read(R/'continue-10000/metrics.json')['history'];rows=[]
for x,y in zip(old,new,strict=True):
 assert x['step']==y['step'];rows.append(dict(step=x['step'],round28CommonNll=x['validation']['nllPerUtf8Byte'],round29CommonNll=y['validation']['nllPerUtf8Byte']))
with (E/'dose-common-nll.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(E/'dose-comparison.json').write_text(json.dumps(dict(onlyLearningDifference='Human corpus mass30%→10%; all other genres proportional',samePreparedDataByteidentically=True,round28ManifestSha256=sha(P/'execution/artifact-manifest.json'),actualUpdatesEach=10000,fullText='DOSE_FULL_GENERATIONS.md',manualMeaningJudgmentPending=True,adoptedControlRemains='round25'),indent=2)+'\n')
print('Paired30%/10% full outputs and commonNLL curve saved; no semantic score invented')
