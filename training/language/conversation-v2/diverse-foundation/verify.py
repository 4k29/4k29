"""Standard-library evidence verifier: frozen inputs, full checkpoint byte streams and raw generations."""
import pathlib,json,hashlib,subprocess,collections,sys
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3]
def read(p):return json.loads(p.read_text())
def data(p):return p.read_bytes()if p.exists()else subprocess.check_output(['git','show','HEAD:'+str(p.relative_to(ROOT))],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def verify():
 plan=read(D/'PLAN.json')
 for f,h in plan['input_sha256'].items():assert sha(data(ROOT/f))==h,f
 for r in read(D/'DEPENDENCIES.json'):assert sha(data(ROOT/r['path']))==r['sha256']
 if(D/'MANIFEST.json').exists():
  for r in read(D/'MANIFEST.json')['records']:
   raw=data(ROOT/r['path']);assert len(raw)==r['bytes']and sha(raw)==r['sha256'],r['path']
 states=[]
 for p in sorted(D.glob('**/archive*/checkpoint.json')):
  m=read(p);h=hashlib.sha256();total=0
  for c in m['chunks']:
   b=data(p.parent/c['path']);assert len(b)==c['bytes']and sha(b)==c['sha256'];assert len(b)<=32*1024**2;h.update(b);total+=len(b)
  assert total==m['bytes']and h.hexdigest()==m['sha256'];states.append(dict(manifest=str(p.relative_to(D)),cursor=m['active_cursor'],sha256=m['sha256']))
 expected={'health/archive/checkpoint.json'}|{f'run/{a}/archive-{n:05d}/checkpoint.json'for a in ['A','B']for n in [plan['comparison_updates'],plan['midpoint_updates'],plan['full_pass_updates']]}
 assert {r['manifest']for r in states}==expected,'All registered full-state milestones must be preserved'
 pieces=[bytes.fromhex(t)for t in read(D.parent/'data/tokenizer.json')['bytes']];ngen=0
 def case(c):
  nonlocal ngen
  if 'tokensIncludingEos'not in c:return
  t=c['tokensIncludingEos'];assert t and all(0<=x<len(pieces)for x in t);assert(c['eos'])==(t[-1]==2);assert 2 not in t[:-1];body=t[:-1]if c['eos']else t;raw=b''.join(pieces[x]for x in body);assert raw.hex()==c['rawBytesHex']
  try:text=raw.decode('utf8','strict')
  except UnicodeError:text=None
  assert text==c['text']and(c['strictUtf8'])==(text is not None);ngen+=1
 for folder in ['evaluation','sampling','daily-prose']:
  for p in sorted((D/folder).glob('*.json'))if(D/folder).exists()else[]:
   if p.name.endswith('-summary.json'):continue
   for c in read(p)['cases']:case(c)
 for p in sorted((D/'panels').glob('*.json'))if(D/'panels').exists()else[]:
  if p.name.endswith('-summary.json'):continue
  r=read(p)
  for k in ['prose_dev','legacy','grounded36','context12']:
   for c in r[k]:case(c)
  for e in r['self_history']:
   for c in e['turns']:case(c)
 for milestone in read(D/'health/evaluations.json'):
  for c in milestone['cases']:case(c)
 for p in sorted((D/'context-edge').glob('*.json')):
  for r in read(p)['rows']:case(r['edge_generation'])
 actual=0;retained=0;processed=0
 for arm in ['A','B']:
  p=D/'run'/arm/'updates.jsonl';events=[json.loads(l)for l in p.read_text().splitlines()];intent=[(r['phase'],r['step'])for r in events if r['event']=='intent'];done=[r for r in events if r['event']=='completed'];assert intent==[(r['phase'],r['step'])for r in done];steps=[r['step']for r in done if r['phase']=='retained'];assert steps==list(range(1,max(steps)+1));actual+=len(done);retained+=len(steps);processed+=sum(r['trace']['targets']for r in done);assert read(D/'run'/arm/'RESUME_AUDIT.json')['exact_model_adam_rng_sampler_cursor_trace_after_actual2_to4']
  receipt=read(D/'run'/arm/f"receipt-{plan['full_pass_updates']:05d}.json");assert len(steps)==receipt['retained_updates']==plan['full_pass_updates'];assert len(done)==receipt['actual_optimizer_calls']==plan['full_pass_updates']+2;assert sum(r['trace']['targets']for r in done if r['phase']=='retained')==receipt['retained_targets']==plan['full_pass_targets']
 health=read(D/'health/receipt.json');assert health['all_three_exact'];actual+=health['actual_optimizer_calls'];processed+=health['retained_targets'];published=subprocess.check_output(['git','ls-files',str(D.relative_to(ROOT))],cwd=ROOT,text=True).splitlines();assert not any('.raw.json'in p or '.private.'in p or p.endswith('/candidates.jsonl.gz')for p in published);assert read(D/'REBUILD_PROOF.json')['all_byte_exact'];assert read(D/'GIT_ARCHIVE_RESTORE_PROOF.json')['full_model_Adam_RNG_sampler_digest_equal']
 result=dict(pass_all=True,full_checkpoint_streams=states,raw_generation_instances_verified=ngen,actual_optimizer_calls_including_health=actual,main_retained_updates=retained,actual_processed_targets_including_replays_and_health=processed,source_and_schedule_rebuild_exact=True,sealed_TEST_used=False,independent_native_human_evaluation=False);(D/'VERIFY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result
if __name__=='__main__':verify()
