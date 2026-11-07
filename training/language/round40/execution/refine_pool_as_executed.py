"""Pre-update refinement after TRAIN text audit; never run on frozen trial."""
import json,pathlib,re,hashlib
R=pathlib.Path(__file__).resolve().parents[1];p=R/'execution/context-auxiliary-pool.json'
assert not (R/'source-manifest.json').exists() and not (R/'continue-10000/checkpoint.pt').exists()
j=json.loads(p.read_text());assert len(j['rows'])==1616
original=hashlib.sha256(p.read_bytes()).hexdigest();excluded={'大丈夫','気分的'};rows=[]
for r in j['rows']:
 anchors=(set(re.findall('[一-龯]{3,}',r['prefix'])) & set(re.findall('[一-龯]{3,}',r['target'])))-excluded
 if anchors and not any(a in r['wrongPrefix'] for a in anchors):r['anchors']=sorted(anchors);rows.append(r)
j.update(selection='Original deterministic1616 two-kanji candidate pairs filtered before any updates: shared maximal >=3-kanji run, excluding generic 大丈夫/気分的, absent from same-token-length donor. No model-score selection.',initialCandidatePoolSha256=original,initialCandidateCount=1616,genericAnchorsExcluded=sorted(excluded),rows=rows)
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');print('frozen training auxiliary pool',len(rows),'originaldocs',len(set(r['document'] for r in rows)))
policy=json.loads((R/'policy.json').read_text());policy['contextPreference']['poolSha256']=hashlib.sha256(p.read_bytes()).hexdigest();policy['contextPreference']['eligibility']=j['selection'];(R/'policy.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2)+'\n')
