"""Same saved human32 QA inputs; gold EOS probability plus saved raw generation rate."""
import argparse,collections
import numpy as np
from common import *

def main():
 p=argparse.ArgumentParser();p.add_argument('--new',nargs='*');a=p.parse_args();torch.set_num_threads(2);tok=json.loads((V/'data/tokenizer.json').read_text());human=json.loads((V/'foundation-data/evaluation/human-dev.json').read_text())['cases'];names=a.new or['initial','foundation','foundation-mixed','foundation-lr','qa-only','qa-rehearsal'];out=N/'forms';out.mkdir(exist_ok=True)
 for name in names:
  if a.new:
   from eval_runtime import snapshot as loadnew
   state=loadnew(name)
  else:state=initial()if name=='initial'else snapshot(name)
  model,_,_=restore_isolated(state['trajectory']);model.eval();rows=[]
  with torch.no_grad():
   for r in human:
    s=r['prefixTokens']+r['goldTokens']+[2];logits=model(torch.tensor([s[:-1]]))[0];body=logits[len(r['prefixTokens'])-1:];y=torch.tensor(r['goldTokens']+[2]);loss=torch.nn.functional.cross_entropy(body,y,reduction='none');rows.append(dict(id=r['id'],p_EOS_at_reference_end=float(body[-1].softmax(-1)[2]),EOS_argmax_at_reference_end=int(body[-1].argmax())==2,body_NLL_sum=float(loss[:-1].sum()),body_targets=len(r['goldTokens'])))
  path=(N if a.new else H)/'evaluation'/(name+'-human32.json');saved=json.loads(path.read_text())['cases']if path.exists()else[];result=dict(model=name,source_sha256=sha(V/'foundation-data/evaluation/human-dev.json'),scope='Same old exposed human32 QA prefix/reference; saved full greedy replies, not independent TEST',reference_end_mean_pEOS=sum(r['p_EOS_at_reference_end']for r in rows)/len(rows),reference_end_EOS_argmax=sum(r['EOS_argmax_at_reference_end']for r in rows),saved_greedy_EOS=sum(r['eos']for r in saved),saved_greedy_count=len(saved),cases=rows,optimizer_updates=0);write(out/(name+'-QA.json'),result);print(name,result['reference_end_mean_pEOS'],result['saved_greedy_EOS'],flush=True)
 meta=json.loads((V/'data/data.json').read_text());freq={}
 for part in ['train','dev']:
  v=np.fromfile(N.parents[3]/meta[part+'TokensPath'],dtype='<u4');c=collections.Counter();positions=collections.Counter()
  for w in meta[part+'Windows']:
   s=v[w['offset']+1:w['offset']+w['length']];c['targets']+=len(s);c['EOS']+=int((s==2).sum());c['role']+=int(((s==3)|(s==4)).sum())
   for j in np.where(s==2)[0]:positions[str(int(j)//32*32)]+=1
  freq[part]=dict(c,EOS_position_bins32=dict(positions),scope='Original RealPersona full epoch teacher positions, no update; not the new sampled schedule')
 write(out/'RP_FREQUENCY.json',freq)
if __name__=='__main__':main()
