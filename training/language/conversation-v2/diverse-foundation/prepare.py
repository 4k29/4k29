"""Candidate assembly: preserve original bytes, speaking order and source boundaries."""
import collections,re,statistics
from common import *
enc=Encoder(read(V/'data/tokenizer.json'));pieces=[bytes.fromhex(x)for x in enc.tok['bytes']]
def encode(s):
 t=enc(s);assert b''.join(pieces[x]for x in t)==s.encode();assert all(x>=6 for x in t);return t
rows=[];rejected=[]
for r in gzrows(P/'corpus-clean.jsonl.gz'):
 if r['split']=='train':rows.append({**r,'origin':'reused_PR103','kind':'prose','speaker_ids':[]})
# Original RP TRAIN only, with existing speaker-independent split. Retain human A/B meaning.
for line in (V/'data/train.docs.jsonl').read_text().splitlines():
 d=json.loads(line);t=[1];texts=[]
 for u in d['utterances']:
  body=encode(u['text']);t += [u['localRoleToken']]+body+[2];texts.append(u['text'])
 rows.append(dict(id=d['id'],source='realpersona',component=d['normalizedDocumentFamily'],family=d['normalizedDocumentFamily'],title='human everyday conversation',split='train',text='\n'.join(texts),tokens=t,body_tokens=[x for x in t if x>=6],BOS=True,EOS=True,kind='human_dialogue',origin='reused_existing_TRAIN',speaker_ids=d['speakers'],utterances=d['utterances'],provenance={k:v for k,v in d.items()if k!='utterances'},boundary_contract='original turn EOS and local human A/B tokens, never assistant identity'))
raw=read(D/'sources/jmrd-train.raw.json');held_movies={};pii=re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)0\d{1,3}[-ー]\d{2,4}[-ー]\d{3,4}(?!\d)')
for d in raw:
 if d['dialog_id']=='03042':held_movies[d['movie_title']]='exposed README family'
 for u in d['dialog']:
  if pii.search(u['text']):held_movies[d['movie_title']]='contact information proxy; whole movie family held'
  for k in u.get('checked_knowledge',[]):
   c=k.get('content','');text=canon(u['text']);c=canon(c)if isinstance(c,str)else''
   if len(c)>=40 and any(c[j:j+40]in text for j in range(len(c)-39)):held_movies[d['movie_title']]='possible third-party plot/review copied into utterance; whole movie family held'
for d in raw:
 family='jmrd|'+d['movie_title']
 if d['movie_title']in held_movies:rejected.append(dict(id='jmrd:'+d['dialog_id'],component=family,reason=held_movies[d['movie_title']]));continue
 t=[1];sp={};utterances=[]
 for i,u in enumerate(d['dialog']):
  if u['speaker']not in sp:sp[u['speaker']]=3+len(sp)
  assert len(sp)<=2 and u['utterance_id']==d['dialog_id']+'_%02d'%i
  assert i==0 or u['speaker']!=d['dialog'][i-1]['speaker']
  body=encode(u['text']);t += [sp[u['speaker']]]+body+[2]
  utterances.append(dict(ordinal=i,speaker_role=u['speaker'],localRoleToken=sp[u['speaker']],text=u['text']))
 rows.append(dict(id='jmrd:'+d['dialog_id'],source='jmrd',component=family,family=family,title=d['movie_title'],split='train',text='\n'.join(u['text']for u in d['dialog']),tokens=t,body_tokens=[x for x in t if x>=6],BOS=True,EOS=True,kind='human_dialogue',origin='reused_prior_acquisition_verified_reGET',speaker_ids=[],utterances=utterances,provenance=dict(url='https://github.com/ku-nlp/JMRD/blob/a20b0a89b4cf6ce1db320039f6e27df10604bf4c/data/train.json',revision='a20b0a89b4cf6ce1db320039f6e27df10604bf4c',raw_sha256=sha(D/'sources/jmrd-train.raw.json'),license='CC-BY-SA-4.0',attribution='Takashi Kodama, Ribeka Tanaka and Sadao Kurohashi; JMRD',fields='dialog[].text only; no knowledge, reviews or questionnaire targets',author_independence='persistent worker IDs unavailable; not claimed'),boundary_contract='original human turn EOS, local human A/B assigned by first speaker; recommender is not AI assistant'))
for r in gzrows(D/'jma-candidates.jsonl.gz'):
 if r['hold_reason']:rejected.append(dict(id=r['id'],component=r['component'],reason=r['hold_reason']));continue
 body=encode(r['text']);rows.append({**r,'body_tokens':body,'tokens':[1]+body+[2],'kind':'prose','origin':'new_network_acquisition','speaker_ids':[]})
gzwrite(D/'candidates.jsonl.gz',rows);write(D/'CANDIDATE_REJECTIONS.json',rejected)
sample=[]
for source,n in [('jmrd',12),('jma',16)]:
 seen=set()
 for r in sorted([x for x in rows if x['source']==source],key=lambda r:rank('read|'+r['id'])):
  if r['component']in seen and source=='jmrd':continue
  seen.add(r['component']);sample.append(dict(id=r['id'],source=source,component=r['component'],split=r['split'],text=r['text']))
  if sum(x['source']==source for x in sample)>=n:break
write(D/'QUALITY_SAMPLE.private.json',sample)
# Publish only non-held source sample text; preserve original local audit SHA.
public=[]
for r in sample:
 if r['source']=='jmrd':
  r=dict(r);r['quarantined_text_sha256']=hashlib.sha256(r.pop('text').encode()).hexdigest();r['text_withheld']='quality-held source body omitted from public audit; original read locally'
 public.append(r)
write(D/'QUALITY_SAMPLE.json',public)
write(D/'CANDIDATE_STATS.json',dict(units=len(rows),body_tokens=dict(collections.Counter({s:sum(len(r['body_tokens'])for r in rows if r['source']==s and r['split']=='train')for s in {x['source']for x in rows}})),jmrd_held_movies=held_movies,sample_count=len(sample)))
print(read(D/'CANDIDATE_STATS.json'))
