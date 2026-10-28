"""New checkpoints: original true-page ends versus new complete paragraph ends."""
import argparse,gzip,statistics
from eval_runtime import *
from mixed_runtime import pack

def main():
 p=argparse.ArgumentParser();p.add_argument('--models',nargs='+',required=True);a=p.parse_args();torch.set_num_threads(2);pure=json.load(gzip.open(H/'schedule.json.gz','rt'));ends={k:[w for w in ws if 2 in w['tokens'][1:]]for k,ws in [('old_TRAIN',[w for b in pure['batches']for w in b]),('old_DEV',pure['dev'])]};native=json.loads((N/'paragraphs.json').read_text());forms=N/'forms';forms.mkdir(exist_ok=True)
 for name in a.models:
  out=forms/(name+'-native.json');assert not out.exists();model,_,_=restore_isolated((initial()if name=='initial'else snapshot(name))['trajectory']);model.eval();result={}
  with torch.no_grad():
   for part,ws in ends.items():
    probs=[]
    for i in range(0,len(ws),4):
     batch=ws[i:i+4];x,y=pack(batch);logits=model(x)
     for b,w in enumerate(batch):
      for j,t in enumerate(w['tokens'][1:]):
       if t==2:probs.append(dict(id=w['id'],position=j,p_EOS=float(logits[b,j].softmax(-1)[2]),argmax=int(logits[b,j].argmax())))
    result[part]=dict(count=len(probs),mean_pEOS=statistics.mean(r['p_EOS']for r in probs),EOS_argmax=sum(r['argmax']==2 for r in probs),positions=probs)
   for part,rs in [('paragraph_TRAIN_fixed32',native['train'][:32]),('paragraph_DEV',native['dev'])]:
    probs=[]
    for r in rs:
     ids=r['tokens'];logits=model(torch.tensor([ids[:-1]]))[0,-1];probs.append(dict(id=r['id'],p_EOS=float(logits.softmax(-1)[2]),argmax=int(logits.argmax())))
    result[part]=dict(count=len(probs),mean_pEOS=statistics.mean(r['p_EOS']for r in probs),EOS_argmax=sum(r['argmax']==2 for r in probs),positions=probs)
  write(out,dict(model=name,results=result,optimizer_updates=0,scope='Exposed DEV and fixed32 TRAIN, full original paragraph not cut; paragraph EOS is new task boundary, page EOS is original parser page-end'));print(name,'end probabilities saved',flush=True)
if __name__=='__main__':main()
