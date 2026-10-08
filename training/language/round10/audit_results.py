"""Confirm optimizer counters, frozen sources, own lineage and unedited raw review."""
import gzip,hashlib,json,pathlib
import torch
ROOT=pathlib.Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def audit_run(folder,steps):
 r=read(folder/'result.json');m=read(folder/'metrics.json');cp=torch.load(folder/'checkpoint.pt',map_location='cpu',weights_only=False)
 assert r['completedRun'] and r['completedSteps']==r['requestedSteps']==cp['step']==steps
 counts=sorted({int(s['step']) for s in cp['optimizer']['state'].values()});assert counts==[steps]
 assert all(t.dtype==torch.float32 for k in ['model','beststate'] for t in cp[k].values());assert all(s[k].dtype==torch.float32 for s in cp['optimizer']['state'].values() for k in ['exp_avg','exp_avg_sq'])
 assert all(torch.isfinite(t).all() for k in ['model','beststate'] for t in cp[k].values())
 assert isinstance(cp['pythonRng'],tuple) and cp['torchRng'].dtype==torch.uint8
 assert cp['beststep']==r['bestStep']==m['bestStep'] and cp['bestloss']==m['bestValidationNllPerByte']==min(x['validation']['nllPerUtf8Byte'] for x in m['history'])
 assert r['checkpointSha256']==sha(folder/'checkpoint.pt');assert r['ownParentOnly'] and r['ownRandomInitializedLineage'] and r['optimizerReset']
 assert not any(r[k] for k in ['externalWeights','externalTokenizer','externalInferenceAPI'])
 for field,file in [('trainerSourceSha256','train.py'),('batchingSourceSha256','batching.py'),('initializationSourceSha256','initialization.py'),('experimentPolicySha256','training-policy.json'),('rawUnitsSha256','units.json'),('sourceSha256','documents.jsonl'),('splitSha256','split.json')]:assert r[field]==sha(ROOT/file)
 directory=ROOT/f"word-bpe-{r['wordMerges']}";assert r['tokenizerSha256']==sha(directory/'tokenizer.json') and r['preparedDataSha256']==sha(directory/'data.json')
 return dict(run=folder.name,completedUpdates=steps,bestStep=r['bestStep'],bestValidationNllPerByte=m['bestValidationNllPerByte'],initialValidationNllPerByte=m['history'][0]['validation']['nllPerUtf8Byte'],checkpointSha256=r['checkpointSha256'],optimizerCounters=counts,parentSelectedWeightLineageUpdates=r['parentSelectedWeightLineageUpdates'],parameters=r['parameters'])
