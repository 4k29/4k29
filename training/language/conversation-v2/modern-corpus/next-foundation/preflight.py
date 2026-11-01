"""Full own-model dynamic padding/gradient and resource audit; optimizer updates0.
Actual post-update resume validation is mandatory in each arm's first4 retained updates.
"""
import pathlib,sys,time,resource,shutil
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from next_runtime import *
from verify_caption_mix import main as verify_corpus

def main():
 plan=read(D/'PLAN.json');torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 for path,expected in plan['input_sha256'].items():assert sha(ROOT/path)==expected,path
 verify_corpus();assert read(D/'REBUILD_PROOF.json')['all_four_byte_exact'];corpus,schedule=load_data();model,opt,rng,base=starting('A');initial_rng=torch.get_rng_state().clone();base_digest=digest(base);weights_before=digest(model.state_dict());other,other_opt,other_rng,other_base=starting('B');same_rng=torch.equal(initial_rng,torch.get_rng_state());assert same_rng and not opt.state and not other_opt.state and opt is not other_opt;assert model.config==other.config and rng.getstate()==other_rng.getstate() and opt.state_dict()['param_groups']==other_opt.state_dict()['param_groups']
 ptrs={p.data_ptr()for p in model.parameters()};assert not ptrs&{p.data_ptr()for p in other.parameters()};del other,other_opt,other_base
 captions=[r for r in corpus if r['source']=='stair'];indices=[0,len(captions)//3,2*len(captions)//3,len(captions)-1];rows=[dict(tokens=captions[i]['tokens'])for i in indices];model.eval();model.zero_grad(set_to_none=True);x,y=legacy.pack(rows);log=model(x);loss=causal_ce(log,y);loss_old=float(loss.detach());live=[log[i,:len(r['tokens'])-1].detach().clone()for i,r in enumerate(rows)];loss.backward();grads=[p.grad.detach().clone()for p in model.parameters()];del log,loss;model.zero_grad(set_to_none=True)
 x,y=pack(rows);log=model(x);loss=causal_ce(log,y);loss_new=float(loss.detach());max_logit=max(float((log[i,:len(r['tokens'])-1]-live[i]).abs().max())for i,r in enumerate(rows));loss.backward();max_gradient=max(float((p.grad-g).abs().max())for p,g in zip(model.parameters(),grads));del grads,live,log,loss
 assert abs(loss_old-loss_new)<=2e-6 and max_logit<=2e-5 and max_gradient<=2e-5
 model.train();model.zero_grad(set_to_none=True);refs=max(schedule['batches'],key=lambda b:max(r['length']-1 for r in b)*len(b));x,y=pack(batch_windows(corpus,refs));t=time.monotonic();loss=causal_ce(model(x),y);assert torch.isfinite(loss);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1));assert math.isfinite(norm)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters());seconds=time.monotonic()-t;assert weights_before==digest(model.state_dict())and base_digest==digest(base);model.zero_grad(set_to_none=True)
 parameters=sum(p.numel()for p in model.parameters());state_budget=parameters*12+16*1024**2;free=shutil.disk_usage(D).free;required=5*state_budget+256*1024**2;assert free>=required,(free,required);rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;assert rss<6*1024**2
 receipt=dict(pass_all=True,plan_sha256=sha(D/'PLAN.json'),optimizer_updates=0,parameter_count=parameters,dynamic_padding_equivalence=dict(old_loss=loss_old,new_loss=loss_new,max_absolute_logit_error=max_logit,max_absolute_gradient_error=max_gradient,tolerances=dict(loss=2e-6,logits=2e-5,gradient=2e-5),scope='Eval-mode mathematical equivalence within FP32 rounding, not bit-exact old training dropout trajectory'),initial_dropout_rng_equal=same_rng,initial_Adam_states_empty_and_independent=True,source_base_unchanged=True,full_model_gradient_finite=True,gradient_norm_before_clip=norm,resource_probe=dict(rows=len(refs),width=x.shape[1],valid_targets=int(y.ne(-100).sum()),forward_backward_seconds=seconds,maximum_RSS_KiB=rss,free_bytes=free,required_peak_checkpoint_budget_bytes=required,checkpoint_budget_per_state_bytes=state_budget,scope='zero-update resource/gradient probe, not learning performance or language evidence'),actual_update_resume_validation='Pending: each arm must complete first4 and exact2-to4 separate-process replay before larger learning')
 write(D/'PREFLIGHT.json',receipt);print(receipt,flush=True)
if __name__=='__main__':main()
