"""Read-only fixed checkpoint baseline on frozen new prose DEV; zero optimizer calls."""
import pathlib,json,hashlib,sys,argparse,time
D=pathlib.Path(__file__).resolve().parent;OLD=D.parent/'diverse-foundation';sys.path.insert(0,str(OLD))
from evaluate import load
from common import torch
from prose_decode import greedy

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--arm',choices=['A','B'],required=True);args=parser.parse_args();out=D/f'NEW_PROSE_BASELINE_{args.arm}.json';assert not out.exists(),'Never overwrite observed evaluation'
 plan=json.loads((D/'NEW_PROSE_DEV_PROTOCOL.json').read_text());p=D/'private/new-prose-dev.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==plan['private_inputs_sha256'];cases=json.loads(p.read_text());tok_path=D.parent/'data/tokenizer.json';assert hashlib.sha256(tok_path.read_bytes()).hexdigest()==plan['tokenizer_sha256'];pieces=[bytes.fromhex(s)for s in json.loads(tok_path.read_text())['bytes']];torch.set_num_threads(2);torch.use_deterministic_algorithms(True);start=time.time();model,cursor=load(args.arm+'-6459');model.eval();rows=[];nll_sum=0.;target_count=0
 with torch.inference_mode():
  for case in cases:
   t=case['tokens'][:257];x=torch.tensor([t[:-1]],dtype=torch.long);y=torch.tensor(t[1:],dtype=torch.long);log=model(x)[0];loss=float(torch.nn.functional.cross_entropy(log,y,reduction='sum'));nll_sum+=loss;target_count+=len(y)
   end=case['tokens'][-256:];end_logits=model(torch.tensor([end],dtype=torch.long))[0,-1];eos_p=float(torch.softmax(end_logits,dim=-1)[2]);g=greedy(model,case['prefix'],pieces,max_new=128)
   rows.append(dict(id=case['id'],source_url=case['source_url'],source_text_sha256=case['text_sha256'],prefix_tokens=case['prefix'],prefix_bytes_hex=b''.join(pieces[t]for t in case['prefix']if t>=6).hex(),NLL=loss/len(y),teacher_targets=len(y),EOS_probability_at_source_answer_end=eos_p,**g));print(args.arm,case['id'],'eos',g['eos'],flush=True)
 summary=dict(checkpoint=plan['checkpoints'][args.arm],cursor=cursor,NLL=nll_sum/target_count,teacher_targets=target_count,cases=len(rows),EOS=sum(r['eos']for r in rows),repeat4=sum(r['repeated4gram']is not None for r in rows),seconds=time.time()-start,optimizer_updates=0,semantic_success='Requires full reading; not inferred from NLL/EOS',independent_human_evaluation=False,protocol_sha256=hashlib.sha256((D/'NEW_PROSE_DEV_PROTOCOL.json').read_bytes()).hexdigest())
 pending=out.with_suffix('.pending');pending.write_text(json.dumps(dict(summary=summary,cases=rows),ensure_ascii=False,indent=2)+'\n');pending.replace(out);print(summary,flush=True)
if __name__=='__main__':main()
