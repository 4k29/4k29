"""Human JaQuAD questions/spans only; preparation does not authorize SFT updates."""
import collections,gzip,hashlib,json,pathlib,re,unicodedata
from runtime import H,V
from new_tokenizer import Encoder
def rank(s):return hashlib.sha256(('human-qa-followup-v1|'+s).encode()).hexdigest()
def main():
 enc=Encoder(json.loads((V/'data/tokenizer.json').read_text()));units=list(map(json.loads,gzip.open(H/'data.jsonl.gz','rt')));allowed={(r['provenance']['id'],o):r for r in units if r['source']=='jaquad'for o in r['paragraph_ordinals']};bad={c['questionId']for c in json.loads((V/'foundation-data/evaluation/quarantined-source-cases.json').read_text())['cases']};rows=[];counts=collections.Counter();seen=collections.Counter()
 for l in gzip.open(V/'foundation-data/corpus/documents.jsonl.gz','rt'):
  d=json.loads(l)
  if d['source']!='jaquad':continue
  for p in d['paragraphs']:
   unit=allowed.get((d['id'],p['ordinal']))
   if not unit:continue
   for q in sorted(p['qas'],key=lambda q:rank(q['id'])):
    if q['id']in bad:counts['known_annotation_error']+=1;continue
    if not q['answers']or seen[(d['id'],p['ordinal'])]>=2:continue
    if seen[d['id']]>=12:continue
    a=q['answers'][0];start=a['answer_start'];raw=a['text'];text=p['text'];norm=unicodedata.normalize('NFC',raw);question=q['question']
    if text[start:start+len(raw)]!=raw:counts['bad_original_offset']+=1;continue
    if not 2<=len(norm)<=40 or not re.search('何|誰|どこ|いつ|どの|どれ|いくつ|なぜ',question)or re.search('以外|でない|いない|正しくない',question):counts['scope']+=1;continue
    context=p['normalizedText'];offset=len(unicodedata.normalize('NFC',text[:start]));assert context[offset:offset+len(norm)]==norm
    prompt='資料の内容だけを使って質問に答えてください。\n資料：'+context+'\n質問：'+question;prefix=[1,3]+enc(prompt)+[2,4];ans=enc(norm)+[2]
    if len(prefix)>192 or len(prefix+ans)>257:counts['whole_context_does_not_fit']+=1;continue
    seen[(d['id'],p['ordinal'])]+=1;seen[d['id']]+=1;rows.append(dict(id=q['id'],split=unit['split'],component=unit['component'],document=d['id'],source_unit=unit['id'],title=d['title'],context=context,question=question,answer=norm,original_answer=raw,original_answer_start=start,normalized_answer_start=offset,prompt=prompt,prefix=prefix,answer_ids=ans,sequence=prefix+ans,answer_start=len(prefix),answer_type=a.get('answer_type'),question_type=q.get('question_type'),authorship='Publisher-declared human-written question and original human-annotated answer span; wrapper program-composed; not full authored assistant prose',license=d['license'],url=d['url']))
 rows.sort(key=lambda r:rank(r['id']));tr=[r for r in rows if r['split']=='train'];de=[r for r in rows if r['split']=='dev'];assert not{r['component']for r in tr}&{r['component']for r in de}
 (H/'qa-candidates.json').write_text(json.dumps(dict(train=tr,dev=de),ensure_ascii=False,separators=(',',':'))+'\n')
 (H/'QA_CANDIDATE_AUDIT.json').write_text(json.dumps(dict(train=len(tr),dev=len(de),train_documents=len({r['document']for r in tr}),held=dict(counts),source_context_already_used_in_foundation_not_new_independent_prose=True,status='pending semantic sample review; no SFT updates authorized',question_and_answer_authorship='human annotations declared by original publisher, correctness not proved by offsets'),indent=2)+'\n')
 sample=tr[:48];(H/'qa-quality-sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2)+'\n');print('QA candidates train/dev',len(tr),len(de))
if __name__=='__main__':main()
