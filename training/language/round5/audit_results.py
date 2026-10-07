"""Audit completed own character training and unchanged prior inventories."""
import gzip, hashlib, json, pathlib, sys
import torch
ROOT = pathlib.Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text())
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()
def write(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def main():
    torch.set_num_threads(1)
    d = ROOT/'characters-10000'; r = read(d/'result.json'); m = read(d/'metrics.json')
    cp = torch.load(d/'checkpoint.pt', map_location='cpu', weights_only=False)
    assert r['completedRun'] and r['completedSteps'] == r['requestedSteps'] == cp['step'] == 10000
    assert r['randomInitialization'] and r['previousWeightsNotAllowed'] and r['wordMerges'] == 0
    assert not any(r[k] for k in ['externalWeights','externalTokenizer','externalInferenceAPI'])
    counts = sorted({int(s['step']) for s in cp['optimizer']['state'].values()}); assert counts == [10000]
    assert all(t.dtype == torch.float32 for k in ['model','beststate'] for t in cp[k].values())
    assert all(s[k].dtype == torch.float32 for s in cp['optimizer']['state'].values() for k in ['exp_avg','exp_avg_sq'])
    assert isinstance(cp['pythonRng'], tuple) and cp['torchRng'].dtype == torch.uint8
    assert cp['beststep'] == r['bestStep'] == m['bestStep']
    assert cp['bestloss'] == min(x['validation']['nllPerUtf8Byte'] for x in m['history'])
    assert r['checkpointSha256'] == sha(d/'checkpoint.pt')
    for field, p in [('trainerSourceSha256',ROOT/'train.py'),('batchingSourceSha256',ROOT/'batching.py'),('characterFrequenciesSha256',ROOT/'character-frequencies.json'),('preparedDataSha256',ROOT/'unicode-bpe-4503/data.json'),('rawUnitsSha256',ROOT.parent/'round3/units.json')]:
        assert r[field] == sha(p), field
    del cp
    snap = read(ROOT/'baseline-1000/snapshot.json')
    assert snap['actualOptimizerUpdates'] == 1000 and snap['optimizerStepCounters'] == [1000] and not snap['additionalUpdates']
    assert snap['checkpointSha256'] == sha(d/'checkpoint-1000.pt')
    packed = ROOT/'baseline-1000/model.js.gz'
    assert snap['gzipModelSha256'] == sha(packed)
    assert snap['plainModelSha256'] == hashlib.sha256(gzip.decompress(packed.read_bytes())).hexdigest()
    choice = read(ROOT/'checkpoint-choice.json'); assert not choice['testUsed']
    assert choice['modelSha256'] == sha(d/'model.js') and choice['policySha256'] == sha(ROOT/'generation-policy.json')
    assert choice['selectedStep'] == r['bestStep']
    results = {}; performance = {}
    for name in ['baseline-1000','characters-10000']:
        folder = ROOT/name; g = read(folder/'validation.json'); v = read(folder/'validation-review.json'); js = read(folder/'validation-js.json')
        assert g['partition'] == 'validation' and g['maxNewTokens'] == 192 and len(g['rows']) == 9
        assert v['generationSha256'] == sha(folder/'validation.json') and not v['independentHumanEvaluation']
        assert js['completeGenerationParity'] and js['modelSha256'] == g['modelFileSha256']
        assert all(x['maxAbsoluteError'] <= 2e-4 for x in js['references'])
        for a,b,c in zip(g['rows'],v['rows'],js['rows'],strict=True):
            for k in ['id','text','tokens','eos','validUtf8','validTokens','inputTokens']: assert a[k] == b[k] == c[k]
        results[name] = dict(passed=v['passed'],total=v['total'],validTokenOutputs=v['validTokenOutputs'],groups=v['groups'],gatePassed=v['gatePassed'],generationSha256=sha(folder/'validation.json'))
        performance[name] = dict(generatedTokenIds=sum(len(row['tokens']) for row in g['rows']),generatedUnicodeCharacters=sum(len(row['text']) for row in g['rows']),pythonGenerationSeconds=sum(row['elapsedSeconds'] for row in g['rows']),javascriptGenerationMs=sum(row['elapsedMs'] for row in js['rows']),generationSha256=sha(folder/'validation.json'),javascriptParitySha256=sha(folder/'validation-js.json'))
    assert not list(ROOT.glob('*/test.json'))
    previous = {}
    for phase in ['round3','round4']:
        base = ROOT.parent/phase; manifest = read(base/'reproducibility-manifest.json')
        for f in manifest['files']: assert sha(base/f['path']) == f['sha256'], f['path']
        previous[phase] = dict(files=len(manifest['files']),manifestSha256=sha(base/'reproducibility-manifest.json'))
    write(ROOT/'optimizer-audit.json',dict(actualOptimizerUpdates=10000,optimizerStepCounters=counts,selectedWeightLineageUpdates=r['bestStep'],parameters=r['parameters'],fullPrecisionWeightsAndOptimizer=True,pythonAndTorchRngSaved=True,randomInitialization=True,previousWeightsNotAllowed=True,baselineAddsUpdates=False,checkpointSha256=r['checkpointSha256'],previousInventoriesVerified=previous))
    write(ROOT/'comparison.json',dict(partition='validation',runs=results,languageGatePassed=results['characters-10000']['gatePassed'],testStillUnopened=True,publicModelReplaced=False,note='Same character vocabulary, architecture, raw fold and 192-token greedy policy at saved1000 versus VAL-selected weights after actual10000. Historical word models differ in architecture and output length; not a one-factor causal comparison.'))
    write(ROOT/'performance.json',dict(runs=performance,contextLimit=256,maxNewTokens=192,parameters=r['parameters'],device='CPU',trainingThreads=2,pythonEvaluationThreads=1,note='Recorded raw generation timings only, excluding model loading. This is not a controlled browser latency benchmark or a demonstration of usable answer quality. Different EOS/content may change work; repeated timing trials were not run.'))
    from report_results import main as report
    report()
    manifest = ROOT/'reproducibility-manifest.json'
    files = [dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(ROOT.rglob('*')) if p.is_file() and p != manifest and '__pycache__' not in p.parts and p.suffix != '.tmp']
    assert all(f['bytes'] < 100*1024*1024 for f in files)
    write(manifest,dict(files=files,previousInventoriesVerified=previous,python=sys.version,torch=torch.__version__,externalWeights=False,externalTokenizer=False,externalInferenceAPI=False,testStillUnopened=True,languageGatePassed=results['characters-10000']['gatePassed']))
    print(json.dumps(dict(actualOptimizerUpdates=10000,files=len(files),results=results)))
if __name__ == '__main__': main()
