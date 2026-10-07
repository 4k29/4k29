"""Verify completed runs and development judgments without opening TEST."""
import gzip,hashlib,json,pathlib,platform,sys
import numpy as np
import torch
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    torch.set_num_threads(1);runs=[]
    for name,trainer in [('pilot-4096','train.py'),('pilot-8192','train.py'),('raw-chains-10000','main_train.py')]:
        directory=ROOT/name;result=read(directory/'result.json');metrics=read(directory/'metrics.json')
        saved=torch.load(directory/'checkpoint.pt',map_location='cpu',weights_only=False)
        states=saved['optimizer']['state'];counts=sorted({int(s['step']) for s in states.values()})
        assert counts==[saved['step']]==[result['completedSteps']]
        assert result['completedRun'] and result['completedSteps']==result['requestedSteps']
        assert result['checkpointSha256']==sha(directory/'checkpoint.pt')
        assert saved['settings']['trainerSourceSha256']==sha(ROOT/trainer)
        assert saved['settings']['rawUnitsSha256']==sha(ROOT/'units.json')
        assert saved['settings']['sourceSha256']==sha(ROOT/'documents.jsonl')
        assert saved['settings']['splitSha256']==sha(ROOT/'split.json')
        assert saved['settings']['tokenizerSha256']==sha(ROOT/f"raw-bpe-{result['merges']}/tokenizer.json")
        assert saved['beststep']==result['bestStep']==metrics['bestStep']
        assert min(r['validation']['nllPerUtf8Byte'] for r in metrics['history'])==metrics['bestValidationNllPerByte']
        assert all(t.dtype==torch.float32 for field in ['model','beststate'] for t in saved[field].values())
        assert all(s[k].dtype==torch.float32 for s in states.values() for k in ['exp_avg','exp_avg_sq'])
        assert isinstance(saved['pythonRng'],tuple) and saved['torchRng'].dtype==torch.uint8
        assert result['randomInitialization'] and result['previousWeightsNotAllowed']
        assert not any(result[k] for k in ['externalWeights','externalTokenizer','externalInferenceAPI'])
        parameters=sum(t.numel() for t in saved['model'].values());assert parameters==result['parameters']
        runs.append(dict(run=name,completedOptimizerUpdates=saved['step'],selectedStep=saved['beststep'],optimizerStepCounters=counts,optimizerStateTensors=len(states),parameters=parameters,fullPrecisionWeightsAndOptimizer=True,pythonAndTorchRngSaved=True,checkpointSha256=sha(directory/'checkpoint.pt'),modelSha256=sha(directory/'model.js'),trainerSha256=sha(ROOT/trainer),bestCanonicalValidationNllPerUtf8Byte=metrics['bestValidationNllPerByte']))
        del saved
    snapshot=read(ROOT/'baseline-1000/snapshot.json')
    assert snapshot['actualOptimizerUpdates']==1000 and not snapshot['additionalUpdates']
    assert snapshot['checkpointSha256']==sha(ROOT/'raw-chains-10000/checkpoint-1000.pt')
    packed=ROOT/'baseline-1000/model.js.gz'
    assert snapshot['gzipModelSha256']==sha(packed)
    assert snapshot['plainModelSha256']==hashlib.sha256(gzip.decompress(packed.read_bytes())).hexdigest()
    diagnostic=read(ROOT/'midpoint-validation-diagnostic.json');middle=read(ROOT/'midpoint-diagnostic-review.json')
    assert diagnostic['checkpointCompletedUpdates']==5000 and diagnostic['selectedStep']==5000
    assert diagnostic['reproducedWithRetainedFullPrecisionState'] and diagnostic['notFinalWeightSelection']
    assert diagnostic['retainedWeightsSha256']==sha(ROOT/diagnostic['retainedFullPrecisionWeights'])
    assert diagnostic['reproductionScriptSha256']==sha(ROOT/diagnostic['reproductionScript'])
    assert middle['generationSha256']==sha(ROOT/'midpoint-validation-diagnostic.json')
    state=torch.load(ROOT/diagnostic['retainedFullPrecisionWeights'],map_location='cpu',weights_only=False)
    assert state['diagnosticOnly'] and state['optimizerNotIncluded']
    assert state['step']==5000 and state['sourceCheckpointSha256']==diagnostic['checkpointSha256']
    assert all(t.dtype==torch.float32 for t in state['beststate'].values());del state
    chosen=read(ROOT/'checkpoint-choice.json');assert not chosen['testUsed']
    assert chosen['modelSha256']==sha(ROOT/'raw-chains-10000/model.js')
    assert chosen['policySha256']==sha(ROOT/'generation-policy.json')
    reviews=[]
    for name in ['raw-chains-10000','baseline-1000']:
        directory=ROOT/name;generation=read(directory/'validation.json');review=read(directory/'validation-review.json');js=read(directory/'validation-js.json')
        assert generation['partition']=='validation' and len(generation['rows'])==9
        assert review['generationSha256']==sha(directory/'validation.json')
        assert js['completeGenerationParity'] and js['modelSha256']==generation['modelFileSha256']
        assert all(r['maxAbsoluteError']<=2e-4 for r in js['references'])
        for raw,judged,other in zip(generation['rows'],review['rows'],js['rows'],strict=True):
            for key in ['id','text','tokens','eos','validUtf8','validTokens','inputTokens']:
                assert raw[key]==judged[key]==other[key]
        reviews.append(dict(run=name,passed=review['passed'],total=review['total'],groups=review['groups'],gatePassed=review['gatePassed'],generationSha256=sha(directory/'validation.json'),reviewSha256=sha(directory/'validation-review.json')))
    test_open=bool(list(ROOT.glob('*/test.json')))
    assert not test_open,'This audit records development-only evaluation; use a separate TEST audit after gate acceptance'
    prior=[]
    for base in [ROOT.parent,ROOT.parent/'round2']:
        inventory=read(base/'reproducibility-manifest.json')
        for f in inventory['files']:assert sha(base/f['path'])==f['sha256'],f['path']
        prior.append(dict(root=str(base.relative_to(ROOT.parents[2])),verifiedFiles=len(inventory['files']),manifestSha256=sha(base/'reproducibility-manifest.json')))
    write(ROOT/'optimizer-audit.json',dict(runs=runs,totalCompletedCleanRawUpdates=sum(r['completedOptimizerUpdates'] for r in runs),mainRunUpdates=runs[-1]['completedOptimizerUpdates'],diagnosticSnapshotAddsUpdates=False,midpointDiagnosticAddsUpdates=False,midpointWeightsOnlyNotResumable=True,unknownUnsavedUpdatesNotCounted=True,priorInventories=prior))
    write(ROOT/'comparison.json',dict(partition='validation',baseline=reviews[1],candidate=reviews[0],testStillUnopened=True,publicModelReplaced=False,languageGatePassed=reviews[0]['gatePassed'],independentHumanEvaluation=False,note='Same new fold, tokenizer and architecture. Development evaluation only; generated outputs do not train/select weights. Language judgments do not verify factual claims.'))
    from report_results import main as write_report
    write_report()
    manifest=ROOT/'reproducibility-manifest.json'
    files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(ROOT.rglob('*')) if p.is_file() and p!=manifest and '__pycache__' not in p.parts and p.suffix!='.tmp']
    assert all(f['bytes']<100*1024*1024 for f in files)
    shared=[ROOT.parent/'model.py',ROOT.parent/'evaluate_js.mjs']+[ROOT.parents[1]/'dialogue'/n for n in ['tokenizer.py','tokenizer.mjs','bpe_heap.mjs','beam_search.mjs','inference.mjs']]
    write(manifest,dict(files=files,sharedFiles=[dict(path=str(p.relative_to(ROOT.parents[2])),sha256=sha(p)) for p in shared],priorInventories=prior,python=sys.version,torch=torch.__version__,numpy=np.__version__,platform=platform.platform(),cudaAvailable=torch.cuda.is_available(),externalWeights=False,externalTokenizer=False,externalInferenceAPI=False,testStillUnopened=True,languageGatePassed=reviews[0]['gatePassed']))
    print(json.dumps(dict(completedUpdates=sum(r['completedOptimizerUpdates'] for r in runs),files=len(files),testStillUnopened=True,languageGatePassed=reviews[0]['gatePassed'])))
if __name__=='__main__':main()
