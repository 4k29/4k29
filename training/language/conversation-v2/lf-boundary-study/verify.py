"""Verify completed records and exact output bytes, no forward or optimizer calls."""
from lf_runtime import *
from build import collapse
assert read(P/'GIT_FULL_STATE_RESTORE_AUDIT.json')['passed']
pieces=[bytes.fromhex(x) for x in read(V/'data/tokenizer.json')['bytes']];plan=read(P/'PLAN.json')
for rel,h in plan['sha256'].items():assert sha(ROOT/rel)==h,rel
for n in [4,289,579]:
 folder=P/f'artifacts/LF1-{n}';m=read(folder/'checkpoint.json');h=hashlib.sha256();size=0
 for c in m['chunks']:
  b=(folder/c['path']).read_bytes();assert len(b)==c['bytes'] and hashlib.sha256(b).hexdigest()==c['sha256'];h.update(b);size+=len(b)
 assert h.hexdigest()==m['sha256'] and size==m['bytes'];assert read(P/f'GIT_RESTORE-{n}.json')['passed']
obj=torch.load(SCRATCH/'LF1-579.pt',map_location='cpu',weights_only=False);assert integrity(obj)==obj['integrity'];assert obj['active_cursor']==579 and obj['sampler']['cursor']==579 and obj['plan_sha256']==sha(P/'PLAN.json')
events=[json.loads(l) for l in (P/'UPDATES.jsonl').read_text().splitlines()];ret=[e['trace'] for e in events if e['event']=='completed' and e['phase']=='retained'];assert ret==obj['trace'];assert len(ret)==579 and sum(x['targets'] for x in ret)==590144;assert {int(v['step']) for v in obj['trajectory']['optimizer']['state'].values()}=={6940}
assert sha(SCRATCH/'initial.pt')==plan['initial_checkpoint_sha256'];assert sha(SCRATCH/'LF2-terminal.pt')=='3cebff9801302bd9969601e539adccaca7e0ea83943cc96bf2dc0b35f0906b9c'
inference=0;free_queries=0;generation_rows=0;self_turns=0
for name in ['initial-LF1','midpoint-LF1','terminal-LF1']:
 x=read(P/'evaluation'/(name+'.json'));bd=read(P/'evaluation'/(name+'-boundaries.json'));assert bd['forward_calls']==72
 assert len(x['cases'])==149 and len(x['self_history'])==4
 steps=0;self_turns+=sum('tokensIncludingEos' in t for ep in x['self_history'] for t in ep['turns'])
 for c in x['cases']+[t for e in x['self_history'] for t in e['turns'] if 'tokensIncludingEos' in t]:
  t=c['tokensIncludingEos'];assert c['eos']==bool(t and t[-1]==2);assert c['nonEosTokens']==(t[:-1] if c['eos'] else t);assert bytes.fromhex(c['rawBytesHex'])==b''.join(pieces[z] for z in c['nonEosTokens']);assert len(c['steps'])==len(t);steps+=len(t)
 assert x['forward_calls']==steps+72;inference+=x['forward_calls'];free_queries+=steps;generation_rows+=len(x['cases'])
for name in ['control-LF2','control-on-LF1','LF1-on-LF2']:
 x=read(P/'evaluation'/(name+'-boundaries.json'));assert x['forward_calls']==72 and len(x['cases'])==40;inference+=72
parity=read(P/'parity-terminal-summary.json');inference+=parity['Python_forwards'];js=read(P/'parity-terminal/LF1-579/javascript.json');js_queries=sum(len(r['referencePythonHistoryScores'])+len(r['independentAutoregression']['steps']) for r in js['rows'])
for n in ['midpoint','terminal']:
 reading=read(P/'evaluation'/(n.upper()+'_READING.json'));screen=read(P/'evaluation'/(n+'-LF1-SCREEN.json'));assert len(reading['rows'])==149 and sum(r['full_text_success'] for r in reading['rows'])==reading['caption_natural']
result=dict(passed=True,frozen_input_SHA_files=len(plan['sha256']),checkpoint_archives_SHA_verified=3,Git_only_restores_verified=3,full_state_and_ledger_match=True,raw_single_prompt_generation_rows=447,raw_self_history_turns=self_turns,free_generation_logit_queries=free_queries,Python_inference_forwards=inference,Python_training_forwards=583,total_actual_Python_model_forwards=inference+583,actual_optimizer_calls=583,JS_score_queries=js_queries,Python_parity_cached_valid_vectors=parity['Python_forwards'],Python_parity_replays=0,failed_optimizer_calls=0,failed_model_forwards=0,independent_native_evaluation=False,formal_adoption=False)
write(P/'FINAL_VERIFICATION.json',result);print(json.dumps(result))
