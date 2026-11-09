"""Check saved completed research receipts. No model forwards or updates."""
import pathlib,json,hashlib,gzip,collections,os
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3]
load=lambda f:json.loads(f.read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for name in ['PLAN.json','EVALUATION_PROTOCOL.json']:
 for rel,h in load(P/name)['sha256'].items():assert sha(ROOT/rel)==h,rel
ledger=[json.loads(l) for l in (P/'UPDATES.jsonl').read_text().splitlines()];intents=[r for r in ledger if r['event']=='intent'];done=[r for r in ledger if r['event']=='completed'];assert len(intents)==len(done)==583
assert [(r['phase'],r['trace']) for r in intents]==[(r['phase'],r['trace']) for r in done]
ret=[r['trace'] for r in done if r['phase']=='retained'];assert [r['step'] for r in ret]==list(range(1,580));assert sum(r['targets'] for r in ret)==590144
for n in [4,289,579]:
 base=P/f'artifacts/MIX-{n}';meta=load(base/'checkpoint.json');h=hashlib.sha256()
 for c in meta['chunks']:
  b=(base/c['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==c['sha256'];h.update(b)
 assert h.hexdigest()==meta['sha256'];proof=load(P/f'GIT_RESTORE-{n}.json');assert proof['passed'] and proof['sha256']==meta['sha256'] and proof['file_materialized_and_deserialized'] and proof['full_model_Adam_RNG_sampler_cursor_trace_integrity']
pieces=[bytes.fromhex(x) for x in load(P.parent/'data/tokenizer.json')['bytes']]
raw_total=turn_total=0
for name in ['midpoint-MIX','terminal-MIX']:
 x=load(P/'evaluation'/f'{name}.json');assert len(x['cases'])==149;raw_total+=149
 outputs=x['cases']+[t for e in x['self_history'] for t in e['turns']];turn_total+=len(outputs)-149
 for c in outputs:
  assert c['eos']==(c['tokensIncludingEos'][-1]==2)
  assert c['nonEosTokens']==[t for t in c['tokensIncludingEos'] if t!=2]
  assert all(0<=t<3997 for t in c['prefix']+c['tokensIncludingEos'])
  assert b''.join(pieces[t] for t in c['nonEosTokens'] if t>5).hex()==c['rawBytesHex']
  assert len(c['prefix'])+len(c['nonEosTokens'])<=256
 r=load(P/'evaluation'/f'{name}-READING.json');assert len([z for z in r['rows'] if z['decision']!='optional_unadjudicated'])==129
old=load(P.parent/'paragraph-foundation/evaluation/base-0-READING.json')['caption_judgments'];new=load(P/'terminal-MIX-CAPTION_DECISIONS.json');a={c['id'] for c in old if c['judgment']=='natural_short_text_only'};b={k for k,v in new.items() if v['decision']=='natural_short_text_only'}
receipt=dict(passed=True,frozen_plan_input_checks=len(load(P/'PLAN.json')['sha256']),frozen_evaluation_input_checks=len(load(P/'EVALUATION_PROTOCOL.json')['sha256']),retained_updates=579,actual_optimizer_calls=583,single_prompt_raw_outputs=raw_total,self_history_raw_turns=turn_total,raw_token_byte_checks=True,full_Git_restore_cursors=[4,289,579],caption_initial_natural=len(a),caption_terminal_natural=len(b),caption_same_cases_natural=len(a&b),caption_lost=sorted(a-b),caption_gained=sorted(b-a),verification_optimizer_calls=0,verification_model_forwards=0,storage_free_bytes={'workspace':os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize,'scratch':os.statvfs('/tmp').f_bavail*os.statvfs('/tmp').f_frsize})
(P/'FINAL_VERIFICATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False))