def main():
 torch.set_num_threads(1);vocabulary=read(ROOT/'vocabulary-choice.json');pilots=[audit_run(ROOT/f'word-{n}-pilot-1000',1000) for n in [512,1024]]
 winner=min(pilots,key=lambda p:(p['bestValidationNllPerByte'],int(p['run'].split('-')[1])));assert winner['run']==vocabulary['selectedRun'] and winner['checkpointSha256']==vocabulary['checkpointSha256']
 candidate=ROOT/f"word-{vocabulary['wordMerges']}-continue-10000";mainrun=audit_run(candidate,10000);r=read(candidate/'result.json')
 assert r['parentCheckpointSha256']==vocabulary['checkpointSha256'] and r['parentSelectedWeightLineageUpdates']==28000+vocabulary['selectedPilotStep']
 initial=torch.load(candidate/'checkpoint-0.pt',map_location='cpu',weights_only=False);assert initial['step']==0 and not initial['optimizer']['state'] and initial['seen_tokens']==initial['seen_bytes']==0
 baseline=ROOT/'main-initial-0';snapshot=read(baseline/'snapshot.json');assert snapshot['checkpointSha256']==sha(candidate/'checkpoint-0.pt') and snapshot['parentSelectedWeightLineageUpdates']==r['parentSelectedWeightLineageUpdates']
 assert snapshot['gzipModelSha256']==sha(baseline/'model.js.gz') and snapshot['plainModelSha256']==hashlib.sha256(gzip.decompress((baseline/'model.js.gz').read_bytes())).hexdigest()
 choice=read(ROOT/'checkpoint-choice.json');assert choice['modelSha256']==sha(candidate/'model.js') and choice['selectedMainUpdates']==r['bestStep'] and choice['vocabularyChoiceSha256']==sha(ROOT/'vocabulary-choice.json') and not choice['testUsed']
 results={};performance={}
 for folder in [baseline,candidate]:
  g=read(folder/'validation.json');review=read(folder/'validation-review.json');js=read(folder/'validation-js.json');manual=read(folder/'validation-manual.json')
  assert g['partition']=='validation' and len(g['rows'])==17 and g['maxNewTokens']==192 and g['policySha256']==sha(ROOT/'generation-policy.json')
  assert review['generationSha256']==manual['generationSha256']==sha(folder/'validation.json') and manual['meaningPolicySha256']==review['meaningPolicySha256']==sha(ROOT/'full-meaning-policy.json')
  assert js['modelSha256']==g['modelFileSha256'] and all(ref['maxAbsoluteError']<=2e-4 for ref in js['references'])
  mismatches=[]
  for a,b,c in zip(g['rows'],review['rows'],js['rows'],strict=True):
   keys=['id','text','tokens','eos','validUtf8','validTokens','inputTokens']
   for key in keys:assert a[key]==b[key]
   if any(a[key]!=c[key] for key in keys):mismatches.append(a['id'])
  assert js['completeGenerationParity']==(not mismatches)
  if mismatches:
   divergence=read(ROOT/'numerical-divergence.json');assert divergence['modelSha256']==sha(candidate/'model.js') and divergence['traceSha256']==sha(candidate/'divergence-python.json');assert mismatches==[x['id'] for x in divergence['rows']]
   assert divergence['noOutputRepair'] and divergence['noWeightChange'] and all(x['argmaxChoicesReproduced'] and x['referenceTolerancePassed'] for x in divergence['rows'])
  assert set(review['scopes'])=={'expanded17','parent13','original9'} and review['gatePassed']==review['naturalLanguageEstablished']==all(s['gatePassed'] for s in review['scopes'].values())
  results[folder.name]={k:review[k] for k in ['total','passed','fullOutputNonLoop','fullOutputMeaningful','validTokenOutputs','scopes','gatePassed','naturalLanguageEstablished']}
  results[folder.name].update(completeGreedySequenceParity=js['completeGenerationParity'],matchingRawSequences=17-len(mismatches),referenceLogitTolerancePassed=True)
  performance[folder.name]=dict(generatedTokens=sum(len(x['tokens']) for x in g['rows']),generatedCharacters=sum(len(x['text']) for x in g['rows']),pythonGenerationSeconds=sum(x['elapsedSeconds'] for x in g['rows']),javascriptGenerationMs=sum(x['elapsedMs'] for x in js['rows']),generationSha256=sha(folder/'validation.json'),javascriptSha256=sha(folder/'validation-js.json'))
 pause=read(ROOT/'pause-record-2150.json');resumed=read(ROOT/'resume-2150-verification.json')
 assert pause['confirmedMainUpdates']==resumed['confirmedUpdatesBeforeResume']==2150 and pause['checkpointSha256']==resumed['checkpointSha256']
 assert resumed['optimizerCounters']==[2150] and pause['noDiscardedUpdates'] and resumed['sourceIdentityVerified']
 assert pause['logSha256']==sha(ROOT/pause['logPath']) and pause['trainerSourceSha256']==r['trainerSourceSha256']
 assert not list(ROOT.glob('*/test.json'))
 for manifest in ['source-manifest.json','pilot-manifest.json']:
  for f in read(ROOT/manifest)['files']:assert sha(ROOT/f['path'])==f['sha256']
 for name,manifestname in [('round8','reproducibility-manifest.json'),('round9-source','source-manifest.json')]:
  parent=ROOT.parent/name
  for f in read(parent/manifestname)['files']:assert sha(parent/f['path'])==f['sha256']
 write(ROOT/'optimizer-audit.json',dict(pilots=pilots,main=mainrun,actualCompletedPilotUpdates=2000,actualCompletedMainUpdates=10000,actualCompletedUpdatesThisRound=12000,round3OnwardConfirmedCompletedUpdates=56000,round3OnwardPhysicalUpdatesLowerBound=56100,priorObservedDiscardedUpdates=100,unloggedPriorDiscardedUpdatesUnknown=True,selectedWeightLineageUpdates=r['parentSelectedWeightLineageUpdates']+r['bestStep'],countsDescribeCompletedBranchesNotWholeLifetime=True,ownParentOnly=True,externalWeights=False,externalTokenizer=False,externalInferenceAPI=False,fullPrecisionWeightsAndOptimizer=True,pythonAndTorchRngSaved=True))
 write(ROOT/'comparison.json',dict(runs=results,naturalLanguageEstablished=results[candidate.name]['naturalLanguageEstablished'],languageGatePassed=results[candidate.name]['gatePassed'],testStillUnopened=True,publicModelReplaced=False,completeGreedySequenceParity=all(x['completeGreedySequenceParity'] for x in results.values()),numericalDivergenceSha256=sha(ROOT/'numerical-divergence.json'),note='Main0 baseline includes the selected own pilot learning. Same vocabulary/corpus/model compared before versus after actual10000 main updates. Old round8 differs in vocabulary/corpus/sampling: no single-factor causal claim. Sentence/nonloop and whole-meaning gates required at all17, parent13 and original9 scopes.'))
 write(ROOT/'performance.json',dict(runs=performance,note='Recorded CPU raw generation timings, not controlled browser or cross-vocabulary benchmarks. Loading excluded; token/character counts and EOS differ.'))
 print(json.dumps(dict(actualCompletedUpdatesThisRound=12000,selectedWeightLineageUpdates=r['parentSelectedWeightLineageUpdates']+r['bestStep'],naturalLanguageEstablished=results[candidate.name]['naturalLanguageEstablished'])))
if __name__=='__main__':main()
