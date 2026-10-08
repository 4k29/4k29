"""Record common-prefix logits at the already observed unedited divergence."""
import hashlib,json,pathlib,subprocess,sys
import torch
ROOT=pathlib.Path(__file__).resolve().parent
from evaluate import load_model
from tokenizer import SPECIALS,encode_stream

def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 torch.set_num_threads(1);folder=ROOT/'word-512-continue-10000';py=read(folder/'validation.json');js=read(folder/'validation-js.json');model,export=load_model(folder/'model.js');rows=[]
 for a,b in zip(py['rows'],js['rows'],strict=True):
  if a['tokens']==b['tokens'] and a['eos']==b['eos']:continue
  position=next((i for i,(x,y) in enumerate(zip(a['tokens'],b['tokens'])) if x!=y),min(len(a['tokens']),len(b['tokens'])))
  tokens=[SPECIALS['bos']]+encode_stream(a['prefix'],export['tokenizer'])+a['tokens'][:position]
  with torch.no_grad():scores=model(torch.tensor([tokens]))[0,-1]
  top=torch.topk(scores,5);rows.append(dict(id=a['id'],firstDifferentIndex=position,tokens=tokens,pythonChosenToken=a['tokens'][position],javascriptChosenToken=b['tokens'][position],pythonTop5=[dict(token=int(t),score=float(s),piece=bytes.fromhex(export['tokenizer']['bytes'][int(t)]).decode('utf8',errors='replace')) for s,t in zip(top.values,top.indices)],pythonTopTwoMargin=float(top.values[0]-top.values[1]),pythonLogits=scores.tolist()))
 write(folder/'divergence-python.json',dict(modelSha256=sha(folder/'model.js'),generationSha256=sha(folder/'validation.json'),rows=rows,noNewGeneration=True,weightsChanged=False))
 subprocess.run(['node',str(ROOT/'diagnose_divergence.mjs'),str(folder/'model.js'),str(folder/'divergence-python.json'),str(ROOT/'numerical-divergence.json')],check=True)
if __name__=='__main__':main()
