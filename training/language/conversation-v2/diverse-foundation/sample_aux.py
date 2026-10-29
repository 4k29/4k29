"""One fixed raw categorical sample per prefix. Auxiliary distribution diagnosis, not primary success."""
import argparse
from common import *
from evaluate import load
from eval_core import byte_payload,repeated_gram

def main():
 a=argparse.ArgumentParser();a.add_argument('--freeze',action='store_true');a.add_argument('--model');args=a.parse_args();proto=D/'SAMPLING_PROTOCOL.json'
 if args.freeze:
  c=read(D/'EVALUATION.json')['cases'];selected=[c[i]for i in [0,8,16,22,33,37,41,47]];write(proto,dict(cases=selected,temperature=1.,top_p=1.,seed=51029,max_new=128,full_vocabulary=True,repetition_penalty=None,primary_greedy_unchanged=True,purpose='Whether raw sampling avoids a greedy attractor but still has broken grammar/topic; no seed/temperature search or successful-sample selection; exposed diagnostic only',formal_language_success_from_sampling=False));return
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);model,cur=load(args.model);model.eval();p=read(proto);pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];cases=[];out=D/'sampling';out.mkdir(exist_ok=True);assert not(out/(args.model+'.json')).exists()
 with torch.inference_mode():
  for i,c in enumerate(p['cases']):
   pre=c['prefix'];generated=[];steps=[];g=torch.Generator().manual_seed(p['seed']+i);before=g.get_state().numpy().tobytes().hex()
   for j in range(p['max_new']):
    logits=model(torch.tensor([pre+generated]))[0,-1];prob=logits.softmax(-1);t=int(torch.multinomial(prob,1,generator=g));generated.append(t);steps.append(dict(position=j,token=t,pEOS=float(prob[2]),probability=float(prob[t]),entropy=float(-(prob*prob.clamp_min(1e-40).log()).sum())))
    if t==2:break
   eos=generated[-1]==2;body=generated[:-1]if eos else generated;cases.append(dict(id=c['id'],panel=c['panel'],prefix=pre,tokensIncludingEos=generated,eos=eos,stopReason='genuine-eos-token2'if eos else'fixed-max-new-tokens',steps=steps,repeated4gram=repeated_gram(body,4),generator_state_before_hex=before,generator_state_after_hex=g.get_state().numpy().tobytes().hex(),**byte_payload(body,pieces)))
 write(out/(args.model+'.json'),dict(model=args.model,cursor=cur,protocol_sha256=sha(proto),cases=cases,primary_greedy=False,optimizer_updates=0));print('sampling',args.model,len(cases),flush=True)
if __name__=='__main__':main()
