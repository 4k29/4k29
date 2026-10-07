"""Freeze own continued weights before development generation; keep TEST shut."""
import hashlib,json,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    directory=ROOT/'boundary-focus-2000'
    while not (directory/'result.json').exists():time.sleep(10)
    result=read(directory/'result.json');metrics=read(directory/'metrics.json')
    assert result['completedRun'] and result['completedSteps']==2000
    assert result['ownParentOnly'] and result['ownRandomInitializedLineage']
    assert result['optimizerReset'] and result['seedReset']
    assert result['parentCheckpointSha256']==sha(ROOT.parent/'round3/raw-chains-10000/checkpoint.pt')
    assert not list(ROOT.glob('*/test.json'))
    choice=dict(run=directory.name,completedUpdates=2000,parentCompletedUpdates=result['parentCompletedSteps'],parentSelectedUpdates=result['parentSelectedSteps'],selectedUpdates=result['bestStep'],selectedWeightLineageUpdates=result['parentSelectedSteps']+result['bestStep'],bestCanonicalValidationNllPerByte=metrics['bestValidationNllPerByte'],modelSha256=sha(directory/'model.js'),policySha256=sha(ROOT/'generation-policy.json'),testUsed=False,selection='Lowest unchanged canonical VAL byte NLL before generation; fresh optimizer/seed and own round3 beststate only')
    (ROOT/'checkpoint-choice.json').write_text(json.dumps(choice,indent=2)+'\n')
    commands=[([sys.executable,str(ROOT/'evaluate.py'),'--model',str(directory/'model.js'),'--partition','validation','--out',str(directory/'validation.json'),'--reference'],directory/'validation-generation.log'),(['node',str(ROOT.parent/'evaluate_js.mjs'),str(directory/'model.js'),str(directory/'validation.json'),str(directory/'validation-js.json')],directory/'validation-parity.log')]
    for command,log in commands:
        with log.open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
    print(json.dumps(dict(developmentGenerationComplete=True,testStillUnopened=True,manualReviewRequired=True)),flush=True)
if __name__=='__main__':main()
