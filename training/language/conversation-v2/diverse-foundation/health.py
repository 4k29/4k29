"""Three independent original sections: learn distinct prefix continuations, not BOS-only ambiguity."""
import time
from common import *
from state import starting
from prose_decode import greedy

def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=read(D/'PLAN.json');out=D/'health';out.mkdir(exist_ok=True);assert not(out/'updates.jsonl').exists();sources=read(D/'HEALTH_SOURCES.json');model,opt,rng,base=starting('B');pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];trace=[];evaluations=[];x,y=pack(sources);t0=time.monotonic()
 for g in opt.param_groups:g['lr']=plan['health']['lr']
 for step in range(1,plan['health']['max_updates']+1):
  model.train();opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1));assert math.isfinite(norm);row=dict(step=step,loss=float(loss.detach()),gradient_norm_before_clip=norm,targets=int(y.ne(-100).sum()));record(out/'updates.jsonl',dict(event='intent',step=step,trace=row));opt.step();record(out/'updates.jsonl',dict(event='completed',step=step,trace=row));opt.zero_grad(set_to_none=True);trace.append(row)
  if step%plan['health']['check_every']==0:
   model.eval();cases=[]
   with torch.inference_mode():
    nll=float(causal_ce(model(x),y))
    for r in sources:
     g=greedy(model,r['prefix'],pieces,max_new=len(r['reference']));cases.append(dict(id=r['id'],prefix=r['prefix'],reference=r['reference'],exact=g['tokensIncludingEos']==r['reference'],**g))
   evaluations.append(dict(step=step,teacher_NLL=nll,cases=cases));write(out/'evaluations.json',evaluations);save(out/'checkpoint.pt',dict(trajectory=trajectory(model,opt,rng,[],step,[],step),active_cursor=step,trace=trace,plan_sha256=sha(D/'PLAN.json')));print('health',step,nll,[r['exact']for r in cases],flush=True)
   if all(r['exact']for r in cases):break
 receipt=dict(all_three_exact=all(r['exact']for r in evaluations[-1]['cases']),actual_optimizer_calls=len(trace),retained_updates=len(trace),retained_targets=sum(r['targets']for r in trace),unique_source_body_tokens=sum(len(r['tokens'])-2 for r in sources),full_sequence_repetitions=len(trace),elapsed_seconds=time.monotonic()-t0,unknown_generalization_proven=False,formal_adoption=False);write(out/'receipt.json',receipt)
if __name__=='__main__':main()
