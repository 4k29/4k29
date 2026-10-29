"""Freeze reviewed admission; DEV-first canonical and verified character-shingle overlap."""
import collections,zlib,statistics
from common import *
rows=gzrows(D/'candidates.jsonl.gz');review=read(D/'QUALITY_REVIEW.json');held=set(review['held_components']);rejected=read(D/'CANDIDATE_REJECTIONS.json');protected=[]
for r in gzrows(P/'corpus-clean.jsonl.gz'):
 if r['split']=='dev':protected.append(dict(id='olddev:'+r['id'],text=r['text'],component=r['component'],split='dev'))
for r in gzrows(H/'data.jsonl.gz'):
 if r['split']=='dev':protected.append(dict(id='hdev:'+r['id'],text=r['text'],component=r['component'],split='dev'))
for l in (V/'data/dev.docs.jsonl').read_text().splitlines():
 r=json.loads(l);protected.append(dict(id='rpdev:'+r['id'],text='\n'.join(u['text']for u in r['utterances']),component=r['normalizedDocumentFamily'],split='dev'))
# FAQ page-family DEV stays entirely out of TRAIN before any generation.
protected += [r for r in rows if r['split']=='dev']
index=collections.defaultdict(list);store=[];seen={};overlaps=[]
def signatures(s):return set(sorted({zlib.crc32(s[i:i+13].encode())for i in range(max(0,len(s)-12))})[:64])
def insert(r,protect=False):
 s=canon(r['text']);h=rank(s);sig=signatures(s);matches=collections.Counter(j for z in sig for j in index[z]);why=None
 if h in seen:why=('canonical',seen[h])
 elif len(s)>=80:
  for j,n in matches.items():
   if n<4:continue
   q,t=store[j]
   if len(t)<80:continue
   a={s[i:i+13]for i in range(len(s)-12)};b={t[i:i+13]for i in range(len(t)-12)};v=len(a&b)/min(len(a),len(b))
   if v>=.85:why=('near_containment',q['id']);overlaps.append(dict(id=r['id'],matches=q['id'],containment=v,protected=q['split']=='dev'));break
 if why and not protect:rejected.append(dict(id=r['id'],component=r['component'],reason=why[0],matches=why[1]));return False
 seen[h]=r['id'];j=len(store);store.append((r,s))
 for z in sig:index[z].append(j)
 return True
for r in protected:insert(r,True)
accepted=[]
for r in sorted(rows,key=lambda r:rank(r['id'])):
 if r['component']in held:rejected.append(dict(id=r['id'],component=r['component'],reason='fixed sample family hold'));continue
 if r['split']=='dev':accepted.append(r);continue
 if insert(r):accepted.append(r)
gzwrite(D/'corpus.jsonl.gz',accepted);write(D/'REJECTIONS.json',rejected);write(D/'OVERLAPS.json',overlaps)
tr=[r for r in accepted if r['split']=='train'];dv=[r for r in accepted if r['split']=='dev'];assert not({r['component']for r in tr}&{r['component']for r in dv})
windows=[]
for r in tr:
 for start in range(0,len(r['tokens'])-1,256):
  t=r['tokens'][start:start+257]
  if len(t)>1:windows.append(dict(id=r['id']+'@'+str(start),unit_id=r['id'],source=r['source'],component=r['component'],start=start,tokens=t))
random.Random(41030).shuffle(windows);batches=[windows[i:i+4]for i in range(0,len(windows),4)]
with (D/'schedule.json.gz').open('wb')as f:
 with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0)as z:z.write(json.dumps(dict(batches=batches),separators=(',',':')).encode())
# Twelve pre-fixed section continuations, four per reserved FAQ page.
new=[]
for family in sorted({r['component']for r in dv}):
 for r in sorted([r for r in dv if r['component']==family],key=lambda r:rank('dev|'+r['id']))[:4]:
  cut=min(32,max(12,len(r['body_tokens'])//5));new.append(dict(id=r['id'],panel='newJMA',component=family,prefix=[1]+r['body_tokens'][:cut],reference=r['body_tokens'][cut:]+[2],prefix_text=b''.join(bytes.fromhex(read(V/'data/tokenizer.json')['bytes'][i])for i in r['body_tokens'][:cut]).decode('utf8','strict'),text=r['text']))
write(D/'NEW_DEV_SOURCES.json',new)
enc=Encoder(read(V/'data/tokenizer.json'))
utterances=[u['text']for r in tr if r['kind']=='human_dialogue'for u in r['utterances']];unique_u=set(utterances)
audit=dict(train_units=len(tr),dev_sections=len(dv),body_tokens=sum(len(r['body_tokens'])for r in tr),source_body_tokens={s:sum(len(r['body_tokens'])for r in tr if r['source']==s)for s in sorted({r['source']for r in tr})},origin_body_tokens={s:sum(len(r['body_tokens'])for r in tr if r['origin']==s)for s in sorted({r['origin']for r in tr})},human_dialogue_utterances=len(utterances),unique_utterance_strings=len(unique_u),conversational_unique_string_body_tokens=sum(len(enc(t))for t in unique_u),speaker_ids=len({s for r in tr for s in r['speaker_ids']}),components=len({r['component']for r in tr}),full_pass_updates=len(batches),full_pass_targets=sum(len(w['tokens'])-1 for w in windows),EOS_teachers=sum(w['tokens'][1:].count(2)for w in windows),role_teachers=sum(sum(x in [3,4]for x in w['tokens'][1:])for w in windows),BOS_teachers=sum(w['tokens'][1:].count(1)for w in windows),PAD_teachers=0,duplicated_target_positions=0,overlap_context_tokens=sum(max(0,(len(r['tokens'])-2)//256)for r in tr),unit_length_quantiles={str(q):sorted(len(r['tokens'])for r in tr)[int(q*(len(tr)-1))]for q in [0,.5,.9,.99,1]},units_over256=sum(len(r['tokens'])>257 for r in tr),byte_roundtrip='all candidates encoded and exact UTF8-verified before admission',sealed_TEST_used=False,author_independence='RP preserved existing speaker split; wiki all-author independence and JMA individual authors unverified',near_duplicate_scope='64 lowest crc32 of all13-char shingles; candidate>=4hits verified85%shorter-set containment; not exhaustive semantic guarantee',new_acquired_vs_reGET='JMA only is newly acquired independent content; JMRD identical old raw SHA, no additional new original volume')
write(D/'CORPUS_AUDIT.json',audit);print(audit)
