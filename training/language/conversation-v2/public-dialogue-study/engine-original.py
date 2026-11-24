"""Isolated real-model CE pilot. Four one-pass updates/arm, no main study authorization."""
import pathlib,sys,json,hashlib,copy,os,math,time,subprocess,gzip,io,resource
P=pathlib.Path(__file__).resolve().parent;V=P.parent;ROOT=V.parents[2];W=ROOT/'scratch-response-learning';W.mkdir(exist_ok=True)
sys.path.insert(0,str(V/'modern-corpus'))
from next_runtime import torch,restore_isolated,trajectory,digest,save,record,causal_ce,clip_grad_accurate,pack,extra_rng,restore_extra_rng,read,write
sys.path.insert(0,str(V/'foundation-stage'));from runtime import loader
sys.path.insert(0,str(V));from core import decoder
from prose_decode import greedy
SOURCE='fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7'
phase='setup'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def integrity(x):return digest({k:v for k,v in x.items()if k!='integrity'})
def calls():
 rows=[json.loads(l)for l in (P/'UPDATES.jsonl').read_text().splitlines()]if(P/'UPDATES.jsonl').exists()else[]
 return dict(actual_optimizer_returns=sum(r['event']=='returned'for r in rows),intents=sum(r['event']=='intent'for r in rows),retained=sum(r['event']=='returned'and r['phase']=='pilot-retained'for r in rows),discarded_original=sum(r['event']=='returned'and r['phase']=='preflight-original'for r in rows),resume_replay=sum(r['event']=='returned'and r['phase']=='preflight-replay'for r in rows))
def track(m):
 old=m.forward
 def forward(*args,**kw):
  record(P/'FORWARDS.jsonl',dict(event='intent',phase=phase,batch=list(args[0].shape)))
  v=old(*args,**kw);record(P/'FORWARDS.jsonl',dict(event='returned',phase=phase));return v
 m.forward=forward
 return m

def source():
 manifest=V/'mixed-retention-study/artifacts/MIX-579/checkpoint.json';assert read(manifest)['sha256']==SOURCE
 src=loader.load_checkpoint(manifest,SOURCE);assert integrity(src)==src['integrity'];assert src['active_cursor']==579 and sum(r['targets']for r in src['trace'])==590144
 return src

def fresh(src):
 m,o,r=restore_isolated(src['trajectory']);restore_extra_rng(src['extra_rng']);assert {int(z['step'])for z in o.state.values()}=={6940}
 assert next(iter(o.state.values()))['exp_avg'].data_ptr()!=next(iter(src['trajectory']['optimizer']['state'].values()))['exp_avg'].data_ptr()
 return track(m),o,r

def payload(m,o,r,arm,cursor,tr):
 x=dict(trajectory=trajectory(m,o,r,list(range(4)),cursor,[],src['trajectory']['uniqueUpdates']+cursor),extra_rng=extra_rng(),sampler=dict(cursor=cursor,schedule_sha256=sha(P/'PILOT_DATA.json')),inherited_sampler=copy.deepcopy(src['sampler']),initial_sha256=SOURCE,arm=arm,active_cursor=cursor,trace=copy.deepcopy(tr),plan_sha256=sha(P/'PLAN.json'));x['integrity']=integrity(x);return x

def batch(i,arm):
 rows=[data['pilot_train'][j]for j in data['batch_order'][i]];x,y=pack(rows);yy=y.clone();mask=torch.zeros_like(y,dtype=torch.bool)
 for j,row in enumerate(rows):
  a=row['response_body_start']-1;n=len(row['tokens'])-1;mask[j,a:n]=True;assert row['tokens'][a]in[3,4]and row['tokens'][-1]==2
 if arm=='B':yy[~mask]=-100
 return x,y,yy,mask,rows

