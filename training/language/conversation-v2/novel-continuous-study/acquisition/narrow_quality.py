import os
import pathlib,json,gzip,re,hashlib,collections
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'));P=pathlib.Path(__file__).resolve().parents[1];q=json.loads((P/'FINAL_POOL_READING.json').read_text());a=[json.loads(x)for x in gzip.decompress((P/'new-pool-reviewed-by-machine.jsonl.gz').read_bytes()).splitlines()];out=[];held=collections.Counter();ids=[]
for r in a:
 why=None
 if r['source'].startswith('globalvoices'):
  article=int(r['id'].split(':')[1])
  if article in q['extra_hold_GV_article_ids']or re.search(q['GV_article_title_regex'],r['title']):why='GV_article_quality_scope'
  elif re.search(q['GV_paragraph_regex'],r['text']):why='GV_attributed_quote_or_missing_context'
 else:
  if r.get('pageid')in q['extra_hold_Wiki_pageids']or r['family']in q['extra_hold_Wiki_families']or('books'in r['source']and re.search(q['exclude_book_title_regex'],r['title'])):why='Wiki_quality_or_prior_course_family_scope'
 if re.search(q['whole_sensitive_regex'],r['text']):why='sensitive_or_non_target_history'
 if re.match(r'^(?:[）)、。]|は流体|このような|そのため|このため|それら|これら|前項|前述|この言葉|この国|つまり|もっとも|この地域)',r['text']):why='conservative_initial_context_hold'
 if why:held[why]+=1;ids.append(dict(id=r['id'],reason=why,text_SHA=r['text_SHA']));continue
 out.append(r)
(P/'narrowed-pool-private.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(r,ensure_ascii=False)for r in out)+'\n').encode(),mtime=0));(P/'NARROWING_AUDIT.json').write_text(json.dumps(dict(input_records=len(a),remaining_records=len(out),remaining_targets=sum(r['all_targets']for r in out),by_source={s:sum(r['all_targets']for r in out if r['source']==s)for s in sorted({r['source']for r in out})},held=dict(held),held_records=ids,criteria_before_optimizer=True),ensure_ascii=False,indent=2)+'\n');print('narrowed',len(out),sum(r['all_targets']for r in out),collections.Counter({s:sum(r['all_targets']for r in out if r['source']==s)for s in {r['source']for r in out}}))
# Targeted confirmation, only8GV+8Books, one per source/category/length stratum. No model yet.
sample=[]
for source in ['globalvoices_human_translation_new','jawikibooks_new']:
 bins=collections.defaultdict(list)
 for r in out:
  if r['source']==source:bins[(r['category'],len(r['tokens'])>256)].append(r)
 for key,rr in sorted(bins.items()):sample.append(min(rr,key=lambda r:hashlib.sha256(('post-narrowing-confirm-v1|'+r['id']).encode()).hexdigest()))
(C/'CONFIRMATION-private.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2));(P/'CONFIRMATION_LOCK.json').write_text(json.dumps(dict(seed='post-narrowing-confirm-v1',records=[dict(id=r['id'],text_SHA=r['text_SHA'],source=r['source'])for r in sample],optimizer_calls=0,model_forwards=0),ensure_ascii=False,indent=2)+'\n');print('confirmation',len(sample))
