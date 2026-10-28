"""Curate original human QA and a token/position-matched rehearsal comparison."""
import collections,gzip,hashlib,json,re
from runtime import H
def rank(s):return hashlib.sha256(('qa-matched-v1|'+s).encode()).hexdigest()
def main():
 source=json.loads((H/'qa-chunk-candidates.json').read_text());sample=json.loads((H/'qa-chunk-quality-sample.json').read_text());bad={sample[i]['id']for i in [11,18,19,30,44]};held=collections.Counter();clean={}
 for split,rows in source.items():
  good=[]
  for r in rows:
   context=r['context'];reason=None
   if r['id']in bad:reason='manual_ambiguity_or_missing_evidence'
   elif re.match(r'\s*(この|その|それ|同年|同時点)',context):reason='conservative_anaphora_guard'
   elif any(context.count(a)!=context.count(b)for a,b in [('「','」'),('『','』'),('（','）')]):reason='unbalanced_sentence_excerpt'
   elif any(q not in context and q not in r['title']for q in re.findall(r'「([^」]{2,})」',r['question'])):reason='quoted_question_anchor_missing'
   elif any(y not in context for y in re.findall(r'\d{3,4}年',r['question'])):reason='question_year_not_in_evidence'
   if reason:held[reason]+=1;continue
   assert context[r['normalized_answer_start']:r['normalized_answer_start']+len(r['answer'])]==r['answer'];good.append(r)
  clean[split]=good
 (H/'qa-data.json').write_text(json.dumps(clean,ensure_ascii=False,separators=(',',':'))+'\n')
 tr=clean['train'];steps=min(256,len(tr)//4);selected=tr[:4*steps]
 units=[r for r in map(json.loads,gzip.open(H/'data.jsonl.gz','rt'))if r['split']=='train'];units.sort(key=lambda r:rank(r['id']));used=set();batches=[]
 for i in range(steps):
  control=selected[4*i:4*i+4];treatment=control[:2]
  for q in control[2:]:
   L,T=len(q['prefix']),len(q['answer_ids']);u=next(r for r in units if r['id']not in used and len(r['tokens'])>=L+T);used.add(u['id']);off=int(rank(q['id'])[:8],16)%(len(u['tokens'])-L-T+1);seq=u['tokens'][off:off+L+T]
   treatment.append(dict(id='rehearsal:'+u['id']+':'+str(off),source_unit=u['id'],offset=off,prefix=seq[:L],answer_ids=seq[L:],answer_start=L,sequence=seq,authorship='original admitted prose target, no invented boundary'))
  assert [len(r['sequence'])for r in control]==[len(r['sequence'])for r in treatment]
  assert [len(r['answer_ids'])for r in control]==[len(r['answer_ids'])for r in treatment]
  batches.append(dict(control=control,treatment=treatment))
 with (H/'response-schedule.json.gz').open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:z.write(json.dumps(batches,ensure_ascii=False,separators=(',',':')).encode())
 review=dict(reviewer='main assistant, no independent human evaluation',all48_source_question_answer_triples_read=True,held_indices=[11,18,19,30,44],notes={'11':'黒化の機序と揮発性の質問が曖昧','18':'2017年という対象年が抜粋から欠落','19':'この時代が中生代である根拠が抜粋外','30':'作業指針の導入年が抜粋外','44':'9枚の窓と客用扉の回答が不整合'},offset_match_not_semantic_correctness=True,uncertain_cases_not_forced_to_pass=True)
 (H/'QA_QUALITY_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
 audit=dict(train_candidates_after_review=len(tr),dev_candidates=len(clean['dev']),manual_fixed_sample=48,held_by_reason=dict(held),comparison_updates_each=steps,unique_QA_control=len(selected),unique_QA_treatment=2*steps,unique_rehearsal_units=2*steps,actual_supervised_targets_each=sum(len(r['answer_ids'])for b in batches for r in b['control']),presented_targets_each=sum(len(r['sequence'])-1 for b in batches for r in b['control']),duplicate_QA_within_each_arm=0,question_answer_authorship='original human annotated span, program wrapper; factual world truth not exhaustively verified',training_authorized=False,reason='Require final foundation generation gate; then freeze inherited state/LR and separate plan before running',single_comparison_factor='data allocation: four QA versus two shared QA plus two prose continuations; same universal suffix CE mask and exact per-slot teacher/input lengths')
 (H/'RESPONSE_PREPARATION.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(audit)
if __name__=='__main__':main()
