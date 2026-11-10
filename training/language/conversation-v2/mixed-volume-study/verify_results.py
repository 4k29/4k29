"""Saved artifacts, exact raw outputs and immutable inputs only; no model imports."""
import json,pathlib,hashlib,gzip
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3];V=P.parent
load=lambda f:json.loads(f.read_text())
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as q:
  for b in iter(lambda:q.read(1024**2),b''):h.update(b)
 return h.hexdigest()
plan=load(P/'PLAN.json')
for f,h in plan['sha256'].items():assert sha(ROOT/f)==h,f
assert sha(P/'PLAN.json')==(P/'PLAN.sha256').read_text().split()[0]
for n in [4,205,401]:
 base=P/f'artifacts/VOLUME-{n}';m=load(base/'checkpoint.json');h=hashlib.sha256()
 for c in m['chunks']:
  f=base/c['path'];assert sha(f)==c['sha256']
  with f.open('rb') as q:
   for b in iter(lambda:q.read(1024**2),b''):h.update(b)
 assert h.hexdigest()==m['sha256'];proof=load(P/f'GIT_RESTORE-{n}.json');assert proof['passed'] and proof['sha256']==m['sha256']
pieces=[bytes.fromhex(x) for x in load(V/'data/tokenizer.json')['bytes']];base=load(V/'mixed-retention-study/evaluation/terminal-MIX.json');by={(c['panel'],c['id']):c for c in base['cases']};nrows=nturns=0
for n in ['midpoint-800k','terminal-1M']:
 x=load(P/'evaluation'/f'{n}.json');assert len(x['cases'])==149;nrows+=149
 for c in x['cases']:assert c['prefix']==by[(c['panel'],c['id'])]['prefix'] and c['maxNewTokens']==by[(c['panel'],c['id'])]['maxNewTokens']
 ts=[t for e in x['self_history'] for t in e['turns']];nturns+=len(ts)
 for c in x['cases']+ts:
  if c.get('unsupported_full_history'):continue
  assert all(0<=t<3997 for t in c['prefix']+c['tokensIncludingEos']);assert len(c['prefix'])+len(c['nonEosTokens'])<=256;assert c['eos']==(c['tokensIncludingEos'][-1]==2)
  assert b''.join(pieces[t] for t in c['nonEosTokens'] if t>5).hex()==c['rawBytesHex']
  if c['strictUtf8']:assert bytes.fromhex(c['rawBytesHex']).decode('utf8')==c['text']
 r=load(P/'evaluation'/f'{n}-READING.json');assert r['required_single_prompt_cases']==129 and r['independent_native_human_evaluation']==False
assert load(P/'RESULTS.json')['baseline_body_NLL_max_difference_from_saved_PR108']==0
res=dict(passed=True,frozen_SHA_inputs=len(plan['sha256']),checkpoint_cold_restores=[4,205,401],raw_single_prompt_outputs=nrows,raw_self_history_turns=nturns,all149_prefixes_and_budgets_equal_PR108=True,all_raw_token_bytes_consistent=True,verification_model_forwards=0,verification_optimizer_calls=0)
(P/'FINAL_VERIFICATION.json').write_text(json.dumps(res,indent=2)+'\n');print(res)
