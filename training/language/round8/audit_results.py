"""Audit actual optimizer updates, fixed inputs and unedited VAL comparisons."""
import gzip,hashlib,json,pathlib,sys
import torch
ROOT=pathlib.Path(__file__).resolve().parent
PARENT=ROOT.parent/'round6'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 torch.set_num_threads(1);d=ROOT/'expanded-characters-10000';r=read(d/'result.json');m=read(d/'metrics.json');cp=torch.load(d/'checkpoint.pt',map_location='cpu',weights_only=False)
 assert r['completedRun'] and r['completedSteps']==r['requestedSteps']==cp['step']==10000
 assert r['ownParentOnly'] and r['ownRandomInitializedLineage'] and r['optimizerReset'] and not r['randomInitialization'] and r['wordMerges']==0
 assert r['parameters']==4537728 and cp['config']['layers']==8 and cp['config']['vocabulary']==4840
 assert r['parentSelectedChildSteps']==8000 and r['parentSelectedWeightLineageUpdates']==18000
 assert r['parentCheckpointSha256']==sha(PARENT/'character-continue-10000/checkpoint.pt') and r['parentTrainerSha256']==sha(PARENT/'train.py')
 assert not any(r[k] for k in ['externalWeights','externalTokenizer','externalInferenceAPI'])
 counts=sorted({int(s['step']) for s in cp['optimizer']['state'].values()});assert counts==[10000]
 assert all(t.dtype==torch.float32 for k in ['model','beststate'] for t in cp[k].values())
 assert all(s[k].dtype==torch.float32 for s in cp['optimizer']['state'].values() for k in ['exp_avg','exp_avg_sq'])
 assert isinstance(cp['pythonRng'],tuple) and cp['torchRng'].dtype==torch.uint8
 assert cp['beststep']==r['bestStep']==m['bestStep'] and cp['bestloss']==min(x['validation']['nllPerUtf8Byte'] for x in m['history'])
 assert r['checkpointSha256']==sha(d/'checkpoint.pt')
 for field,file in [('trainerSourceSha256','train.py'),('batchingSourceSha256','batching.py'),('initializationSourceSha256','initialization.py'),('experimentPolicySha256','experiment-policy.json'),('characterFrequenciesSha256','character-frequencies.json'),('preparedDataSha256','unicode-bpe-4578/data.json'),('rawUnitsSha256','units.json'),('sourceSha256','documents.jsonl'),('splitSha256','split.json'),('tokenizerSha256','unicode-bpe-4578/tokenizer.json')]:assert r[field]==sha(ROOT/file),field
 del cp
 recovery=read(ROOT/'recovery.json');assert sha(ROOT/recovery['priorLogPath'])==recovery['priorLogSha256']
 restored=torch.load(ROOT/recovery['resumeCheckpointPath'],map_location='cpu',weights_only=False)
 assert sha(ROOT/recovery['resumeCheckpointPath'])==recovery['resumeCheckpointSha256'] and restored['step']==7000
 assert sorted({int(s['step']) for s in restored['optimizer']['state'].values()})==[7000]
 assert recovery['lastLoggedUpdatesBeforeReset']-restored['step']==recovery['observedDiscardedUpdates']==100
 for key,value in restored['settings'].items():assert r[key]==value,key
 del restored
 initial=torch.load(d/'checkpoint-0.pt',map_location='cpu',weights_only=False)
 assert initial['step']==0 and not initial['optimizer']['state'] and initial['seen_tokens']==initial['seen_bytes']==0
 for key,value in initial['settings'].items():assert r[key]==value,key
 snap=read(ROOT/'initial-0/snapshot.json');assert snap['completedUpdates']==0 and snap['optimizerCounters']==[] and not snap['additionalUpdates']
 assert snap['checkpointSha256']==sha(d/'checkpoint-0.pt') and snap['parentSelectedWeightLineageUpdates']==18000
 packed=ROOT/'initial-0/model.js.gz';assert snap['gzipModelSha256']==sha(packed) and snap['plainModelSha256']==hashlib.sha256(gzip.decompress(packed.read_bytes())).hexdigest()
 del initial
 choice=read(ROOT/'checkpoint-choice.json');assert not choice['testUsed'] and choice['actualChildUpdates']==10000 and choice['selectedChildUpdates']==r['bestStep']
 assert choice['modelSha256']==sha(d/'model.js') and choice['baselineModelSha256']==snap['plainModelSha256'] and choice['selectedWeightLineageUpdates']==18000+r['bestStep']
 assert choice['policySha256']==sha(ROOT/'generation-policy.json') and choice['experimentPolicySha256']==r['experimentPolicySha256']
 results={};performance={};full_meaning={};meaning_policy=read(ROOT/'full-meaning-policy.json')
 for name in ['initial-0','expanded-characters-10000']:
  folder=ROOT/name;g=read(folder/'validation.json');v=read(folder/'validation-review.json');js=read(folder/'validation-js.json')
  assert g['partition']=='validation' and g['maxNewTokens']==192 and len(g['rows'])==13 and v['coreTotal']==9
  assert g['policySha256']==sha(ROOT/'generation-policy.json') and v['generationSha256']==sha(folder/'validation.json') and not v['independentHumanEvaluation']
  assert js['completeGenerationParity'] and js['modelSha256']==g['modelFileSha256']
  assert all(ref['maxAbsoluteError']<=2e-4 for ref in js['references'])
  for a,b,c in zip(g['rows'],v['rows'],js['rows'],strict=True):
   for k in ['id','text','tokens','eos','validUtf8','validTokens','inputTokens']:assert a[k]==b[k]==c[k]
  assert v['gatePassed']==all(x['gatePassed'] for x in list(v['groups'].values())+list(v['coreGroups'].values()))
  judgments=read(folder/'validation-manual.json');assert judgments['fullMeaningPolicySha256']==sha(ROOT/'full-meaning-policy.json');assert all(isinstance(x['fullOutputMeaningful'],bool) for x in judgments['rows'])
  full_j={x['id']:x['fullOutputMeaningful'] for x in judgments['rows']};assert set(full_j)=={x['id'] for x in g['rows']}
  full_meaning[name]={}
  core_ids={x['id'] for x in read(ROOT.parent/'round6/generation-policy.json')['probes']['validation']}
  for scope in ['expanded13','original9']:
   chosen=[x for x in g['rows'] if scope=='expanded13' or x['id'] in core_ids]
   for genre in ['narrative','contemporary-expository']:
    subset=[x for x in chosen if (x['site']=='aozora')==(genre=='narrative')];passed=sum(full_j[x['id']] and x['validTokens'] for x in subset)
    full_meaning[name][scope+'/'+genre]=dict(total=len(subset),fullMeaningful=passed,rate=passed/len(subset),criterionPassed=passed/len(subset)>=meaning_policy['minimumMeaningfulFullOutputRate'])
  results[name]=dict(passed=v['passed'],total=v['total'],corePassed=v['corePassed'],coreTotal=v['coreTotal'],validTokenOutputs=v['validTokenOutputs'],groups=v['groups'],coreGroups=v['coreGroups'],gatePassed=v['gatePassed'],generationSha256=sha(folder/'validation.json'))
  performance[name]=dict(generatedTokenIds=sum(len(x['tokens']) for x in g['rows']),generatedUnicodeCharacters=sum(len(x['text']) for x in g['rows']),pythonGenerationSeconds=sum(x['elapsedSeconds'] for x in g['rows']),javascriptGenerationMs=sum(x['elapsedMs'] for x in js['rows']),generationSha256=sha(folder/'validation.json'),javascriptParitySha256=sha(folder/'validation-js.json'))
 assert not list(ROOT.glob('*/test.json'))
 previous={}
 for phase in ['round3','round4','round5','round6','round7','round9-source']:
  base=ROOT.parent/phase;file=base/('source-manifest.json' if phase in ['round7','round9-source'] else 'reproducibility-manifest.json');manifest=read(file)
  for f in manifest['files']:assert sha(base/f['path'])==f['sha256'],phase+'/'+f['path']
  for f in manifest.get('sharedFiles',[]):assert sha(ROOT.parents[2]/f['path'])==f['sha256'],f['path']
  previous[phase]=dict(files=len(manifest['files']),manifestSha256=sha(file),manifestName=file.name)
 for f in read(ROOT/'source-manifest.json')['files']:assert sha(ROOT/f['path'])==f['sha256'],f['path']
 write(ROOT/'optimizer-audit.json',dict(actualAdditionalOptimizerUpdates=10000,actualUpdateCountScope='Confirmed completed checkpoint branch; discarded interrupted updates recorded separately',observedDiscardedUpdates=recovery['observedDiscardedUpdates'],physicalAdditionalUpdatesLowerBound=10000+recovery['observedDiscardedUpdates'],unloggedDiscardedUpdatesUnknown=True,recoveryRecordSha256=sha(ROOT/'recovery.json'),optimizerStepCounters=counts,parentCompletedUpdates=10000,parentSelectedChildUpdates=8000,parentSelectedWeightLineageUpdates=18000,selectedChildUpdates=r['bestStep'],selectedWeightLineageUpdates=18000+r['bestStep'],round3OnwardConfirmedCompletedUpdates=44000,round3OnwardPhysicalUpdatesLowerBound=44100,parameters=r['parameters'],fullPrecisionWeightsAndOptimizer=True,pythonAndTorchRngSaved=True,ownParentOnly=True,ownRandomInitializedLineage=True,baselineActualUpdates=0,baselineAddsUpdates=False,checkpointSha256=r['checkpointSha256'],previousInventoriesVerified=previous))
 write(ROOT/'comparison.json',dict(partition='validation',runs=results,languageGatePassed=results['expanded-characters-10000']['gatePassed'],fullMeaningAssessment=full_meaning,fullMeaningPolicySha256=sha(ROOT/'full-meaning-policy.json'),naturalLanguageEstablished=results['expanded-characters-10000']['gatePassed'] and all(x['criterionPassed'] for x in full_meaning['expanded-characters-10000'].values()),testStillUnopened=True,publicModelReplaced=False,note='Same expanded8-layer character model at initialization0 versus VAL-selected after actual10000. Historical4-layer model differs in architecture, corpus and vocabulary; no single-factor causal claim. Both original9 and expanded13 group gates must pass; first-sentence/nonloop scores do not certify full meaning or factual accuracy.'))
 write(ROOT/'performance.json',dict(runs=performance,contextLimit=256,maxNewTokens=192,parameters=r['parameters'],device='CPU',trainingThreads=2,pythonEvaluationThreads=1,note='Raw generation timings excluding loading; not a controlled browser latency benchmark. Content/EOS can change work; repeated timing trials were not run.'))
 print(json.dumps(dict(actualAdditionalOptimizerUpdates=10000,selectedChildUpdates=r['bestStep'],results=results)))
if __name__=='__main__':main()
