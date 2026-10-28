"""Correct-history old dialogue diagnostic; EOS metrics do not imply conversation success."""
import argparse,json
import numpy as np
from eval_runtime import N, H,V,torch,initial,snapshot,restore_isolated,pack
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default='initial');a=p.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);base=initial()if a.model=='initial'else snapshot(a.model);model,_,_=restore_isolated(base['trajectory']);model.eval();meta=json.loads((V/'data/data.json').read_text());v=np.fromfile(H.parents[3]/meta['devTokensPath'],dtype='<u4');stats={k:dict(nll_sum=0.,tokens=0)for k in ['all','body','role','eos']};prob=correct=count=0
 with torch.no_grad():
  for w in meta['devWindows']:
   s=v[w['offset']:w['offset']+w['length']].tolist();x=torch.tensor([s[:-1]]);y=torch.tensor(s[1:]);logits=model(x)[0];loss=torch.nn.functional.cross_entropy(logits,y,reduction='none')
   for key,mask in [('all',y.ge(0)),('body',y.ge(6)),('role',y.eq(3)|y.eq(4)),('eos',y.eq(2))]:stats[key]['nll_sum']+=float(loss[mask].sum());stats[key]['tokens']+=int(mask.sum())
   mask=y.eq(2);prob+=float(logits.softmax(-1)[mask,2].sum());correct+=int(logits.argmax(-1)[mask].eq(2).sum());count+=int(mask.sum())
 for r in stats.values():r['nll']=r['nll_sum']/r['tokens']
 result=dict(model=a.model,stats=stats,gold_end_mean_EOS_probability=prob/count,gold_end_EOS_top1_fraction=correct/count,gold_end_positions=count,optimizer_updates=0,scope='existing exposed humanA/B DEV, correct teacher history; not semantic dialogue success or independent TEST');out=N/'evaluation'/(a.model+'-RP.json');assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(a.model,result['gold_end_mean_EOS_probability'],result['stats']['body']['nll'],flush=True)
if __name__=='__main__':main()
