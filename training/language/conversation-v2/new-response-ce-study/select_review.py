"""Freeze source/partition/stratum sample before human semantic reading or model outputs."""
import pathlib,json,re,hashlib,collections
P=pathlib.Path(__file__).resolve().parent;rows=json.loads((P/'PRIVATE/CANDIDATES.json').read_text());seed='new-response-20261112-review-v1';patterns={'reason':'なぜ|どうして|理由','comparison':'比較|比べ|違い|どちら|どっち','condition':'条件|なら|場合|以内|以下|以上|含め|除い','procedure':'方法|手順|どうやって|どうすれば|作り方','provided_context':'以下|次の|この文章|これまで','other':'.'};selected=[];counts={}
for src in ['ichikara','instruction_ja']:
 for part,quota in [('train',8),('dev',2)]:
  seen=set();pool=[r for r in rows if r['source']==src and r['partition']==part and r['mechanically_eligible']];counts[src+':'+part]={}
  for tag,pat in patterns.items():
   candidates=sorted((r for r in pool if r['family']not in seen and re.search(pat,r['question'])),key=lambda r:hashlib.sha256((seed+'|'+src+'|'+part+'|'+tag+'|'+r['id']).encode()).hexdigest());take=candidates[:quota];counts[src+':'+part][tag]=len(take)
   for r in take:seen.add(r['family']);selected.append(dict(r,review_stratum=tag))
meta=[{k:r[k]for k in ['id','source','partition','family','question_sha256','answer_sha256','body_tokens','input_tokens','review_stratum']}for r in selected];(P/'REVIEW_PROTOCOL.json').write_text(json.dumps(dict(seed=seed,strata=patterns,train_quota_per_stratum=8,dev_quota_per_stratum=2,one_per_question_family=True,mechanical_selection_not_quality=True,source_authorship_separate=True,counts=counts,selection=meta,optimizer_calls=0,model_forwards=0,adoption_authorized=False),indent=2)+'\n');(P/'PRIVATE/REVIEW_CARDS.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n');print(counts);print('selected',len(selected))
