"""Matched eight-history comparisons; reuse all B logits, no optimizer creation."""
import gc,gzip,json,math,os,pathlib,subprocess,tempfile
from distribution_stats import P,V,ROOT,OUT,sha,read,write
ORIGIN='aa5d426ba9d550b74e9aa5348ca0ae6936565998'
def restore_file(folder):
 manifest=read(folder/'checkpoint.json');out=pathlib.Path(tempfile.gettempdir())/('read-only-'+folder.name+'.pt')
 h=__import__('hashlib').sha256()
 with out.open('wb')as f:
  for c in manifest['chunks']:
   rel=str((folder/c['path']).relative_to(ROOT))
   process=subprocess.Popen(['git','show','HEAD:'+rel],cwd=ROOT,stdout=subprocess.PIPE)
   ch=__import__('hashlib').sha256();n=0
   while b:=process.stdout.read(1048576):h.update(b);ch.update(b);n+=len(b);f.write(b)
   assert process.wait()==0 and n==c['bytes']and ch.hexdigest()==c['sha256']
 assert h.hexdigest()==manifest['sha256']and out.stat().st_size==manifest['bytes']
 out.chmod(0o444)
 return out,manifest
def summarize(values,gold,mata=3749,nl=16):
 maximum=max(values);w=[math.exp(v-maximum)for v in values];z=sum(w);prob=[v/z for v in w]
 def one(t):return dict(token=t,P=prob[t],rank=1+sum(x>values[t]for x in values))
 order=sorted(range(len(values)),key=lambda t:(-values[t],t))
 H=-sum(p*math.log(p)for p in prob if p)
 return dict(newline=one(nl),mata=one(mata),gold=one(gold),argmax=order[0],top5=[one(t)for t in order[:5]],entropy_nats=H,entropy_bits=H/math.log(2))
