"""Audit real full-precision optimizer counters and final reproducibility files."""
import gzip,hashlib,json,pathlib,sys
import torch
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def write(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
    torch.set_num_threads(1);runs=[]
    for name,trainer in [('pilot-4096','pilot-trainer.py'),('pilot-8192','pilot-trainer.py'),('raw-modern-million','train.py'),('prefix-million','train_prefix.py')]:
        run=ROOT/name;cp=run/'checkpoint.pt';result=read(run/'result.json');metrics=read(run/'metrics.json');saved=torch.load(cp,map_location='cpu',weights_only=False)
        step=saved['step'];states=saved['optimizer']['state'];counts=sorted({int(s['step']) for s in states.values()})
        assert counts==[step];assert step==result['completedSteps']==result['requestedSteps']
        assert result['completedRun'];assert sha(cp)==result['checkpointSha256']
        assert saved['beststep']==result['bestStep']==metrics['bestStep']
        assert min(r['validation']['nllPerUtf8Byte'] for r in metrics['history'])==metrics['bestValidationNllPerByte']
        if 'trainerSourceSha256' in saved['settings']:
            assert saved['settings']['trainerSourceSha256']==sha(ROOT/trainer)
        parameters=sum(t.numel() for t in saved['model'].values())
        assert parameters==result['parameters'];assert all(t.dtype==torch.float32 for t in saved['model'].values())
        assert all(t.dtype==torch.float32 for t in saved['beststate'].values())
        assert all(s[k].dtype==torch.float32 for s in states.values() for k in ['exp_avg','exp_avg_sq'])
        assert isinstance(saved['pythonRng'],tuple) and saved['torchRng'].dtype==torch.uint8
        runs.append(dict(run=name,completedOptimizerUpdates=step,selectedStep=saved['beststep'],optimizerStateTensors=len(states),optimizerStepCounters=counts,parameters=parameters,fullPrecisionWeightsAndOptimizer=True,pythonAndTorchRngSaved=True,checkpointSha256=sha(cp),modelSha256=sha(run/'model.js'),trainerSha256=sha(ROOT/trainer),trainerHashSavedAtRunTime='trainerSourceSha256' in saved['settings'],bestCanonicalValidationNllPerUtf8Byte=metrics['bestValidationNllPerByte']))
        del saved
    child=read(ROOT/'prefix-million/result.json');parent=runs[2]
    assert child['parentCheckpointSha256']==parent['checkpointSha256'];assert child['parentSelectedSteps']==parent['selectedStep']
    diagnostics=[]
    for name in ['validation-5000','prefix-validation-5000']:
        directory=ROOT/name;snapshot=read(directory/'snapshot.json');report=read(directory/'review.json');packed=directory/'model.js.gz';js=read(directory/'validation-js.json')
        assert snapshot['actualSavedUpdates']==5000 and snapshot['optimizerStepCounters']==[5000]
        assert not snapshot['completedRequestedRun']
        assert snapshot['compressedModelSha256']==sha(packed)
        assert snapshot['uncompressedModelSha256']==hashlib.sha256(gzip.decompress(packed.read_bytes())).hexdigest()
        assert js['completeGenerationParity'];assert report['generationSha256']==sha(directory/'validation.json')
        diagnostics.append(dict(directory=name,actualRunUpdates=5000,selectedStep=snapshot['selectedStep'],parentSelectedSteps=snapshot['training'].get('parentSelectedSteps',0),firstSentencePassed=report['passed'],total=report['total'],gatePassed=report['gatePassed'],snapshotSha256=sha(directory/'snapshot.json'),note='Intermediate subset of the run, not additional optimizer updates. Frozen exporter family name may match other diagnostics; identity is bound by SHA and training.run.'))
    write(ROOT/'optimizer-audit.json',dict(runs=runs,diagnostics=diagnostics,totalCompletedCleanRawUpdates=sum(r['completedOptimizerUpdates'] for r in runs),discardedPrecisionTimingUpdates=60,selectedChildWeightLineageUpdates=child['parentSelectedSteps']+child['bestStep'],optimizerResetBeforeChild=True,note='Pilots are separate random initializations, not part of the six-layer weight lineage. Checkpoint optimizer/RNG describe the final update; exported weights describe the separately selected beststate. No interrupted attempts without updates are counted. Pilots did not save trainer SHA at run time; their exact source copy is retained, with its SHA recorded retrospectively.'))
    old=read(ROOT.parent/'reproducibility-manifest.json')
    for f in old['files']:assert sha(ROOT.parent/f['path'])==f['sha256'],f['path']
    choice=read(ROOT/'checkpoint-choice.json');selected=ROOT/choice['chosenRun'];current=read(selected/'review-test.json');baseline=read(ROOT/'baseline/test-review.json')
    for directory,report,generation,js in [(selected,'review-test.json','test.json','test-js.json'),(ROOT/'baseline','test-review.json','test.json','test-js.json')]:
        g=read(directory/generation);r=read(directory/report);j=read(directory/js)
        assert r['generationSha256']==sha(directory/generation);assert len(g['rows'])==24
        assert j['completeGenerationParity'];assert all(x['maxAbsoluteError']<=2e-4 for x in j['references'])
        assert j['modelSha256']==g['modelFileSha256']
    write(ROOT/'comparison.json',dict(policySha256=sha(ROOT/'generation-policy.json'),checkpointChoiceSha256=sha(ROOT/'checkpoint-choice.json'),sameFreshOpenings=True,baseline=dict(model='../paragraph-million/model.js',sha256=sha(ROOT.parent/'paragraph-million/model.js'),reportSha256=sha(ROOT/'baseline/test-review.json'),passed=baseline['passed'],total=baseline['total'],groups=baseline['groups']),candidate=dict(run=choice['chosenRun'],reportSha256=sha(selected/'review-test.json'),passed=current['passed'],total=current['total'],groups=current['groups'],gatePassed=current['gatePassed']),independentHumanEvaluation=False,testNowConsumed=True,publicModelReplaced=False,note='Same fixed fresh raw openings, greedy decoding and strict language rubric. Neither TEST outputs nor manual reviews select or train weights. Model, tokenizer, training data and updates all differ, so this is not a one-factor causal experiment.'))
    manifest=ROOT/'reproducibility-manifest.json'
    files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(ROOT.rglob('*')) if p.is_file() and p!=manifest and '__pycache__' not in p.parts]
    assert all(f['bytes']<100*1024*1024 for f in files),'GitHub single-file size limit'
    shared=[ROOT.parent/'model.py',ROOT.parent/'evaluate_js.mjs',ROOT.parent.parent/'dialogue/tokenizer.py',ROOT.parent.parent/'dialogue/bpe_heap.py',ROOT.parent.parent/'dialogue/inference.mjs']
    shared=[p for p in shared if p.exists()]
    write(manifest,dict(files=files,sharedFiles=[dict(path=str(p.relative_to(ROOT.parent.parent.parent)),sha256=sha(p)) for p in shared],priorFrozenFilesVerified=len(old['files']),python=sys.version,torch=torch.__version__,cudaAvailable=torch.cuda.is_available(),externalWeights=False,externalTokenizer=False,externalInferenceAPI=False,languageGatePassed=current['gatePassed'],note='Inventory only this round; previous frozen 206-file inventory is unchanged. Source credits and terms accompany source documents.'))
    print(json.dumps(dict(files=len(files),updates=sum(r['completedOptimizerUpdates'] for r in runs),gatePassed=current['gatePassed'])))
if __name__=='__main__':main()
