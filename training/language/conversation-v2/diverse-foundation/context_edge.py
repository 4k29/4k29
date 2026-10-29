"""Supplementary zero-update boundary-contract audit, not a new language benchmark."""
import argparse
from common import *
from study_checkpoint import load
from prose_decode import greedy
def main():
 a=argparse.ArgumentParser();a.add_argument('--model',required=True);args=a.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 model,cursor=load(args.model);model.eval();pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];units=gzrows(D/'corpus.jsonl.gz');rows=[]
 for source in ['jaquad','realpersona','jawikibooks','jawikivoyage','jma']:
  eligible=sorted([r for r in units if r['split']=='train'and r['source']==source and len(r['tokens'])>=257],key=lambda r:rank('edge|'+r['id']))
  if not eligible:continue
  r=eligible[0];t=r['tokens'][:257]
  with torch.inference_mode():
   log=model(torch.tensor([t[:256]]));assert log.shape==(1,256,3997)and torch.isfinite(log).all();p=log[0,-1].softmax(-1)
   g=greedy(model,t[:255],pieces,max_new=1)
   try:greedy(model,t[:255],pieces,max_new=2)
   except ValueError:over_budget_rejected=True
   else:raise AssertionError('Decoder silently exceeded fixed generation budget')
   try:model(torch.tensor([t[:256]+[6]]))
   except IndexError:position257_rejected=True
   else:raise AssertionError('Model unexpectedly accepted more positions than learned embeddings')
  rows.append(dict(source=source,unit_id=r['id'],prefix_tokens=t[:255],edge_generation=g,full_256_input_logits_finite=True,last_position_pEOS=float(p[2]),last_position_gold=t[256],last_position_gold_probability=float(p[t[256]]),over_budget_rejected=over_budget_rejected,model_position257_rejected=position257_rejected))
 out=D/'context-edge';out.mkdir(exist_ok=True);write(out/(args.model+'.json'),dict(model=args.model,cursor=cursor,rows=rows,optimizer_updates=0,scope='One rank-fixed TRAIN unit per eligible source; diagnostic selected after common results. Helper requires prefix+planned outputs<=256 and never crops/rolls. Architecture has256 learned input positions; a direct257 input raises IndexError. No long-context language success claimed. Earlier main failures occur well before budget edge.'))
 print('Context edge contract checked',args.model,len(rows))
if __name__=='__main__':main()
