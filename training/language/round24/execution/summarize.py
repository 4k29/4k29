"""Build traceable comparison, loss CSV and unabridged reading artifact."""
import pathlib,json,hashlib,csv,re
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'execution'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
audit=read(OUT/'optimizer-audit.json');models={}
for name in ['old','new']:
 g=read(OUT/f'{name}-validation.json');r=read(OUT/f'{name}-review.json');j=read(OUT/f'{name}-validation-js.json');manual=read(OUT/f'{name}-manual.json')
 assert r['generationSha256']==manual['generationSha256']==sha(OUT/f'{name}-validation.json')
 assert r['meaningPolicySha256']==sha(ROOT.parent/'round10/full-meaning-policy.json')
 assert j['modelSha256']==g['modelFileSha256']
 assert g['maxNewTokens']==192 and g['evaluationThreads']==1 and len(g['rows'])==17
 for a,b in zip(g['rows'],r['rows'],strict=True):assert all(a[k]==b[k] for k in ['id','text','tokens','prefix','eos','validUtf8','validTokens','inputTokens'])
 mismatches=[a['id'] for a,b in zip(g['rows'],j['rows'],strict=True) if any(a[k]!=b[k] for k in ['id','text','tokens','eos','validUtf8','validTokens','inputTokens'])]
 assert j['completeGenerationParity']==(not mismatches)
 assert r['gatePassed']==all(s['gatePassed'] for s in r['scopes'].values())
 models[name]=dict(firstSentencePasses=r['passed'],nonLoopOutputs=r['fullOutputNonLoop'],meaningfulFullOutputs=r['fullOutputMeaningful'],validTokenOutputs=r['validTokenOutputs'],gatePassed=r['gatePassed'],scopes=r['scopes'],completeSequenceParity=j['completeGenerationParity'],matchingSequences=17-len(mismatches),mismatches=mismatches,maxReferenceLogitError=max(x['maxAbsoluteError'] for x in j['references']),generationSha256=sha(OUT/f'{name}-validation.json'),manualSha256=sha(OUT/f'{name}-manual.json'),modelSha256=g['modelFileSha256'])
assert models['new']['modelSha256']==audit['modelSha256']
write(OUT/'comparison.json',dict(actualCompletedUpdates=audit['actualCompletedUpdates'],requestedUpdates=10000,remainingUpdates=10000-audit['actualCompletedUpdates'],completedRun=audit['completedRun'],selectedStep=audit['selectedStep'],developmentLanguageGatePassed=models['new']['gatePassed'],models=models,naturalJapaneseEstablished=False,developmentOnly=True,unseenGeneralizationEstablished=False,testEncodedOrGenerated=False,publicModelReplaced=False,independentHumanEvaluation=False,selectionUsedGeneratedOutputs=False))
with (OUT/'loss-history.csv').open('w') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['step','sampled_combined_objective','weighted_development_nll_per_utf8_byte','canonical_nll_per_byte','glyph_nll_per_byte','random_character_cuts_nll_per_byte','learning_rate','elapsed_seconds'])
 for h in read(ROOT/'continue-10000/metrics.json')['history']:
  v=h['validation'];w.writerow([h['step'],h.get('trainingLoss',''),v['nllPerUtf8Byte'],*(v['views'][str(k)]['nllPerUtf8Byte'] for k in range(3)),h.get('learningRate',''),h['elapsedSeconds']])
with (OUT/'training-loss-events.csv').open('w') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['step','sampled_combined_objective','cross_entropy','unlikelihood','negative_candidates','elapsed_seconds'])
 for path in [OUT/'train.log']:
  for line in path.read_text().splitlines():
   h=json.loads(line)
   if 'trainingLoss' in h:w.writerow([h['step'],h['trainingLoss'],h['crossEntropyLoss'],h['unlikelihoodLoss'],h['negativeCandidates'],h['elapsedSeconds']])
text=['# Unabridged raw Japanese continuations — development only','', 'Greedy full vocabulary, max192 new tokens, true EOS stop. No rewriting, filtering, retrieval, templates or repetition penalties. JSON files retain every token ID, exact Unicode text and byte validity; fullwidth whitespace is preserved there. Both models use the same17 openings and settings. These are not new TEST results.','']
old=read(OUT/'old-validation.json');new=read(OUT/'new-validation.json')
for a,b in zip(old['rows'],new['rows'],strict=True):
 assert a['id']==b['id'] and a['prefix']==b['prefix']
 fence='`'*max(3,max((len(x) for x in re.findall(r'`+',a['text']+b['text']+a['prefix'])),default=0)+1)
 text.extend(['## '+a['id'],'','Opening:','',fence+'text',a['prefix'],fence,'','Old full continuation:','',fence+'text',a['text'],fence,'',f"New full continuation (selected step{audit['selectedStep']}, actual completed updates{audit['actualCompletedUpdates']}):",'',fence+'text',b['text'],fence,''])
(OUT/'FULL_GENERATIONS.md').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(models=models,actualCompletedUpdates=audit['actualCompletedUpdates']),ensure_ascii=False))
