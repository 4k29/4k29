"""Read-only, separately frozen new DEV evaluation; optimizer never constructed."""
import pathlib,sys,json,hashlib,time,resource,os,shutil,platform
P=pathlib.Path(__file__).resolve().parent;V=P.parent;ROOT=V.parents[2]
sys.path.insert(0,str(V/'foundation-stage'));from runtime import torch,loader
sys.path.insert(0,str(V));from core import decoder,digest
from prose_decode import greedy
read=lambda p:json.loads(p.read_text());write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 start=time.monotonic();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);ground=read(P/'GROUNDED_DEV.json');new=read(P/'ADDITIONAL_DATA.json')['parts']['dev'];pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];allresults=[];counts={}
 for name,manifest in [('initial',V/'mixed-retention-study/artifacts/MIX-579/checkpoint.json'),('A-pilot4',P/'artifacts/A-PILOT4/checkpoint.json'),('B-pilot4',P/'artifacts/B-PILOT4/checkpoint.json')]:
  meta=read(manifest);state=loader.load_checkpoint(manifest,meta['sha256']);initial=digest(state);calls=0
  with torch.random.fork_rng():m=decoder(state['trajectory']['config']);m.load_state_dict(state['trajectory']['model'])
  m.eval();old=m.forward
  def counted(*args,**kwargs):
   nonlocal calls
   out=old(*args,**kwargs);calls+=1;return out
  m.forward=counted;rows=[];nll=[]
  with torch.inference_mode():
   for r in new:
    t=r['tokens'];s=r['response_body_start'];target=torch.tensor(t[s:]);lp=m(torch.tensor([t[:-1]]))[0,s-1:].double().log_softmax(-1);loss=-lp[torch.arange(len(target)),target];nll.append(dict(id=r['id'],body_sum=float(loss[:-1].sum()),body_tokens=len(target)-1,with_EOS_sum=float(loss.sum()),with_EOS_tokens=len(target)))
    prefix=t[:s];assert len(prefix)+32<=256;rows.append(dict(id=r['id'],panel='additional-human-dev6',prefix=prefix,**greedy(m,prefix,pieces,max_new=32)))
   for r in ground['rows']:
    assert len(r['prefix'])+32<=256;rows.append(dict(id=r['id'],panel='authored-grounded-dev7',prefix=r['prefix'],**greedy(m,r['prefix'],pieces,max_new=32)))
  assert digest(state)==initial;allresults.append(dict(model=name,checkpoint_sha256=meta['sha256'],cases=rows,NLL=nll,model_forward_returns=calls,state_unchanged=True));counts[name]=calls;del m,state
 write(P/'EXTRA_EVALUATION.json',dict(models=allresults,optimizer_calls=0,forward_returns=sum(counts.values()),forward_by_model=counts,grounded_dev_sha256=hashlib.sha256((P/'GROUNDED_DEV.json').read_bytes()).hexdigest(),additional_data_sha256=hashlib.sha256((P/'ADDITIONAL_DATA.json').read_bytes()).hexdigest(),greedy='unmodified all3997 vocabulary',torch=torch.__version__,python=sys.version,seconds=time.monotonic()-start,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,environment=dict(platform=platform.platform(),logical_cpu_count=os.cpu_count(),torch_threads=torch.get_num_threads(),RAM_bytes=os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES'),free_disk_bytes=shutil.disk_usage(ROOT).free,paid_resources=False)))
if __name__=='__main__':main()
