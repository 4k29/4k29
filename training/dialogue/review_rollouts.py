"""Inspect actual generated-history turns independently of exact matching."""
import argparse,hashlib,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--stem',required=True);p.add_argument('--policy',required=True);p.add_argument('--corpus');args=p.parse_args()
root=pathlib.Path(__file__).resolve().parent
report=json.loads((root/(args.stem+'-rollout-results.json')).read_text())
corpus=json.loads((pathlib.Path(args.corpus) if args.corpus else root/'switch-rollouts.json').read_text())
assert report['sourceSha256']==corpus['sourceSha256']
assert [c['id'] for c in report['rows']]==[c['id'] for c in corpus['conversations']]
for actual,gold in zip(report['rows'],corpus['conversations']):
    assert len(actual['rows'])==len(gold['turns'])
    for r,t in zip(actual['rows'],gold['turns']):assert r['question']==t['question'] and r['expected']==t['answer']
manual=json.loads((root/(args.stem+'-rollout-manual-review.json')).read_text())
policy_path=pathlib.Path(args.policy);policy=json.loads(policy_path.read_text());names=list(policy['dimensions'])
nonexact={f'{c["id"]}:{i}' for c in report['rows'] for i,r in enumerate(c['rows']) if not r['exact']}
assert set(manual['answers'])==nonexact
rows=[]
for c in report['rows']:
    history=[];turns=[]
    for i,r in enumerate(c['rows']):
        identity=f'{c["id"]}:{i}'
        review=manual['answers'].get(identity,dict(scores={name:2 for name in names},reason='Reviewed authored gold matches exactly.'))
        scores=review['scores'];assert set(scores)==set(names)
        assert all(type(v) is int and 0<=v<=2 for v in scores.values());assert review['reason'].strip()
        passed=all(v==2 for v in scores.values())
        assert not passed or (r['eos'] and r['validTokens'])
        turns.append(dict(id=identity,history=history.copy(),question=r['question'],answer=r['answer'],expected=r['expected'],eos=r['eos'],validTokens=r['validTokens'],exact=r['exact'],scores=scores,passed=passed,reason=review['reason']))
        if r['eos'] and r['validTokens']:history.append(dict(question=r['question'],answer=r['answer']))
    rows.append(dict(id=c['id'],allPass=all(r['passed'] for r in turns),rows=turns))
turns=[r for c in rows for r in c['rows']]
summary=dict(conversations=len(rows),turns=len(turns),exact=sum(r['exact'] for r in turns),passed=sum(r['passed'] for r in turns),allPassConversations=sum(c['allPass'] for c in rows),equivalentNonExact=[r['id'] for r in turns if r['passed'] and not r['exact']])
result=dict(version=report['version'],sourceSha256=report['sourceSha256'],policySha256=hashlib.sha256(policy_path.read_bytes()).hexdigest(),reviewer='Implementation assistant; not an independent human review.',scope='Twelve frozen conversations, actual generated history; no gold replacement or corrected outputs. Finite authored test, not representative general dialogue.',summary=summary,rows=rows)
(root/(args.stem+'-rollout-quality-review.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary))
