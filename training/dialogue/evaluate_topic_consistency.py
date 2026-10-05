"""Paired direct question/history diagnostics, never checkpoint selection."""
import argparse
import json
import pathlib

p=argparse.ArgumentParser()
p.add_argument('--review',required=True)
p.add_argument('--out',required=True)
args=p.parse_args()
review=json.loads(pathlib.Path(args.review).read_text())
rows={r['id']:r for r in review['rows']}
pairs=[]
for i in range(28):
    a,b=rows[f'switch-audit:{i}'],rows[f'switch-audit:{i+32}']
    assert a['question']==b['question'] and a['expected']==b['expected']
    assert not a['history'] and b['history']
    pairs.append(dict(question=a['question'],expected=a['expected'],standaloneId=a['id'],historyId=b['id'],
                      standaloneAnswer=a['answer'],historyAnswer=b['answer'],
                      standalonePass=a['passed'],historyPass=b['passed'],
                      standaloneExact=a['exact'],historyExact=b['exact'],
                      unchanged=a['answer']==b['answer']))
summary=dict(total=len(pairs),standalonePass=sum(r['standalonePass'] for r in pairs),
             historyPass=sum(r['historyPass'] for r in pairs),
             bothPass=sum(r['standalonePass'] and r['historyPass'] for r in pairs),
             passLostAfterHistory=sum(r['standalonePass'] and not r['historyPass'] for r in pairs),
             passGainedAfterHistory=sum(not r['standalonePass'] and r['historyPass'] for r in pairs),
             unchanged=sum(r['unchanged'] for r in pairs))
report=dict(version=review['version'],auditSha256=review['auditSha256'],summary=summary,
            scope='Same28 authored explicit questions, without history and after unrelated gold history. Descriptive paired diagnostic; no statistical independence, general dialogue or causal effect claim. Correct gold histories do not replace live rollouts.',rows=pairs)
pathlib.Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary))
