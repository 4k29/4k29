"""Inventory finalized own data, code, weights and evaluations without secrets.

Requires both raw experiments and all final TEST reports to have completed.
It never alters data, vocabulary, weights, generation or judgments.
"""
import hashlib,json,pathlib,platform,sys
import torch
ROOT=pathlib.Path(__file__).resolve().parent
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    runs=[]
    for name in ['pilot-2048','pilot-4096','raw-million','paragraph-million']:
        path=ROOT/name;result=read(path/'result.json');assert result['completedRun']
        assert result['checkpointSha256']==sha(path/'checkpoint.pt')
        metrics=read(path/'metrics.json');best=min(metrics['history'],key=lambda r:r['validation']['nllPerUtf8Byte'])
        assert best['step']==result['bestStep']
        row=dict(run=name,completedUpdates=result['completedSteps'],selectedStep=result['bestStep'],parameters=result['parameters'],sourceSha256=result['sourceSha256'],tokenizerSha256=result['tokenizerSha256'],seenTargetTokens=result['seenTargetTokens'],seenTargetUtf8Bytes=result['seenTargetUtf8Bytes'],initialValidation=metrics['history'][0]['validation'],selectedValidation=best['validation'],checkpointSha256=sha(path/'checkpoint.pt'),exportedModelSha256=sha(path/'model.js'))
        if name in ['raw-million','paragraph-million']:
            test=read(path/'test.json');review=read(path/'test-review.json');js=read(path/'test-js.json')
            assert test['modelFileSha256']==row['exportedModelSha256'];assert review['generationSha256']==sha(path/'test.json');assert js['completeGenerationParity']
            row.update(testLikelihood=test['likelihood'],testLikelihoodUnit=test['likelihoodUnit'],testGroups=review['groups'],languageGatePassed=review['gatePassed'],independentHumanEvaluation=False)
        if result.get('ownInitialModel'):row['ownInitialModel']=result['ownInitialModel']
        runs.append(row)
    excluded={'reproducibility-manifest.json'}
    paths=sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded and p.suffix!='.tmp')
    files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in paths]
    for name in ['tokenizer.py','tokenizer.mjs','bpe_heap.mjs','inference.mjs','switch-candidate.js']:
        p=ROOT.parent/'dialogue'/name;files.append(dict(path='../dialogue/'+name,bytes=p.stat().st_size,sha256=sha(p)))
    hardware={name:pathlib.Path('/sys/fs/cgroup/'+name).read_text().strip() for name in ['cpu.max','memory.max']}
    manifest=dict(schemaVersion=1,software=dict(python=sys.version,torch=torch.__version__,platform=platform.platform(),cudaAvailable=torch.cuda.is_available()),hardware=hardware,runs=runs,completedCurrentRawUpdates=sum(r['completedUpdates'] for r in runs),completedMillionParameterRawUpdates=sum(r['completedUpdates'] for r in runs if r['parameters']==2665728),selectedParagraphLineageUpdates=runs[-1]['ownInitialModel']['selectedParentStep']+runs[-1]['selectedStep'],uniqueCorpus=read(ROOT/'sources.json'),sourceAttribution='source-credits.json and DATA-LICENSE.md',generationPolicySha256=sha(ROOT/'generation-policy.json'),files=files,note='Update counts are actual completed optimizer steps. Selected ancestry can be shorter than total completed runs. Seen byte/token exposures include repeated samples and are not new unique prose. Abandoned extraction and discarded numerical timing updates are preserved separately and excluded from these totals. Every inference and manual judgment is retained; TEST never selects weights or trains vocabulary. Assistant scoring is not independent human assessment. The public owner model has not been replaced by these raw-language prototypes.')
    (ROOT/'reproducibility-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(files=len(files),completedCurrentRawUpdates=manifest['completedCurrentRawUpdates'],completedMillionParameterRawUpdates=manifest['completedMillionParameterRawUpdates'],selectedParagraphLineageUpdates=manifest['selectedParagraphLineageUpdates'])))
if __name__=='__main__':main()
