"""VAL-only generation after immutable likelihood selection; TEST stays closed."""
import gzip,hashlib,json,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(1,str(ROOT.parent))
import torch
from model import Decoder
from train import export_model

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def run(command,path):
    with path.open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
    candidate=ROOT/'expanded-characters-10000'
    while not (candidate/'result.json').exists():time.sleep(10)
    result=read(candidate/'result.json');assert result['completedRun'] and result['completedSteps']==10000
    assert result['ownParentOnly'] and result['ownRandomInitializedLineage'] and result['optimizerReset']
    policy=read(ROOT/'experiment-policy.json');assert result['experimentPolicySha256']==sha(ROOT/'experiment-policy.json')
    for relative,key in [('train.py','trainerSourceSha256'),('initialization.py','initializationSourceSha256'),('documents.jsonl','sourceSha256'),('split.json','splitSha256'),('units.json','rawUnitsSha256'),('generation-policy.json','generationPolicySha256')]:assert sha(ROOT/relative)==policy[key]
    assert not list(ROOT.glob('*/test.json'))
    baseline=ROOT/'initial-0';baseline.mkdir(exist_ok=True)
    saved=torch.load(candidate/'checkpoint-0.pt',map_location='cpu',weights_only=False)
    assert saved['step']==0 and saved['seen_tokens']==0 and saved['seen_bytes']==0 and not saved['optimizer']['state']
    model=Decoder(saved['config']);model.load_state_dict(saved['model']);tokenizer=read(ROOT/'unicode-bpe-4578/tokenizer.json')
    training=dict(**saved['settings'],completedRun=False,completedSteps=0,bestStep=0,parameters=sum(p.numel() for p in model.parameters()),seenTargetTokens=0,seenTargetUtf8Bytes=0,checkpointSha256=sha(candidate/'checkpoint-0.pt'),comparisonBaseline=True)
    export_model(model,saved['model'],tokenizer,saved['config'],training,baseline/'model.js')
    packed=baseline/'model.js.gz';packed.write_bytes(gzip.compress((baseline/'model.js').read_bytes(),mtime=0))
    write(baseline/'snapshot.json',dict(completedUpdates=0,optimizerCounters=[],checkpointSha256=sha(candidate/'checkpoint-0.pt'),plainModelSha256=sha(baseline/'model.js'),gzipModelSha256=sha(packed),additionalUpdates=False,parentSelectedWeightLineageUpdates=result['parentSelectedWeightLineageUpdates']))
    metrics=read(candidate/'metrics.json')
    write(ROOT/'checkpoint-choice.json',dict(run=candidate.name,actualChildUpdates=10000,selectedChildUpdates=result['bestStep'],selectedWeightLineageUpdates=result['parentSelectedWeightLineageUpdates']+result['bestStep'],parentSelectedUpdates=result['parentSelectedWeightLineageUpdates'],bestCanonicalValidationNllPerByte=metrics['bestValidationNllPerByte'],modelSha256=sha(candidate/'model.js'),baselineModelSha256=sha(baseline/'model.js'),policySha256=sha(ROOT/'generation-policy.json'),experimentPolicySha256=sha(ROOT/'experiment-policy.json'),testUsed=False,selection='Canonical VAL byte NLL only; fixed before development generation'))
    for folder in [candidate,baseline]:
        run([sys.executable,str(ROOT/'evaluate.py'),'--model',str(folder/'model.js'),'--partition','validation','--out',str(folder/'validation.json'),'--reference'],folder/'validation-generation.log')
        run(['node',str(ROOT/'evaluate_js.mjs'),str(folder/'model.js'),str(folder/'validation.json'),str(folder/'validation-js.json')],folder/'validation-parity.log')
    (baseline/'model.js').unlink()
    print(json.dumps(dict(developmentGenerationCompleted=True,testStillUnopened=True,manualReviewRequired=True)),flush=True)
if __name__=='__main__':main()
