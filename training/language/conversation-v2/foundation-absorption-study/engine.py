"""Fixed one-pass extra LM, then matched fresh-Adam response CE. Research only."""
import pathlib,sys,json,gzip,copy,hashlib,os,math,time,subprocess,resource,io,random
P=pathlib.Path(__file__).resolve().parent;V=P.parent;ROOT=V.parents[2];W=ROOT/'scratch-absorption';W.mkdir(exist_ok=True)
sys.path.insert(0,str(V/'modern-corpus'));from next_runtime import torch,restore_isolated,trajectory,digest,save,record,causal_ce,clip_grad_accurate,pack,extra_rng,restore_extra_rng,read,write
sys.path.insert(0,str(V/'foundation-stage'));from runtime import loader
from prose_decode import greedy
sys.path.insert(0,str(V));from core import decoder
SOURCE='fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7';phase='setup'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def integrity(x):return digest({k:v for k,v in x.items()if k!='integrity'})
def init_data():
 global corpus,schedule,faq,prose,plan
 corpus=[json.loads(x)for x in gzip.decompress((P/'corpus.jsonl.gz').read_bytes()).splitlines()];schedule=read(P/'SCHEDULE.json')['batches'];faq=read(V/'faq-ce-verified-study/DATA.json');prose=read(P/'PROSE_DEV.json')['cases'];plan=read(P/'PLAN.json')
def track(m):
 old=m.forward
 def forward(*a,**kw):
  record(P/'FORWARDS.jsonl',dict(event='intent',phase=phase,shape=list(a[0].shape)));v=old(*a,**kw);record(P/'FORWARDS.jsonl',dict(event='returned',phase=phase));return v
 m.forward=forward;return m

def source():
 p=V/'mixed-retention-study/artifacts/MIX-579/checkpoint.json';assert read(p)['sha256']==SOURCE;obj=loader.load_checkpoint(p,SOURCE);assert obj['integrity']==integrity(obj);assert obj['active_cursor']==579;assert sum(x['targets']for x in obj['trace'])==590144;return obj

def starting(base,tag):
 m,o,r=restore_isolated(base['trajectory']);restore_extra_rng(base['extra_rng'])
 assert next(iter(o.state.values()))['exp_avg'].data_ptr()!=next(iter(base['trajectory']['optimizer']['state'].values()))['exp_avg'].data_ptr()
 if tag=='LM':
  for g in o.param_groups:g['lr']=3e-5
  assert {int(v['step'])for v in o.state.values()}=={6940}
 else:
  import numpy as np
  o=torch.optim.AdamW(m.parameters(),lr=1e-5,betas=(.9,.999),eps=1e-8,weight_decay=.05);torch.manual_seed(20261114);random.seed(20261114);np.random.seed(20261114);r=random.Random(20261114);assert not o.state
 m.train();return track(m),o,r

def batch(tag,i):
 if tag=='LM':
  refs=schedule[i];rows=[dict(tokens=corpus[z['record']]['tokens'][z['input_start']:z['end']])for z in refs];x,y=pack(rows)
  for j,z in enumerate(refs):y[j,:z['target_start']-z['input_start']-1]=-100
  ids=[corpus[z['record']]['id']for z in refs]
 else:
  rows=[faq['parts']['train'][k]for k in faq['batch_order'][i]];x,y=pack(rows)
  for j,z in enumerate(rows):y[j,:z['response_body_start']-1]=-100
  ids=[z['id']for z in rows]
 assert y.ne(-100).any();return x,y,ids

def state(m,o,r,tag,cursor,tr,base):
 n=len(schedule)if tag=='LM'else 93
 obj=dict(trajectory=trajectory(m,o,r,list(range(n)),cursor,[],base['trajectory']['uniqueUpdates']+cursor),extra_rng=extra_rng(),sampler=dict(tag=tag,cursor=cursor,order=list(range(n)),schedule_sha256=sha(P/'SCHEDULE.json')if tag=='LM'else sha(V/'faq-ce-verified-study/DATA.json')),initial_sha256=SOURCE,parent_integrity=base['integrity'],arm=tag,active_cursor=cursor,trace=copy.deepcopy(tr),plan_sha256=sha(P/'PLAN.json'));obj['integrity']=integrity(obj);return obj

