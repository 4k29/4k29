"""Only previously admitted paragraphs; EOS only on whole, closed native paragraphs."""
import collections,gzip,hashlib,re
from common import *
def rank(s):return hashlib.sha256(('natural-boundary-study-v1|'+s).encode()).hexdigest()
def main():
 units=list(map(json.loads,gzip.open(H/'data.jsonl.gz','rt')));wanted={r['provenance']['id']for r in units};docs={r['id']:r for r in map(json.loads,gzip.open(V/'foundation-data/corpus/documents.jsonl.gz','rt'))if r['id']in wanted};tok=json.loads((V/'data/tokenizer.json').read_text());enc=Encoder(tok);rows={};excluded=collections.Counter()
 for u in units:
  if u['source']=='jaquad':continue # No EOS on JaQuAD excerpts, including punctuation-ended excerpts.
  d=docs[u['provenance']['id']];paras={p['ordinal']:p for p in d['paragraphs']}
  for ordinal in u['paragraph_ordinals']:
   p=paras[ordinal];s=p.get('normalizedText',p['text']);assert s in u['text'],'Original paragraph must be unchanged within admitted unit'
   if not s.endswith('。')or not s or s.count('「')!=s.count('」')or s.count('（')!=s.count('）'):excluded['not_closed_paragraph']+=1;continue
   if re.match(r'^(この|その|それ|これ|また|さらに|なお|ただし|つまり|一方|上述|前述|次に|例えば|したがって|そして|しかし|図|表|※|\d+[\.．])',s):excluded['antecedent_or_list_proxy']+=1;continue
   if any(x in s for x in ['以下の','上記の','下記の','図を','表を','{{','http']):excluded['external_reference_proxy']+=1;continue
   ids=enc(s)
   if not 40<=len(ids)<=240:excluded['length']+=1;continue
   ident=u['provenance']['id']+':paragraph'+str(ordinal);r=dict(id=ident,source_unit=u['id'],source=u['source'],split=u['split'],component=u['component'],title=u['title'],paragraph_ordinal=ordinal,text=s,body_tokens=ids,tokens=[1]+ids+[2],provenance=u['provenance'],boundary='Original processed paragraph, terminal Japanese full stop, closed delimiters, no cut; new independent paragraph task, not asserted original page boundary',semantic_review='candidate proxy, not an individual semantic pass')
   if ident in rows:assert rows[ident]['text']==s
   else:rows[ident]=r
 pool=sorted(rows.values(),key=lambda r:rank(r['id']));train=[r for r in pool if r['split']=='train'];dev=[r for r in pool if r['split']=='dev'];sample=[]
 for source in ['jawikibooks','jawikivoyage']:
  candidates=[r for r in train if r['source']==source];seen=set()
  for r in candidates:
   if r['component']in seen and len(seen)<8:continue
   sample.append(r);seen.add(r['component'])
   if len([x for x in sample if x['source']==source])==16:break
 write(N/'paragraph-candidates.json',dict(train=train,dev=dev));write(N/'paragraph-review.json',sample);write(N/'CANDIDATE_AUDIT.json',dict(train_paragraphs=len(train),dev_paragraphs=len(dev),train_body_tokens=sum(len(r['body_tokens'])for r in train),source_counts=dict(collections.Counter(r['source']for r in train)),source_components=len({r['component']for r in train}),dev_components=len({r['component']for r in dev}),excluded=dict(excluded),not_yet_training_authorized=True));print(json.loads((N/'CANDIDATE_AUDIT.json').read_text()))
if __name__=='__main__':main()
