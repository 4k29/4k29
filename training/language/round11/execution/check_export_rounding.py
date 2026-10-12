"""Compare raw selected FP32 checkpoint to the seven-decimal inference export."""
import pathlib,sys,json,torch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'round10'))
from evaluate import load_model,generate
from train import read,write,sha
from model import Decoder
torch.set_num_threads(1)
cp=torch.load(ROOT/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);model=Decoder(cp['config']);model.load_state_dict(cp['beststate']);model.eval()
rounded,export=load_model(ROOT/'continue-10000/model.js');g=read(ROOT/'execution/new-validation.json');rows=[];errors=[]
for r in g['rows']:
 raw=generate(model,r['prefix'],export['tokenizer'],g['maxNewTokens']);same=all(raw[k]==r[k] for k in ['text','tokens','eos','validUtf8','validTokens','inputTokens'])
 rows.append(dict(id=r['id'],prefix=r['prefix'],**raw,sameAsRoundedPython=same))
for ref in g['references']:
 with torch.no_grad():raw=model(torch.tensor([ref['tokens']]))[0,-1];rounded_scores=rounded(torch.tensor([ref['tokens']]))[0,-1]
 errors.append(dict(id=ref['id'],maxAbsoluteError=float((raw-rounded_scores).abs().max())))
write(ROOT/'execution/export-rounding.json',dict(checkpointSha256=sha(ROOT/'continue-10000/checkpoint.pt'),modelSha256=sha(ROOT/'continue-10000/model.js'),selectedStep=cp['beststep'],completeRawVersusRoundedGenerationParity=all(r['sameAsRoundedPython'] for r in rows),matchingSequences=sum(r['sameAsRoundedPython'] for r in rows),totalSequences=len(rows),references=errors,rows=rows,noOutputRepair=True,note='Frozen exporter rounds weights to seven decimal places. This probe checks its effect on the same development openings; no universal numeric equivalence claim.'))
