"""No model forward: verify retained/discarded/replay ledgers and published evidence."""
import pathlib,json,hashlib,collections
P=pathlib.Path(__file__).resolve().parent
read=lambda n:json.loads((P/n).read_text())
rows=[json.loads(s)for s in (P/'UPDATES.jsonl').read_text().splitlines()];actual=[r for r in rows if r['event']=='returned'];assert len(actual)==40 and len(rows)==80
assert collections.Counter(r['phase']for r in actual)=={'pilot-retained':34,'preflight-original':4,'preflight-replay':2}
d=read('DATA.json');plan=read('PLAN.json');assert len(d['batch_order'])==17
for arm in ['A','B']:
 tr=[r['trace']for r in actual if r['arm']==arm and r['phase']=='pilot-retained'];assert [r['step']for r in tr]==list(range(1,18));ids=sum([r['ids']for r in tr],[]);assert len(ids)==len(set(ids))==66
 assert sum(r['input_tokens']for r in tr)==4880;assert sum(r['active_teachers']for r in tr)==(4880 if arm=='A'else 2124)
 for n in [9,17]:
  cold=read(f'COLD-{arm}-{n}.json');manifest=read(f'artifacts/{arm}-PILOT{n}/checkpoint.json');assert cold['passed']and cold['remote_only_no_alternates'];assert cold['sha256']==manifest['sha256'];assert manifest['cursor']==n and manifest['Adam_steps']==[6940+n];assert manifest['plan_sha256']==hashlib.sha256((P/'PLAN.json').read_bytes()).hexdigest()
 result=read(f'evaluation/{arm}-pilot17.json');assert len(result['cases'])==144 and len(result['self_history'])==4;assert result['whole_vocabulary_greedy']and result['raw_unmodified'];assert len(result['NLL'])==81
 reading=read(f'evaluation/{arm}-pilot17-READING.json');assert len(reading['rows'])==144;assert reading['source_sha256']==hashlib.sha256((P/f'evaluation/{arm}-pilot17.json').read_bytes()).hexdigest()
 assert all('rawBytesHex'in r and 'tokensIncludingEos'in r for r in result['cases'])
f=[json.loads(l)for l in (P/'FORWARDS.jsonl').read_text().splitlines()];a=read('RESULT.json');assert a['model_forward_returns']==sum(r['event']=='returned'for r in f)==sum(r['event']=='intent'for r in f);assert a['passed']and a['source_unchanged'];assert a['actual_optimizer_returns']==40;assert read('PREFLIGHT.json')['passed'];assert read('DATA_REPRO_RECEIPT.json')['passed']
print(json.dumps(dict(passed=True,actual_optimizer_calls=40,retained=34,discarded=4,replay=2,complete_cold_states=4,terminal_raw_generations=288,terminal_self_episodes=8,additional_optimizer_calls=0,additional_forwards=0)))
