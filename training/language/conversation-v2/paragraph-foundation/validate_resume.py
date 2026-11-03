"""Four diagnostic updates plus two replay calls on already-admitted old STAIR.
This is execution validation, not paragraph learning or a language success test.
"""
import pathlib,sys,json,gzip,copy,time,subprocess,resource,os,argparse,shutil
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(P.parent/'modern-corpus'))
from next_runtime import torch,read,write,sha,restore_isolated,trajectory,digest,extra_rng,restore_extra_rng,causal_ce,clip_grad_accurate,pack,save,record
DURABLE=pathlib.Path('/workspace/4k29')/P.relative_to(ROOT)/'private/validation'
JOURNAL=DURABLE/'actual-updates.jsonl'
def payload(model,opt,rng,base,cursor,trace):
 return dict(trajectory=trajectory(model,opt,rng,[0,1,2,3],cursor,[],base+cursor),extra_rng=extra_rng(),cursor=cursor,trace=trace,protocol_sha256=sha(P/'NUMERICAL_VALIDATION_PROTOCOL.json'))
def run(obj,rows,end,phase):
 s=obj['trajectory'];before=digest(s);model,opt,rng=restore_isolated(s);restore_extra_rng(obj['extra_rng']);trace=copy.deepcopy(obj.get('trace',[]));base=s['uniqueUpdates']-obj['cursor']
 for i in range(obj['cursor'],end):
  x,y=pack(rows[i*8:(i+1)*8]);model.train();opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1.));assert torch.isfinite(loss)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters())
  row=dict(step=i+1,loss=float(loss.detach()),targets=int(y.ne(-100).sum()),EOS_targets=int(y.eq(2).sum()),gradient_norm=norm,clipped=norm>1,lr=opt.param_groups[0]['lr']);assert row['lr']==1e-5
  record(JOURNAL,dict(event='intent',phase=phase,**row));opt.step();record(JOURNAL,dict(event='completed',phase=phase,**row));opt.zero_grad(set_to_none=True);trace.append(row)
  if phase=='validation-continuous'and i==1:
   assert shutil.disk_usage(DURABLE).free>2*135723997+256*1024**2
   save(DURABLE/'after2.pt',payload(model,opt,rng,base,i+1,trace))
 assert digest(s)==before
 return payload(model,opt,rng,base,end,trace)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--replay',action='store_true');args=parser.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);DURABLE.mkdir(parents=True,exist_ok=True)
 rows=read(P/'NUMERICAL_VALIDATION_INPUTS.json')['rows']
 if args.replay:
  obj=torch.load(DURABLE/'after2.pt',weights_only=False);assert obj['protocol_sha256']==sha(P/'NUMERICAL_VALIDATION_PROTOCOL.json');out=run(obj,rows,4,'validation-replay');write(P/'private/replay-digest.json',dict(digest=digest(out),trace=out['trace']));return
 assert not JOURNAL.exists(),'No implicit repeated optimizer calls'
 source=torch.load(P/'private/source-B-6361.pt',weights_only=False);obj=dict(trajectory=source['trajectory'],extra_rng=source['extra_rng'],cursor=0,trace=[]);started=time.monotonic();out=run(obj,rows,4,'validation-continuous');save(P/'private/validation-after4.pt',out)
 subprocess.run([sys.executable,str(pathlib.Path(__file__).resolve()),'--replay'],check=True);proof=read(P/'private/replay-digest.json');assert proof['digest']==digest(out)and proof['trace']==out['trace']
 events=[json.loads(l)for l in JOURNAL.read_text().splitlines()];assert sum(e['event']=='completed'for e in events)==6
 write(P/'UPDATE_RESUME_AUDIT.json',dict(pass_all=True,actual_optimizer_calls=6,continuous_validation_updates=4,replay_calls=2,comparative_learning_updates=0,trajectory_includes_model_adam_torch_private_python=True,extra_rng_sampler_cursor_trace_exact=True,separate_process_replay=True,replay_loaded_durable_after2=True,terminal_state_digest=digest(out),terminal_file_sha256=sha(P/'private/validation-after4.pt'),trace=out['trace'],seconds=time.monotonic()-started,max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
 (DURABLE/'after2.pt').unlink();print(json.dumps(read(P/'UPDATE_RESUME_AUDIT.json')))
if __name__=='__main__':main()