def step(m,o,r,arm,i,label,tr):
 global phase
 begin=time.monotonic();phase=label+'-'+arm;assert __import__('shutil').disk_usage(W).free>2*1024**3
 x,y,yy,mask,rows=batch(i,arm);m.train();o.zero_grad(set_to_none=True)
 for g in o.param_groups:
  assert tuple(g['betas'])==(.9,.999)and g['eps']==1e-8 and g['weight_decay']==.05;g['lr']=1e-5
 captured=[]
 def hook(mod,inp,out):out.retain_grad();captured.append(out)
 h=m.token.register_forward_hook(hook)if i==0 else None
 logits=m(x);logits.retain_grad();loss=causal_ce(logits,yy);loss.backward()
 if h:h.remove()
 norm=float(clip_grad_accurate(m.parameters(),1.));post=math.sqrt(sum(float(p.grad.detach().double().square().sum())for p in m.parameters()))
 assert math.isfinite(norm)and torch.isfinite(loss)and post<=1.00002 and all(p.grad is not None and torch.isfinite(p.grad).all()for p in m.parameters())
 outside=float(logits.grad[yy.eq(-100)].abs().sum());assert outside==0
 audit=None
 if i==0:
  g=captured[0].grad;his=sum(float(g[j,:row['response_body_start']-1].double().square().sum())for j,row in enumerate(rows));assert his>0
  qsum=0.0
  for j,row in enumerate(rows):
   prior=row['tokens'][:row['response_body_start']-1];role=max(k for k,t in enumerate(prior)if t in[3,4]);qsum+=float(g[j,role+1:row['response_body_start']-2].double().square().sum())
  assert qsum>0
  audit=dict(question_body_activation_gradient_L2=qsum**.5,history_embedding_activation_gradient_L2=his**.5,masked_out_logit_gradient_abs_sum=outside,history_tokens_remain_in_attention=True,semantic_context_understanding_proven=False,logit_SHA=digest(logits.detach()))
 before=[p.detach().clone()for p in m.parameters()]
 z=dict(step=i+1,loss=float(loss.detach()),input_tokens=int(y.ne(-100).sum()),active_teachers=int(yy.ne(-100).sum()),response_body_teachers=int((mask&(y>5)).sum()),response_EOS_teachers=int((mask&y.eq(2)).sum()),gradient_norm=norm,postclip_norm=post,clipped=norm>1,lr=1e-5,ids=[q['id']for q in rows],audit=audit)
 record(P/'UPDATES.jsonl',dict(event='intent',phase=label,arm=arm,trace=z));o.step();record(P/'UPDATES.jsonl',dict(event='returned',phase=label,arm=arm,trace=z))
 delta=math.sqrt(sum(float((p.detach().double()-v.double()).square().sum())for p,v in zip(m.parameters(),before)));assert math.isfinite(delta)and all(torch.isfinite(p).all()for p in m.parameters())
 assert all(torch.isfinite(t).all()for st in o.state.values()for t in st.values()if isinstance(t,torch.Tensor));assert {int(s['step'])for s in o.state.values()}=={6940+i+1}
 record(P/'UPDATE_DELTAS.jsonl',dict(phase=label,arm=arm,step=i+1,Adam_step=6940+i+1,delta_L2=delta,seconds=time.monotonic()-begin));o.zero_grad(set_to_none=True);tr.append(z)

def publish(msg):
 subprocess.run(['git','add',str(P.relative_to(ROOT))],cwd=ROOT,check=True)
 if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:
  subprocess.run(['git','-c','user.name=github-actions[bot]','-c','user.email=41898282+github-actions[bot]@users.noreply.github.com','commit','-m',msg+' [skip ci]'],cwd=ROOT,check=True)
  subprocess.run(['git','push','origin','HEAD:research/response-learning-pilot'],cwd=ROOT,check=True)
 return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

def archive(path,arm,n):
 folder=P/'artifacts'/f'{arm}-PILOT{n}';folder.mkdir(parents=True);parts=[]
 with path.open('rb')as f:
  for i,b in enumerate(iter(lambda:f.read(32*1024**2),b'')):
   name=f'part-{i:03d}.bin';(folder/name).write_bytes(b);parts.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
 obj=torch.load(path,weights_only=False);manifest=dict(sha256=sha(path),bytes=path.stat().st_size,chunks=parts,arm=arm,cursor=n,integrity=obj['integrity'],Adam_steps=sorted({int(s['step'])for s in obj['trajectory']['optimizer']['state'].values()}),plan_sha256=sha(P/'PLAN.json'),formal_adoption=False);write(folder/'checkpoint.json',manifest);commit=publish(f'Archive {arm} pilot{n} full state')
 bare=W/f'cold-{arm}-{n}';subprocess.run(['git','init','--bare','-q',str(bare)],check=True)
 def git(*args,**kw):return subprocess.check_output(['git','--git-dir',str(bare),*args],**kw)
 git('remote','add','origin','https://github.com/4k29/4k29.git');git('config','remote.origin.promisor','true');git('config','remote.origin.partialclonefilter','blob:none');git('fetch','--depth=1','--filter=blob:none','origin',commit)
 buf=io.BytesIO()
 for part in parts:
  b=git('show',commit+':'+str((folder/part['path']).relative_to(ROOT)));assert len(b)==part['bytes']and hashlib.sha256(b).hexdigest()==part['sha256'];buf.write(b)
 assert hashlib.sha256(buf.getvalue()).hexdigest()==manifest['sha256'];buf.seek(0);cold=torch.load(buf,weights_only=False);assert integrity(cold)==manifest['integrity'];assert digest(cold)==digest(obj)
 write(P/f'COLD-{arm}-{n}.json',dict(passed=True,source_commit=commit,sha256=manifest['sha256'],all_model_Adam_RNG_sampler_trace_equal=True,remote_only_no_alternates=True,optimizer_calls=0,model_forwards=0));publish(f'Verify remote-only cold state {arm}-{n}')

