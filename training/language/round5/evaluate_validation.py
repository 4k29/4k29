"""Freeze own character weights before development generation; TEST stays shut."""
import gzip,hashlib,json,pathlib,subprocess,sys,time
import torch
from train import export_model
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def run(command,path):
    with path.open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
    directory=ROOT/'characters-10000'
    while not (directory/'result.json').exists():time.sleep(10)
    result=read(directory/'result.json');assert result['completedRun'] and result['completedSteps']==10000
    assert result['randomInitialization'] and result['previousWeightsNotAllowed'] and result['unicodeCharacterAssembly']
    baseline=ROOT/'baseline-1000';baseline.mkdir(exist_ok=True);torch.set_num_threads(1);cp=directory/'checkpoint-1000.pt';saved=torch.load(cp,map_location='cpu',weights_only=False)
    assert saved['step']==1000;counts=sorted({int(s['step']) for s in saved['optimizer']['state'].values()});assert counts==[1000]
    tok=read(ROOT/f"unicode-bpe-{result['merges']}/tokenizer.json")
    training=dict(**saved['settings'],completedRun=False,diagnosticSnapshot=True,completedSteps=1000,requestedSteps=10000,bestStep=saved['beststep'],parameters=result['parameters'],checkpointSha256=sha(cp),history=saved['history'],selection='Own character run best canonical VAL byte loss available by actual1000; not outside or previous weights')
    export_model(None,saved['beststate'],tok,saved['config'],training,baseline/'model.js');packed=baseline/'model.js.gz';packed.write_bytes(gzip.compress((baseline/'model.js').read_bytes(),mtime=0))
    write(baseline/'snapshot.json',dict(actualOptimizerUpdates=1000,selectedStep=saved['beststep'],optimizerStepCounters=counts,checkpointSha256=sha(cp),plainModelSha256=sha(baseline/'model.js'),gzipModelSha256=sha(packed),additionalUpdates=False));del saved
    metrics=read(directory/'metrics.json');assert not list(ROOT.glob('*/test.json'))
    write(ROOT/'checkpoint-choice.json',dict(run=directory.name,completedUpdates=10000,selectedStep=result['bestStep'],bestCanonicalValidationNllPerByte=metrics['bestValidationNllPerByte'],modelSha256=sha(directory/'model.js'),baselineModelSha256=sha(baseline/'model.js'),policySha256=sha(ROOT/'generation-policy.json'),testUsed=False,baseline='Same new character run at saved1000; same vocabulary, architecture, output-token limit and fold',developmentLanguageGateRequiredBeforeTest=True))
    for modeldir in [directory,baseline]:
        run([sys.executable,str(ROOT/'evaluate.py'),'--model',str(modeldir/'model.js'),'--partition','validation','--out',str(modeldir/'validation.json'),'--reference'],modeldir/'validation-generation.log')
        run(['node',str(ROOT/'evaluate_js.mjs'),str(modeldir/'model.js'),str(modeldir/'validation.json'),str(modeldir/'validation-js.json')],modeldir/'validation-parity.log')
    (baseline/'model.js').unlink()
    print(json.dumps(dict(developmentGenerationCompleted=True,testStillUnopened=True,manualReviewRequired=True)),flush=True)
if __name__=='__main__':main()