def step(m,o,r,tag,i,label,tr):
 global phase
 phase=label+'-'+tag;rng_before=digest(torch.get_rng_state());x,y,ids=batch(tag,i);m.train();o.zero_grad(set_to_none=True);o.param_groups[0]['lr']=3e-5 if tag=='LM'else 1e-5
 assert tuple(o.param_groups[0]['betas'])==(.9,.999)and o.param_groups[0]['eps']==1e-8 and o.param_groups[0]['weight_decay']==.05
 captured=[]
 def hook(mod,inp,out):out.retain_grad();captured.append(out)
 h=m.token.register_forward_hook(hook)if i==0 and tag!='LM'else None
 logits=m(x);logits.retain_grad()if i==0 else None;loss=causal_ce(logits,y);loss.backward()
 if h:h.remove()
 activation=None
 if h:
  gq=captured[0].grad;rows=[faq['parts']['train'][k]for k in faq['batch_order'][i]];qs=sum(float(gq[j,2:z['response_body_start']-2].double().square().sum())for j,z in enumerate(rows));assert qs>0;activation=dict(question_gradient_L2=qs**.5,semantic_understanding_proven=False)
 norm=clip_grad_accurate(m.parameters(),1.0);g=float(norm['norm'])if isinstance(norm,dict)else float(norm)
 # Existing accurate clipping returns a structured receipt in this own stack.
 if i==0:assert float(logits.grad[y.eq(-100)].abs().sum())==0
 before=[z.detach().clone()for z in m.parameters()]if i in[0,(len(schedule)//2 if tag=='LM'else 46),(len(schedule)-1 if tag=='LM'else 92)]else None
 record(P/'UPDATES.jsonl',dict(event='intent',phase=label,tag=tag,step=i+1));record(P/'OPTIMIZER_CALLS.jsonl',dict(event='intent',phase=label,tag=tag,step=i+1));o.step();record(P/'OPTIMIZER_CALLS.jsonl',dict(event='returned',phase=label,tag=tag,step=i+1))
 assert all(torch.isfinite(z).all()for z in m.parameters());assert all(torch.isfinite(t).all()for st in o.state.values()for t in st.values()if isinstance(t,torch.Tensor));adam=sorted({int(z['step'])for z in o.state.values()});assert adam==[(6940 if tag=='LM'else 0)+i+1]
 delta=math.sqrt(sum(float((z.detach().double()-a.double()).square().sum())for z,a in zip(m.parameters(),before)))if before else None
 t=dict(step=i+1,torch_rng_before_sha256=rng_before,activation_audit=activation,loss=float(loss),gradient_norm=g,clipped=g>1.0,active_teachers=int(y.ne(-100).sum()),input_nonPAD=int(x.ne(0).sum()),IDs=ids,Adam_step=adam[0],LR=o.param_groups[0]['lr'],weight_delta_L2=delta,mask_sha256=hashlib.sha256(y.ne(-100).numpy().tobytes()).hexdigest());tr.append(t);record(P/'UPDATES.jsonl',dict(event='returned',phase=label,tag=tag,trace=t));o.zero_grad(set_to_none=True)

def publish(msg):
 subprocess.run(['git','add',str(P.relative_to(ROOT))],cwd=ROOT,check=True)
 if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:
  subprocess.run(['git','-c','user.name=github-actions[bot]','-c','user.email=41898282+github-actions[bot]@users.noreply.github.com','commit','-m',msg+' [skip ci]'],cwd=ROOT,check=True);subprocess.run(['git','push','origin','HEAD:research/foundation-absorption-study'],cwd=ROOT,check=True)
 return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

def archive(obj,tag,n):
 path=W/f'{tag}-{n}.pt';save(path,obj);assert integrity(torch.load(path,weights_only=False))==obj['integrity'];folder=P/'artifacts'/f'{tag}-{n}';folder.mkdir(parents=True);parts=[]
 with path.open('rb')as f:
  for i,b in enumerate(iter(lambda:f.read(32*1024**2),b'')):
   q=folder/f'part-{i:03d}.bin';q.write_bytes(b);parts.append(dict(path=q.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
 manifest=dict(sha256=sha(path),bytes=path.stat().st_size,chunks=parts,tag=tag,cursor=n,Adam_steps=sorted({int(x['step'])for x in obj['trajectory']['optimizer']['state'].values()}),integrity=obj['integrity'],plan_sha256=sha(P/'PLAN.json'),formal_adoption=False);write(folder/'checkpoint.json',manifest);commit=publish(f'Archive absorption {tag}-{n} complete state')
 bare=W/f'cold-{tag}-{n}';subprocess.run(['git','init','--bare','-q',str(bare)],check=True)
 def git(*a):return subprocess.check_output(['git','--git-dir',str(bare),*a])
 git('remote','add','origin','https://github.com/4k29/4k29.git');git('config','remote.origin.promisor','true');git('config','remote.origin.partialclonefilter','blob:none');git('fetch','--depth=1','--filter=blob:none','origin',commit);buf=io.BytesIO()
 for z in parts:
  b=git('show',commit+':'+str((folder/z['path']).relative_to(ROOT)));assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'];buf.write(b)
 assert hashlib.sha256(buf.getvalue()).hexdigest()==manifest['sha256'];buf.seek(0);cold=torch.load(buf,weights_only=False);assert digest(cold)==digest(obj);write(P/f'COLD-{tag}-{n}.json',dict(passed=True,source_commit=commit,sha256=manifest['sha256'],all_state_equal=True,remote_only_no_alternates=True,optimizer_calls=0,forwards=0));publish(f'Confirm absorption {tag}-{n} Git-only cold restore');return path

def preflight(base,tag):
 m,o,r=starting(base,tag);tr=[];initial=dict(optimizer_sha=digest(o.state_dict()),torch_RNG_sha=digest(torch.get_rng_state()),extra_RNG_sha=digest(extra_rng()),private_RNG_sha=digest(r.getstate()),initial_Adam_steps=sorted({int(z['step'])for z in o.state.values()}));step(m,o,r,tag,0,'discarded-original',tr);obj=state(m,o,r,tag,1,tr,base);save(W/f'preflight-{tag}.pt',obj);step(m,o,r,tag,1,'discarded-original',tr);expected=state(m,o,r,tag,2,tr,base);subprocess.run([sys.executable,str(P/'engine.py'),'replay',tag],check=True);proof=read(P/f'REPLAY-{tag}.json');assert proof['integrity']==expected['integrity'];write(P/f'PREFLIGHT-{tag}.json',dict(passed=True,initial=initial,update_resume_exact=True,Adam_storage_nonshared=True,discarded_original=2,replay=1,retained=0));publish('Verify real updated-state resume '+tag);return initial

def evaluate(obj,name,reuse=False,full=True):
 global phase
 phase='evaluation-'+name
 with torch.random.fork_rng():m=decoder(obj['trajectory']['config']);m.load_state_dict(obj['trajectory']['model'])
 track(m);m.eval();pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];cases=[];nll=[];prose_nll=[]
 with torch.inference_mode():
  for part,rs in faq['parts'].items():
   for row in rs:
    s=row['response_body_start'];t=row['tokens'];lp=m(torch.tensor([t[:-1]]))[0,s-1:].double().log_softmax(-1);gold=torch.tensor(t[s:]);ls=-lp[torch.arange(len(gold)),gold];nll.append(dict(id=row['id'],source=row['source'],partition=part,body_sum=float(ls[:-1].sum()),body_tokens=len(gold)-1,with_EOS_sum=float(ls.sum()),with_EOS_tokens=len(gold)))
  source_dev=None
  if full:
   if reuse:
    source_dev=read(V/'mixed-retention-study/NLL/mixed.json');assert source_dev['checkpoint_sha256']==SOURCE
   else:
    dv=json.load(gzip.open(V/'mixed-retention-study/DEV_BODY_NLL.json.gz','rt'));tot=__import__('collections').defaultdict(lambda:[0.,0]);detail=[]
    for i in range(0,len(dv),4):
     br=dv[i:i+4];xx,yy=pack(br);vv=m(xx)
     for j,z in enumerate(br):
      n=len(z['tokens'])-1;ls=torch.nn.functional.cross_entropy(vv[j,:n],yy[j,:n],reduction='none');mask=torch.tensor(z['body_mask']);value=float(ls[mask].sum());count=int(mask.sum());tot[z['source']][0]+=value;tot[z['source']][1]+=count;detail.append(dict(id=z['id'],source=z['source'],body_NLL_sum=value,body_targets=count))
    source_dev=dict(groups={k:dict(NLL=a/b,targets=b)for k,(a,b)in tot.items()},windows=detail,body_definition='IDs>5 except LF; same530 exposed windows; metric exclusions never suppress inference vocabulary',optimizer_calls=0)
  for row in prose:
   p=row['prefix'];gold=row['teacher_continuation'];lp=m(torch.tensor([p+gold[:-1]]))[0,len(p)-1:].double().log_softmax(-1);ls=-lp[torch.arange(len(gold)),torch.tensor(gold)];positions=[dict(token=g,nll=float(ls[i]),P_LF=float(lp[i,16].exp()),rank=int((lp[i]>lp[i,g]).sum())+1)for i,g in enumerate(gold)];prose_nll.append(dict(id=row['id'],source=row['source'],positions=positions,body_sum=sum(z['nll']for z in positions if z['token']>=6 and z['token']!=16),body_tokens=sum(z['token']>=6 and z['token']!=16 for z in positions)))
   if full:cases.append(dict(id=row['id'],panel='source-heldout-prose12',prefix=p,**greedy(m,p,pieces,gold=gold,max_new=row['maxNewTokens'])))
  episodes=[]
  if full:
   if reuse:
    old=V/'faq-ce-verified-study';prior=read(old/'evaluation/initial.json');mix=read(V/'mixed-retention-study/evaluation/terminal-MIX.json');asdc=read(V/'public-dialogue-study/evaluation/initial.json');expected=read(old/'evaluation/A-study93.json')['cases'];by={x['id']:x for x in prior['cases']+mix['cases']+asdc['cases']}
    for x in expected:
     r=by[x['id']];assert r['prefix']==x['prefix']and r['maxNewTokens']==x['maxNewTokens'];rr=copy.deepcopy(r);rr['panel']=x['panel'];cases.append(rr)
    episodes=copy.deepcopy(mix['self_history']);reuse_note=dict(existing_cases=167,existing_self_episodes=4,new_forwards_for_reused_generations=0,only_A_base_common_model_SOURCE=SOURCE)
   else:
    expected=read(V/'faq-ce-verified-study/evaluation/A-study93.json')['cases']
    for row in expected:cases.append(dict(id=row['id'],panel=row['panel'],prefix=row['prefix'],**greedy(m,row['prefix'],pieces,max_new=row['maxNewTokens'])))
    from new_tokenizer import Encoder
    enc=Encoder(read(V/'data/tokenizer.json'));collapse=lambda ts:[t for i,t in enumerate(ts)if not(t==16 and i and ts[i-1]==16)]
    for row in read(V/'paragraph-foundation/panels/B-579.json')['self_history']:
     ids=collapse(row['prefix']);turns=[]
     for k in range(3):
      if len(ids)+24>256:turns.append(dict(unsupported_full_history=True));break
      g=greedy(m,ids,pieces,max_new=24);turns.append(dict(prefix=ids[:],**g));ids+=g['tokensIncludingEos']
      if not g['eos']:break
      if k<2:ids+=collapse([3]+enc(row['followups'][k])+[2,4])
     episodes.append(dict(id=row['id'],turns=turns))
    reuse_note=None
   for i in plan['train_generation_rows']:
    row=faq['parts']['train'][i];p=row['tokens'][:row['response_body_start']];cases.append(dict(id=row['id'],panel='train-absorption4',prefix=p,**greedy(m,p,pieces,max_new=256-len(p))))
  else:reuse_note=None
 write(P/f'evaluation/{name}.json',dict(name=name,cases=cases,NLL=nll,prose_NLL=prose_nll,source_dev_NLL=source_dev,self_history=episodes,reused=reuse_note,whole_vocabulary_greedy=True,raw_unmodified=True,independent_human_evaluation=False,optimizer_calls=0));publish('Save absorption evaluation '+name)

def main():
 global phase
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);init_data()
 for f,h in plan['sha256'].items():assert sha(ROOT/f)==h,f
 if len(sys.argv)>1 and sys.argv[1]=='replay':
  tag=sys.argv[2];b=torch.load(W/f'preflight-{tag}.pt',weights_only=False);assert integrity(b)==b['integrity'];m,o,r=restore_isolated(b['trajectory']);restore_extra_rng(b['extra_rng']);track(m);tr=copy.deepcopy(b['trace']);step(m,o,r,tag,1,'resume-replay',tr);out=state(m,o,r,tag,2,tr,dict(trajectory=dict(uniqueUpdates=b['trajectory']['uniqueUpdates']-1),integrity=b['parent_integrity']));write(P/f'REPLAY-{tag}.json',dict(integrity=out['integrity']));return
 assert not(P/'UPDATES.jsonl').exists(),'Never auto replay completed/ambiguous study';assert __import__('shutil').disk_usage(W).free>6*1024**3;src=source();original=digest(src);write(P/'RESOURCE.json',dict(CPU=os.cpu_count(),threads=torch.get_num_threads(),RAM=pathlib.Path('/proc/meminfo').read_text(),disk=__import__('shutil').disk_usage(W)._asdict(),GPU=torch.cuda.is_available(),run_id=os.environ.get('GITHUB_RUN_ID')))
 preflight(src,'LM');evaluate(src,'A-base',reuse=True);m,o,r=starting(src,'LM');tr=[];N=len(schedule)
 for i in range(N):
  assert __import__('shutil').disk_usage(W).free>2*1024**3;step(m,o,r,'LM',i,'retained',tr)
  if i+1 in [4,(N+1)//2,N]:
   b=state(m,o,r,'LM',i+1,tr,src);path=archive(b,'LM',i+1)
   if i+1==N:Bpath=path
   if i+1==(N+1)//2:evaluate(b,'B-LM-mid',full=False)
 assert digest(src)==original;del m,o,r,b;Bbase=torch.load(Bpath,weights_only=False);evaluate(Bbase,'B-base');initials={}
 for arm,base in [('A',src),('B',Bbase)]:
  tag='SFT-'+arm;initials[arm]=preflight(base,tag)
  if arm=='B':assert initials['A']==initials['B'],'SFT optimizer/RNG init differs; weights intentionally differ'
  m,o,r=starting(base,tag);tr=[]
  for i in range(93):
   step(m,o,r,tag,i,'retained',tr)
   if i+1 in[47,93]:
    obj=state(m,o,r,tag,i+1,tr,base);archive(obj,tag,i+1);evaluate(obj,tag+'-'+str(i+1),full=i+1==93)
  del m,o,r,obj
 assert digest(src)==original;u=[json.loads(x)for x in(P/'UPDATES.jsonl').read_text().splitlines()];f=[json.loads(x)for x in(P/'FORWARDS.jsonl').read_text().splitlines()];c=__import__('collections').Counter(x['phase']for x in u if x['event']=='returned');assert c=={'retained':N+186,'discarded-original':6,'resume-replay':3};assert sum(x['event']=='intent'for x in u)==len(u)//2;assert sum(x['event']=='intent'for x in f)==len(f)//2;write(P/'RESULT.json',dict(passed=True,retained_LM=N,retained_SFT_each=93,actual_optimizer_calls=len(u)//2,by_phase=dict(c),model_forwards=len(f)//2,seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_unchanged=True,raw_optimizer_return_calls=sum(json.loads(x)['event']=='returned'for x in(P/'OPTIMIZER_CALLS.jsonl').read_text().splitlines()),python=sys.version,torch=torch.__version__,SFT_optimizer_RNG_initialization_identical=initials['A']==initials['B']));publish('Complete foundation absorption experiment with actual ledgers')
if __name__=='__main__':
 started=time.monotonic()
 try:main()
 except Exception as e:
  write(P/'FAILURE.json',dict(error=repr(e),phase=phase,automatic_replay=False,raw_optimizer_return_calls=sum(json.loads(x)['event']=='returned'for x in(P/'OPTIMIZER_CALLS.jsonl').read_text().splitlines())if(P/'OPTIMIZER_CALLS.jsonl').exists()else 0));
  try:publish('Preserve absorption failure without automatic replay')
  except Exception:pass
  raise