def evaluate(obj,name,legacy=False):
 global phase
 phase='evaluation-'+name
 with torch.random.fork_rng():m=decoder(obj['trajectory']['config']);m.load_state_dict(obj['trajectory']['model'])
 track(m);m.eval();pieces=[bytes.fromhex(t)for t in read(V/'data/tokenizer.json')['bytes']];result=[];nll=[]
 with torch.inference_mode():
  for part in ['pilot_train','dev']:
   for row in data[part]:
    t=row['tokens'];s=row['response_body_start'];logits=m(torch.tensor([t[:-1]]))[0,s-1:];target=torch.tensor(t[s:]);lp=logits.double().log_softmax(-1);loss=-lp[torch.arange(len(target)),target]
    nll.append(dict(id=row['id'],partition=part,body_sum=float(loss[:-1].sum()),body_tokens=len(target)-1,with_EOS_sum=float(loss.sum()),with_EOS_tokens=len(target)))
  for row in data['dev']:
   prefix=row['tokens'][:row['response_body_start']];assert len(prefix)+64<=256;result.append(dict(id=row['id'],panel='human-dev19',prefix=prefix,**greedy(m,prefix,pieces,max_new=64)))
  episodes=[]
  if legacy:
   old=V/'paragraph-foundation';panels=read(old/'panels/B-579.json');raw=read(old/'evaluation/B-579.json')
   collapse=lambda ts:[t for i,t in enumerate(ts)if not(t==16 and i and ts[i-1]==16)]
   for row in raw['cases']+panels['legacy']:
    if row['panel']in ['newJMA','train4','train-caption4']:continue
    prefix=collapse(row['prefix']);result.append(dict(id=row['id'],panel=row['panel'],prefix=prefix,**greedy(m,prefix,pieces,max_new=row['maxNewTokens'])))
   from new_tokenizer import Encoder
   enc=Encoder(read(V/'data/tokenizer.json'))
   for row in panels['self_history']:
    ids=collapse(row['prefix']);turns=[]
    for k in range(3):
     if len(ids)+24>256:turns.append(dict(unsupported_full_history=True));break
     g=greedy(m,ids,pieces,max_new=24);turns.append(dict(prefix=ids[:],**g));ids+=g['tokensIncludingEos']
     if not g['eos']:break
     if k<2:ids+=collapse([3]+enc(row['followups'][k])+[2,4])
    episodes.append(dict(id=row['id'],turns=turns))
 write(P/f'evaluation/{name}.json',dict(name=name,cases=result,self_history=episodes,NLL=nll,whole_vocabulary_greedy=True,raw_unmodified=True,semantic_scoring='main assistant separate; no human evaluation claim',optimizer_calls=0))

def replay(arm):
 obj=torch.load(W/f'preflight-{arm}.pt',weights_only=False);assert integrity(obj)==obj['integrity'];m,o,r=restore_isolated(obj['trajectory']);restore_extra_rng(obj['extra_rng']);track(m);tr=copy.deepcopy(obj['trace']);step(m,o,r,arm,1,'preflight-replay',tr);out=payload(m,o,r,arm,2,tr);write(P/f'REPLAY-{arm}.json',dict(integrity=out['integrity'],trace=tr))

