"""Record a strict manual review, separately from frozen exact-match scores.

Every non-exact answer requires explicit reviewed scores and an explanation.
This never changes gold labels or generated answers and does not train a model.
"""
import argparse
import collections
import hashlib
import json
import pathlib

HERE=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--stem',default='prefix-corrected');p.add_argument('--audit');p.add_argument('--policy');args=p.parse_args()
read=lambda suffix:json.loads((HERE/(args.stem+suffix)).read_text())
report=read('-audit-results.json');audit=json.loads(pathlib.Path(args.audit).read_text()) if args.audit else read('-audit.json');manual=read('-manual-review.json')
policy_path=pathlib.Path(args.policy) if args.policy else HERE/'prefix-review-policy.json'
policy=json.loads(policy_path.read_text())
names=list(policy['dimensions']);gold={r['id']:r for r in audit['rows']}
nonexact={r['id'] for r in report['rows'] if not r['exact']}
assert set(manual['answers'])==nonexact,'Every and only non-exact answer needs manual review'
assert report['sourceSha256']==audit['sourceSha256']
rows=[]
for r in report['rows']:
    assert r['expected']==gold[r['id']]['answer']
    review=manual['answers'].get(r['id'],dict(scores={name:2 for name in names},reason='Reviewed authored gold matches exactly.'))
    scores=review['scores'];assert set(scores)==set(names)
    assert all(type(v) is int and 0<=v<=2 for v in scores.values())
    assert isinstance(review['reason'],str) and review['reason'].strip()
    passed=all(v==2 for v in scores.values())
    assert not passed or (r['eos'] and r['validTokens']),'Invalid/incomplete generation cannot pass'
    rows.append(dict(id=r['id'],kind=r['kind'],question=r['question'],history=r['history'],expected=r['expected'],answer=r['answer'],exact=r['exact'],eos=r['eos'],validTokens=r['validTokens'],scores=scores,passed=passed,reason=review['reason']))
summary=dict(total=len(rows),exact=sum(r['exact'] for r in rows),passed=sum(r['passed'] for r in rows),semanticEquivalentNonExact=[r['id'] for r in rows if r['passed'] and not r['exact']],eos=sum(r['eos'] for r in rows),validTokens=sum(r['validTokens'] for r in rows),dimensionsFull={name:sum(r['scores'][name]==2 for r in rows) for name in names},byKind={kind:dict(total=sum(r['kind']==kind for r in rows),passed=sum(r['kind']==kind and r['passed'] for r in rows)) for kind in sorted({r['kind'] for r in rows})})
result=dict(version=report['version'],corpusSha256=report['training']['sourceSha256'],auditSha256=audit['sourceSha256'],policySha256=hashlib.sha256(policy_path.read_bytes()).hexdigest(),reviewer='Implementation assistant; not an independent human evaluation.',scope=policy['scope'],procedure=policy['procedure'],passingRule=policy['passingRule'],summary=summary,rows=rows)
(HERE/(args.stem+'-quality-review.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
