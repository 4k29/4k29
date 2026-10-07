"""Bind completed own continuation, outputs, judgments and reproducibility."""
import gzip,hashlib,json,pathlib,platform,sys
import torch,numpy as np
ROOT=pathlib.Path(__file__).resolve().parent;PARENT=ROOT.parent/'round3'
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    torch.set_num_threads(1);directory=ROOT/'boundary-focus-2000';result=read(directory/'result.json');metrics=read(directory/'metrics.json')
    saved=torch.load(directory/'checkpoint.pt',map_location='cpu',weights_only=False);states=saved['optimizer']['state']
    assert saved['step']==result['completedSteps']==result['requestedSteps']==2000 and result['completedRun']
    assert sorted({int(s['step']) for s in states.values()})==[2000]
    assert result['checkpointSha256']==sha(directory/'checkpoint.pt')
    assert saved['beststep']==result['bestStep']==metrics['bestStep']
    assert min(r['validation']['nllPerUtf8Byte'] for r in metrics['history'])==metrics['bestValidationNllPerByte']
    assert result['trainerSourceSha256']==sha(ROOT/'train.py') and result['batchingSourceSha256']==sha(ROOT/'batching.py')
    assert result['boundaryDataSha256']==sha(ROOT/'boundary-bpe-8192/data.json')
    assert result['rawUnitsSha256']==sha(PARENT/'units.json')
    assert result['parentCheckpointSha256']==sha(PARENT/'raw-chains-10000/checkpoint.pt')
    assert result['ownParentOnly'] and result['ownRandomInitializedLineage'] and result['optimizerReset'] and result['seedReset']
    assert not any(result[k] for k in ['externalWeights','externalTokenizer','externalInferenceAPI'])
    assert all(t.dtype==torch.float32 for k in ['model','beststate'] for t in saved[k].values())
    assert all(s[k].dtype==torch.float32 for s in states.values() for k in ['exp_avg','exp_avg_sq'])
    assert isinstance(saved['pythonRng'],tuple) and saved['torchRng'].dtype==torch.uint8
    parameters=sum(t.numel() for t in saved['model'].values());assert parameters==result['parameters'];del saved
    choice=read(ROOT/'checkpoint-choice.json');assert not choice['testUsed']
    assert choice['modelSha256']==sha(directory/'model.js') and choice['policySha256']==sha(ROOT/'generation-policy.json')
    assert choice['selectedUpdates']==result['bestStep']
    primary=read(directory/'validation.json');review=read(directory/'validation-review.json')
    for name in ['boundary-focus-2000','terminal-2000']:
        d=ROOT/name;g=read(d/'validation.json');r=read(d/'validation-review.json');js=read(d/'validation-js.json')
        assert len(g['rows'])==9 and g['partition']=='validation'
        assert r['generationSha256']==sha(d/'validation.json') and not r['independentHumanEvaluation']
        assert js['completeGenerationParity'] and js['modelSha256']==g['modelFileSha256']
        assert all(x['maxAbsoluteError']<=2e-4 for x in js['references'])
        for original,judged,other in zip(g['rows'],r['rows'],js['rows'],strict=True):
            for k in ['id','text','tokens','eos','validUtf8','validTokens','inputTokens']:assert original[k]==judged[k]==other[k]
    terminal=read(ROOT/'terminal-2000/snapshot.json')
    assert not terminal['additionalUpdates'] and terminal['actualTerminalUpdates']==2000
    assert terminal['checkpointSha256']==result['checkpointSha256']
    assert terminal['gzipModelSha256']==sha(ROOT/'terminal-2000/model.js.gz')
    assert terminal['plainModelSha256']==hashlib.sha256(gzip.decompress((ROOT/'terminal-2000/model.js.gz').read_bytes())).hexdigest()
    assert not list(ROOT.glob('*/test.json')) and not list(PARENT.glob('*/test.json'))
    old=read(PARENT/'reproducibility-manifest.json')
    for f in old['files']:assert sha(PARENT/f['path'])==f['sha256'],f['path']
    write(ROOT/'optimizer-audit.json',dict(actualAdditionalOptimizerUpdates=2000,optimizerStepCounters=[2000],optimizerStateTensors=len(states),fullPrecisionWeightsAndOptimizer=True,pythonAndTorchRngSaved=True,parentCompletedUpdates=result['parentCompletedSteps'],parentSelectedUpdates=result['parentSelectedSteps'],childSelectedUpdates=result['bestStep'],selectedWeightLineageUpdates=result['parentSelectedSteps']+result['bestStep'],parameters=parameters,checkpointSha256=result['checkpointSha256'],modelSha256=sha(directory/'model.js'),diagnosticTerminalAddsUpdates=False,priorRoundFilesVerified=len(old['files'])))
    baseline=read(PARENT/'raw-chains-10000/validation-review.json')
    write(ROOT/'comparison.json',dict(partition='validation',baseline=dict(run='round3/raw-chains-10000',passed=baseline['passed'],total=9,groups=baseline['groups'],generationSha256=sha(PARENT/'raw-chains-10000/validation.json')),candidate=dict(run=directory.name,passed=review['passed'],total=9,groups=review['groups'],validTokenOutputs=review['validTokenOutputs'],generationSha256=sha(directory/'validation.json')),languageGatePassed=review['gatePassed'],testStillUnopened=True,publicModelReplaced=False,terminalDiagnosticSameWeightsAsSelected=result['bestStep']==2000,note='Development-only same-fold comparison. A marginal first-sentence gain does not establish full-output stability or broad conversation. Additional training, label distribution, optimizer and seed differ.'))
    from report_results import main as report
    report()
    manifest=ROOT/'reproducibility-manifest.json'
    files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(ROOT.rglob('*')) if p.is_file() and p!=manifest and '__pycache__' not in p.parts and p.suffix!='.tmp']
    assert all(f['bytes']<100*1024*1024 for f in files)
    shared=[ROOT.parent/'model.py',ROOT.parent/'evaluate_js.mjs']+[ROOT.parents[1]/'dialogue'/n for n in ['tokenizer.py','tokenizer.mjs','bpe_heap.mjs','beam_search.mjs','inference.mjs']]
    write(manifest,dict(files=files,sharedFiles=[dict(path=str(p.relative_to(ROOT.parents[2])),sha256=sha(p)) for p in shared],priorRoundFilesVerified=len(old['files']),priorRoundManifestSha256=sha(PARENT/'reproducibility-manifest.json'),python=sys.version,torch=torch.__version__,numpy=np.__version__,platform=platform.platform(),externalWeights=False,externalTokenizer=False,externalInferenceAPI=False,testStillUnopened=True,languageGatePassed=review['gatePassed']))
    print(json.dumps(dict(actualAdditionalUpdates=2000,selectedLineageUpdates=result['parentSelectedSteps']+result['bestStep'],files=len(files),sentencePassed=review['passed'],languageGatePassed=review['gatePassed'],testStillUnopened=True)))
if __name__=='__main__':main()