def main():
 global src,data,phase
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);data=read(P/'PILOT_DATA.json');plan=read(P/'PLAN.json')
 for path,h in plan['sha256'].items():assert sha(ROOT/path)==h,path
 src=source();original=digest(src);assert __import__('shutil').disk_usage(W).free>3*1024**3
 if len(sys.argv)>1 and sys.argv[1]=='replay':replay(sys.argv[2]);return
 assert not(P/'UPDATES.jsonl').exists(),'Never repeat completed or ambiguous pilot'
 write(P/'SOURCE_STATE.json',dict(checkpoint_sha256=SOURCE,integrity=src['integrity'],initial_Adam_steps=sorted({int(s['step'])for s in src['trajectory']['optimizer']['state'].values()}),source_unique_updates=src['trajectory']['uniqueUpdates'],source_state_unchanged=True))
 evaluate(src,'initial',False)
 proofs={};first_logits={}
 for arm in ['A','B']:
  m,o,r=fresh(src);tr=[];step(m,o,r,arm,0,'preflight-original',tr);save(W/f'preflight-{arm}.pt',payload(m,o,r,arm,1,tr));step(m,o,r,arm,1,'preflight-original',tr);target=payload(m,o,r,arm,2,tr)
  subprocess.run([sys.executable,str(P/'engine.py'),'replay',arm],check=True);proof=read(P/f'REPLAY-{arm}.json');assert proof==dict(integrity=target['integrity'],trace=tr);assert digest(src)==original
  proofs[arm]=dict(passed=True,separate_process_full_state_resume_exact=True,Adam_storage_nonshared=True,first_update_audit=tr[0]['audit'],gradient_norm=tr[0]['gradient_norm'],postclip_norm=tr[0]['postclip_norm'],loss=tr[0]['loss'],active_teachers=tr[0]['active_teachers'],input_tokens=tr[0]['input_tokens']);first_logits[arm]=tr[0]['audit']['logit_SHA'];del m,o,r,target
 assert first_logits['A']==first_logits['B'],'Initial model/input/dropout diverged before mask'
 write(P/'PREFLIGHT.json',dict(passed=True,arms=proofs,initial_forward_identical=True,actual_optimizer_calls=6,discarded_original=4,replay=2,retained=0));publish('Complete real Transformer gradient and exact update-resume audit')
 for arm in ['A','B']:
  m,o,r=fresh(src);tr=[]
  for i in range(4):
   step(m,o,r,arm,i,'pilot-retained',tr)
   if i+1 in [2,4]:
    obj=payload(m,o,r,arm,i+1,tr);path=W/f'{arm}-PILOT{i+1}.pt';save(path,obj);assert integrity(torch.load(path,weights_only=False))==obj['integrity'];archive(path,arm,i+1)
    if i==1:
     del m,o,r;m,o,r=restore_isolated(obj['trajectory']);restore_extra_rng(obj['extra_rng']);track(m)
  evaluate(obj,arm+'-pilot4',True);assert digest(src)==original;publish(f'Save {arm} four-update pilot raw evaluation');del m,o,r,obj
 c=calls();assert c==dict(actual_optimizer_returns=14,intents=14,retained=8,discarded_original=4,resume_replay=2)
 f=[json.loads(l)for l in (P/'FORWARDS.jsonl').read_text().splitlines()];assert sum(r['event']=='intent'for r in f)==sum(r['event']=='returned'for r in f)
 write(P/'RESULT.json',dict(passed=True,purpose='pilot only, not main A/B or generalization proof',**c,model_forward_returns=sum(r['event']=='returned'for r in f),forward_by_phase={k:sum(r['event']=='returned'and r['phase']==k for r in f)for k in sorted({r['phase']for r in f})},source_unchanged=digest(src)==original,main_learning_updates=0,seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,python=sys.version,torch=torch.__version__))
 with (P/'FORWARDS.jsonl').open('rb')as f:(P/'FORWARDS.jsonl.gz').write_bytes(gzip.compress(f.read(),mtime=0))
 publish('Complete14 actual optimizer calls and fixed pilot evaluation')
if __name__=='__main__':
 started=time.monotonic()
 try:main()
 except Exception as exc:
  write(P/'FAILURE.json',dict(error_type=type(exc).__name__,error=str(exc),**calls(),automatic_replay=False));
  try:publish('Preserve failed pilot receipt without replay')
  except Exception:pass
  raise
