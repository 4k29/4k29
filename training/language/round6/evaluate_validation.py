"""VAL-only parent/child generation after immutable likelihood selection."""
import gzip,hashlib,json,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parent;PARENT=ROOT.parent/'round5'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def run(command,path):
    with path.open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
    candidate=ROOT/'character-continue-10000'
    while not (candidate/'result.json').exists():time.sleep(10)
    result=read(candidate/'result.json');assert result['completedRun'] and result['completedSteps']==10000
    assert result['ownParentOnly'] and result['ownRandomInitializedLineage'] and result['optimizerReset']
    assert result['parentCheckpointSha256']==sha(PARENT/'characters-10000/checkpoint.pt')
    assert result['experimentPolicySha256']==sha(ROOT/'experiment-policy.json')
    assert not list(ROOT.glob('*/test.json')) and not list(PARENT.glob('*/test.json'))
    baseline=ROOT/'parent-10000';baseline.mkdir(exist_ok=True)
    model=PARENT/'characters-10000/model.js';(baseline/'model.js').write_bytes(model.read_bytes())
    packed=baseline/'model.js.gz';packed.write_bytes(gzip.compress(model.read_bytes(),mtime=0))
    write(baseline/'snapshot.json',dict(parentCompletedUpdates=result['parentCompletedSteps'],parentSelectedUpdates=result['parentSelectedSteps'],parentCheckpointSha256=result['parentCheckpointSha256'],plainModelSha256=sha(model),gzipModelSha256=sha(packed),additionalUpdates=False))
    metrics=read(candidate/'metrics.json')
    write(ROOT/'checkpoint-choice.json',dict(run=candidate.name,actualChildUpdates=10000,selectedChildUpdates=result['bestStep'],selectedWeightLineageUpdates=result['parentSelectedSteps']+result['bestStep'],parentSelectedUpdates=result['parentSelectedSteps'],bestCanonicalValidationNllPerByte=metrics['bestValidationNllPerByte'],modelSha256=sha(candidate/'model.js'),baselineModelSha256=sha(model),policySha256=sha(ROOT/'generation-policy.json'),experimentPolicySha256=sha(ROOT/'experiment-policy.json'),testUsed=False,selection='Canonical VAL byte NLL only; fixed before development generation'))
    for folder in [candidate,baseline]:
        run([sys.executable,str(ROOT/'evaluate.py'),'--model',str(folder/'model.js'),'--partition','validation','--out',str(folder/'validation.json'),'--reference'],folder/'validation-generation.log')
        run(['node',str(ROOT/'evaluate_js.mjs'),str(folder/'model.js'),str(folder/'validation.json'),str(folder/'validation-js.json')],folder/'validation-parity.log')
    (baseline/'model.js').unlink()
    print(json.dumps(dict(developmentGenerationCompleted=True,testStillUnopened=True,manualReviewRequired=True)),flush=True)
if __name__=='__main__':main()
