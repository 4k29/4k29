"""Record raw-text continuation fluency without an exact-match target."""
import argparse,hashlib,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--stem',required=True);args=p.parse_args()
root=pathlib.Path(__file__).resolve().parent
report=json.loads((root/(args.stem+'-raw-results.json')).read_text())
probes=json.loads((root/'switch-raw-probes.json').read_text())
assert report['sourceSha256']==probes['sourceSha256']
assert [r['id'] for r in report['rows']]==[r['id'] for r in probes['rows']]
for r,prompt in zip(report['rows'],probes['rows']):
    assert r['prefix']==prompt['prefix'] and r['textSha256']==prompt['textSha256']
manual=json.loads((root/(args.stem+'-raw-manual-review.json')).read_text())
assert set(manual['answers'])=={r['id'] for r in report['rows']}
rows=[]
for r in report['rows']:
    review=manual['answers'][r['id']];scores=review['scores']
    assert set(scores)=={'japanese','continuity'}
    assert all(type(v) is int and 0<=v<=2 for v in scores.values())
    assert review['reason'].strip()
    passed=r['validTokens'] and all(v==2 for v in scores.values())
    rows.append(dict(id=r['id'],prefix=r['prefix'],continuation=r['continuation'],validTokens=r['validTokens'],stop=r['stop'],scores=scores,passed=passed,reason=review['reason']))
result=dict(version=report['version'],sourceSha256=report['sourceSha256'],manualSha256=hashlib.sha256((root/(args.stem+'-raw-manual-review.json')).read_bytes()).hexdigest(),
    reviewer='Implementation assistant; not an independent human review.',
    policy='Evaluate joined seed+continuation. Japanese2 means a complete coherent Japanese continuation;1 means understandable but awkward/incomplete;0 means broken or meaningless. Continuity2 means meaningfully follows the seeded text;1 means loosely related;0 means contradicts, breaks or changes it. Both2 and valid tokens required. Source continuation is illustrative, not an exact target or test of factual accuracy. Eight fixed prompts only, not a general prose benchmark.',
    summary=dict(total=len(rows),passed=sum(r['passed'] for r in rows),validTokens=sum(r['validTokens'] for r in rows),japaneseFull=sum(r['scores']['japanese']==2 for r in rows),continuityFull=sum(r['scores']['continuity']==2 for r in rows)),rows=rows)
(root/(args.stem+'-raw-quality-review.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result['summary']))
