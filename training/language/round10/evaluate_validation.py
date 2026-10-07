"""VAL-only after likelihood selection; compare main0 warm start and final weights."""
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
 while not (ROOT/'vocabulary-choice.json').exists():time.sleep(10)
 vocabulary=read(ROOT/'vocabulary-choice.json');candidate=ROOT/f"word-{vocabulary['wordMerges']}-continue-10000"
 while not (candidate/'result.json').exists():time.sleep(10)
 result=read(candidate/'result.json');assert result['completedRun'] and result['completedSteps']==10000 and result['checkpointSha256']==sha(candidate/'checkpoint.pt')
 assert result['ownParentOnly'] and result['ownRandomInitializedLineage'] and result['optimizerReset'] and result['experimentPolicySha256']==sha(ROOT/'training-policy.json')
 for f in read(ROOT/'source-manifest.json')['files']:assert sha(ROOT/f['path'])==f['sha256']
 assert not list(ROOT.glob('*/test.json'))
 baseline=ROOT/'main-initial-0';baseline.mkdir(exist_ok=True)
 saved=torch.load(candidate/'checkpoint-0.pt',map_location='cpu',weights_only=False);assert saved['step']==0 and saved['seen_tokens']==saved['seen_bytes']==0 and not saved['optimizer']['state']
 model=Decoder(saved['config']);model.load_state_dict(saved['model']);tok=read(ROOT/f"word-bpe-{vocabulary['wordMerges']}/tokenizer.json")
 training=dict(**saved['settings'],completedRun=False,completedSteps=0,bestStep=0,parameters=sum(p.numel() for p in model.parameters()),seenTargetTokens=0,seenTargetUtf8Bytes=0,checkpointSha256=sha(candidate/'checkpoint-0.pt'),comparisonBaseline=True)
 export_model(model,saved['model'],tok,saved['config'],training,baseline/'model.js');packed=baseline/'model.js.gz';packed.write_bytes(gzip.compress((baseline/'model.js').read_bytes(),mtime=0))
 write(baseline/'snapshot.json',dict(completedMainUpdates=0,optimizerCounters=[],checkpointSha256=sha(candidate/'checkpoint-0.pt'),plainModelSha256=sha(baseline/'model.js'),gzipModelSha256=sha(packed),parentSelectedWeightLineageUpdates=result['parentSelectedWeightLineageUpdates'],note='Baseline includes selected own pilot learning, but adds zero main updates. Original pre-pilot likelihood is recorded separately.'))
 write(ROOT/'checkpoint-choice.json',dict(run=candidate.name,actualMainUpdates=10000,selectedMainUpdates=result['bestStep'],selectedWeightLineageUpdates=result['parentSelectedWeightLineageUpdates']+result['bestStep'],parentSelectedWeightLineageUpdates=result['parentSelectedWeightLineageUpdates'],modelSha256=sha(candidate/'model.js'),baselineModelSha256=sha(baseline/'model.js'),vocabularyChoiceSha256=sha(ROOT/'vocabulary-choice.json'),meaningPolicySha256=sha(ROOT/'full-meaning-policy.json'),generationPolicySha256=sha(ROOT/'generation-policy.json'),selection='Canonical VAL byte NLL only; frozen before raw development generation',testUsed=False))
 for folder in [baseline,candidate]:
  run([sys.executable,str(ROOT/'evaluate.py'),'--model',str(folder/'model.js'),'--partition','validation','--out',str(folder/'validation.json'),'--reference'],folder/'validation-generation.log')
  run(['node',str(ROOT/'evaluate_js.mjs'),str(folder/'model.js'),str(folder/'validation.json'),str(folder/'validation-js.json')],folder/'validation-parity.log')
 (baseline/'model.js').unlink()
 print(json.dumps(dict(developmentGenerationCompleted=True,rowsEach=17,testStillUnopened=True,manualReviewRequired=True)),flush=True)
if __name__=='__main__':main()
