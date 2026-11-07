"""Isolated memorization health check only; never an adopted model or unknown-family result."""
import time,copy,subprocess,os
from common import *
from state import starting
from prose_decode import greedy

def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);spec=read(P/'OVERFIT_PLAN.json');out=P/'overfit';out.mkdir(exist_ok=True);assert not(out/'receipt.json').exists();data=read(P/'OVERFIT_SOURCES.json');model,opt,rng,base=starting('C');pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];trace=[];evaluations=[];t0=time.monotonic()
 for g in opt.param_groups:g['lr']=spec['lr']
 x,y=pack([dict(tokens=r['tokens'])for r in data])
 for step in range(1,spec['maximum_updates']+1):
  model.train();opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);assert torch.isfinite(loss);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1));row=dict(step=step,loss=float(loss.detach()),gradient_norm_before_clip=norm,targets=int(y.ne(-100).sum()));record(out/'updates.jsonl',dict(event='intent',trace=row));opt.step();record(out/'updates.jsonl',dict(event='completed',trace=row));opt.zero_grad(set_to_none=True);trace.append(row)
  if step%64==0:
   model.eval();cases=[]
   with torch.inference_mode():
    gold_logits=model(x);nll=float(causal_ce(gold_logits,y))
    for r in data:
     g=greedy(model,r['tokens'][:1],pieces,max_new=len(r['tokens'])-1);cases.append(dict(id=r['id'],prefix=r['tokens'][:1],reference=r['tokens'][1:],exact=g['tokensIncludingEos']==r['tokens'][1:],**g))
   evaluations.append(dict(step=step,teacher_NLL=nll,cases=cases));write(out/'evaluations.json',evaluations);save(out/'checkpoint.pt',dict(trajectory=trajectory(model,opt,rng,[],step,[],step),active_cursor=step,trace=trace,plan_sha256=sha(P/'OVERFIT_PLAN.json')))
   if all(r['exact']for r in cases):break
 receipt=dict(actual_optimizer_calls=len(trace),retained_updates=len(trace),targets=sum(r['targets']for r in trace),unique_body_tokens=sum(len(r['body_tokens'])for r in data),full_sequence_repetitions=len(trace),exact_train_sequences=sum(r['exact']for r in evaluations[-1]['cases']),train_sequences=len(data),elapsed_seconds=time.monotonic()-t0,unknown_generalization_proven=False,formal_adoption=False)
 write(out/'receipt.json',receipt);print(receipt,flush=True)
if __name__=='__main__':main()
