"""Inspect common-prefix logits without changing weights or repairing outputs."""
import pathlib,sys,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'round10'))
from evaluate import load_model
from tokenizer import SPECIALS,encode_stream
import torch
from train import read,write,sha
torch.set_num_threads(1)
for name,path in [('old',ROOT.parent/'round39/continue-10000/model.js'),('new',ROOT/'continue-10000/model.js')]:
 py=read(ROOT/'execution'/f'{name}-validation.json');js=read(ROOT/'execution'/f'{name}-validation-js.json');model,export=load_model(path);rows=[]
 for a,b in zip(py['rows'],js['rows'],strict=True):
  if all(a[k]==b[k] for k in ['tokens','text','eos','validUtf8','validTokens','inputTokens']):continue
  position=next((i for i,(x,y) in enumerate(zip(a['tokens'],b['tokens'])) if x!=y),min(len(a['tokens']),len(b['tokens'])))
  tokens=[SPECIALS['bos']]+encode_stream(a['prefix'],export['tokenizer'])+a['tokens'][:position]
  with torch.no_grad():scores=model(torch.tensor([tokens]))[0,-1]
  rank=sorted(range(len(scores)),key=lambda t:(-float(scores[t]),t))[:5]
  rows.append(dict(id=a['id'],firstDifferentIndex=position,tokens=tokens,pythonChosenToken=a['tokens'][position] if position<len(a['tokens']) else SPECIALS['eos'],javascriptChosenToken=b['tokens'][position] if position<len(b['tokens']) else SPECIALS['eos'],pythonTop5=[dict(token=int(t),score=float(s),piece=bytes.fromhex(export['tokenizer']['bytes'][int(t)]).decode('utf8',errors='replace')) for t,s in [(t,scores[t]) for t in rank]],pythonTopTwoMargin=float(scores[rank[0]]-scores[rank[1]]),pythonLogits=scores.tolist()))
 trace=ROOT/'execution'/f'{name}-divergence-python.json';write(trace,dict(modelSha256=sha(path),generationSha256=sha(ROOT/'execution'/f'{name}-validation.json'),rows=rows,totalSequences=len(py['rows']),noNewGeneration=True,weightsChanged=False))
 subprocess.run(['node',str(ROOT/'execution/diagnose_parity.mjs'),str(path),str(trace),str(ROOT/'execution'/f'{name}-numerical-divergence.json')],check=True)