def main():
 import sys
 import torch
 import numpy as np
 sys.path.insert(0,str(V));import core
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 audit_file=P.parent/'newline-followup/EIGHT_CASE_AUDIT.json'
 audit=read(audit_file);cases=audit['cases'];assert len(cases)==8
 saved=P.parent/'newline-followup/top-candidates/LOGITS.json.gz'
 with gzip.open(saved,'rt')as f:B= json.load(f)
 assert len(B)==8
 for a,b in zip(cases,B):assert a['index']==b['index']and a['history_tokens']==b['input_tokens']
 references={
 'base-0':V/'modern-corpus/next-foundation/artifacts/B-6361',
 'A-579':P.parent/'artifacts/A-579',
 'B-579_numeric_control_only':P.parent/'artifacts/B-579'}
 expected={'base-0':'8109d11f80edba3e4ba6acbb513890db42c1b2fb8b612f79f5fc3d5d27c74e2e',
 'A-579':'725d362f5188867dfb33f97db358b9a956db532ecdd5dfe277a0daf47b9caeb2',
 'B-579_numeric_control_only':'3cebff9801302bd9969601e539adccaca7e0ea83943cc96bf2dc0b35f0906b9c'}
 watched=[audit_file,saved,P.parent/'PLAN.json',P.parent/'ACTUAL_UPDATES_A.jsonl',P.parent/'ACTUAL_UPDATES_B.jsonl',V/'data/tokenizer.json',V/'core.py',V.parent/'model.py']
 before={str(f.relative_to(ROOT)):sha(f)for f in watched}
 protocol=dict(fixed_before_inference=True,cases=8,origin_commit=ORIGIN,
  primary_additional_forwards=16,base=8,A=8,B_primary_forwards=0,
  additional_numeric_control_forward=1,
  control_reason='Managed executor failed to start; GitHub Actions uses pinned torch2.5.1 CPU. One B case verifies saved-logit numerical compatibility before reusing all8 B vectors. Does not prove every cross-runtime position identical.',
  control_max_logit_error=2e-4,control_max_probability_error=1e-5,
  saved_probability_reproduction_tolerance=1e-5,
  if_control_fails='Stop; do not silently rerun B or compare incompatible distributions.',
  input_contract='Exactly saved LF2 token IDs, default positions0..length-1, eval/dropout off, raw full3997-vocabulary logits, temperature1, FP64 softmax. No altered masks/positions/decoding.',
  checkpoints=expected,input_sha256=before,optimizer_updates=0,generation_runs=0,
  versions=dict(torch=torch.__version__,numpy=np.__version__),code_sha256=sha(__file__))
 write('PREDICTION_PROTOCOL.json',protocol)
 results={'B-579':[summarize(r['logits_FP32'],c['gold'])for r,c in zip(B,cases)]}
 archived={};calls=0;control=None
 # Check compatibility first, then obtain only the16 missing distributions.
 for name in ['B-579_numeric_control_only','base-0','A-579']:
  file,m=restore_file(references[name]);assert m['sha256']==expected[name]
  obj=torch.load(file,map_location='cpu',weights_only=False)
  if m.get('full_state_digest'):assert core.digest(obj)==m['full_state_digest']
  if m.get('trajectory_digest'):assert core.digest(obj['trajectory'])==m['trajectory_digest']
  with torch.random.fork_rng(devices=[]):model=core.decoder(obj['trajectory']['config'])
  model.load_state_dict(obj['trajectory']['model'],strict=True);model.eval();del obj
  before_model=core.digest(model.state_dict());values=[]
  with torch.inference_mode():
   for i,c in enumerate(cases[:1]if name.startswith('B-579')else cases):
    log=model(torch.tensor([c['history_tokens']],dtype=torch.long))[0,-1].tolist();calls+=1
    s=summarize(log,c['gold']);values.append(log)
    if name.startswith('B-579'):
     old=results['B-579'][0]
     control=dict(max_logit_error=max(abs(x-y)for x,y in zip(log,B[0]['logits_FP32'])),
      max_named_probability_error=max(abs(s[k]['P']-old[k]['P'])for k in ['newline','mata','gold']),argmax_same=s['argmax']==old['argmax'])
     assert control['max_logit_error']<=2e-4 and control['max_named_probability_error']<=1e-5 and control['argmax_same']
    else:
     previous=c['predictions'][name]
     assert abs(s['newline']['P']-previous['P_newline'])<=1e-5
     assert abs(s['gold']['P']-previous['P_gold'])<=1e-5
     assert s['argmax']==previous['argmax']
  assert core.digest(model.state_dict())==before_model and sha(file)==expected[name]
  if not name.startswith('B-579'):
   results[name]=[summarize(v,c['gold'])for v,c in zip(values,cases)]
   archived[name]=[dict(index=c['index'],input_tokens=c['history_tokens'],logits_FP32=v)for c,v in zip(cases,values)]
  del model,values;gc.collect()
 assert calls==17
 assert before=={str(f.relative_to(ROOT)):sha(f)for f in watched}
 outrows=[]
 for i,c in enumerate(cases):
  outrows.append(dict(index=i,source_id=c['source_id'],source_offset=c['source_offset'],gold=c['gold'],gold_piece_text=c['gold_piece_text'],
   input_tokens=c['history_tokens'],position_ids=list(range(len(c['history_tokens']))),
   conditions={k:results[k][i]for k in ['base-0','A-579','B-579']}))
 with (OUT/'NEW_COMPARISON_LOGITS.json.gz').open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,filename='')as z:z.write(json.dumps(archived,separators=(',',':')).encode())
 write('PREDICTIONS.json',dict(cases=outrows,summary={name:dict(
  mean_P_newline=sum(r['newline']['P']for r in rows)/8,mean_P_mata=sum(r['mata']['P']for r in rows)/8,
  mean_P_gold=sum(r['gold']['P']for r in rows)/8,mean_entropy_nats=sum(r['entropy_nats']for r in rows)/8,
  newline_argmax=sum(r['argmax']==16 for r in rows),mata_second=sum(r['mata']['rank']==2 for r in rows))
  for name,rows in results.items()},runtime_control=control,model_forward_calls=17,
  optimizer_updates=0,generation_runs=0,checkpoint_and_models_unchanged=True,
  B_logits_reused_from=str(saved.relative_to(ROOT)),new_logits_sha256=sha(OUT/'NEW_COMPARISON_LOGITS.json.gz'),
  CI_execution=dict(run_id=os.getenv('GITHUB_RUN_ID'),workflow_source_sha=os.getenv('GITHUB_SHA')),
  selection_bias='These8 are selected from actual B newline failures, not random contexts, DEV or population estimates.'))
 print('Additional next-token calls:',calls,'updates0; saved B8 reused; control:',control)
if __name__=='__main__':main()
