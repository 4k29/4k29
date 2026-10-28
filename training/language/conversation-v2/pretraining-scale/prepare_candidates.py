"""Reuse licensed official TRAIN-derived material. Candidate extraction, not admission."""
import collections,re,importlib.util
from common import *
spec=importlib.util.spec_from_file_location('old_admission',H/'prepare.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
BOOK=re.compile(r'料理|学習方法|独学|家庭|園芸|生物|理科|地理|歴史|美術|音楽|天体|太陽系|将棋|囲碁|物理|化学|日本語|言語|地球|地学|生活|環境|スポーツ|農業|写真')
EXTRA_BAD=re.compile(r'法令|条文|法律|憲法|刑法|民法|著作権法|プログラミング|プログラム|ソースコード|API|古典|古文|漢文|聖書|宗教|保健|医療|医学|病気|薬学|軍事')
oldrows=gzrows(H/'data.jsonl.gz');oldpos={(r['provenance']['id'],n)for r in oldrows for n in r['paragraph_ordinals']};olddev={r['component']for r in oldrows if r['split']=='dev'}
broad={r['id']for r in gzrows(N/'expansion-broad-candidates.jsonl.gz')};held=read(N/'PARAGRAPH_REVIEW.json')['held'];heldpairs=set();heldfamily={'jawikibooks|囲碁'}
for ident in held:
 if ':paragraph'in ident:doc,n=ident.rsplit(':paragraph',1);heldpairs.add((doc,int(n)))
pool=[];counts=collections.Counter()
for d in gzrows(V/'foundation-data/corpus/documents.jsonl.gz'):
 if d['split']not in ['train','dev']:continue
 if old.BAD_TITLE.search(d['title'])or EXTRA_BAD.search(d['title'])or d['component']in heldfamily:continue
 if d['source']=='jawikibooks'and not BOOK.search(d['family'].split('|',1)[-1]):continue
 if d['source']!='jaquad'and('bot'in d.get('lastContributorUsername','').lower()or not d.get('lastContributorId')):continue
 for p in d['paragraphs']:
  if not p['keepForCandidateTraining']or(d['id'],p['ordinal'])in heldpairs:continue
  if old.eligible(p['normalizedText']):continue
  ident=d['id']+':'+str(p['ordinal']);prev=(d['id'],p['ordinal'])in oldpos
  if d['source']=='jaquad'and not(prev or ident in broad or d['split']=='dev'):continue
  if d['split']=='train'and d['component']in olddev:raise AssertionError('Old DEV leak')
  pool.append(dict(id=ident,source=d['source'],component=d['component'],family=d['family'],title=d['title'],split=d['split'],text=p['normalizedText'],previous_BPE=p['ownBpeTokens'],old_admission=prev,paragraph_ordinal=p['ordinal'],provenance={k:v for k,v in d.items()if k not in ['paragraphs','extractionCounts']},original_page_start=p['ordinal']==0,original_page_end=p['ordinal']==len(d['paragraphs'])-1))
# Deterministic quota: no evaluation output is involved. Fixed whole paragraphs, no text rewriting.
selected=[];totals=collections.Counter();family=collections.Counter()
caps={'jaquad':2_500_000,'jawikibooks':900_000,'jawikivoyage':250_000}
for r in sorted(pool,key=lambda r:(not r['old_admission'],rank(r['id']))):
 n=r['previous_BPE'];k=(r['split'],r['source']);fk=(r['split'],r['component'])
 if r['split']=='train'and(totals[k]+n>caps[r['source']]or family[fk]+n>100_000):continue
 totals[k]+=n;family[fk]+=n;selected.append(r)
gzipwrite(P/'candidates.jsonl.gz',selected)
sample=[]
for source,count in [('jaquad',48),('jawikibooks',16),('jawikivoyage',8)]:
 rows=[r for r in selected if r['source']==source and r['split']=='train'and not r['old_admission']];seen=set()
 for r in sorted(rows,key=lambda r:rank('review|'+r['id'])):
  if r['component']in seen:continue
  seen.add(r['component']);sample.append(r)
  if len(seen)>=count:break
write(P/'QUALITY_SAMPLE.json',sample);write(P/'CANDIDATE_AUDIT.json',dict(rows=len(selected),sample=len(sample),prior_BPE_by_source={str(k):v for k,v in totals.items()},source_sha256=sha(V/'foundation-data/corpus/documents.jsonl.gz'),no_new_acquisition=True,status='candidate pending sample/roundtrip/split/near-duplicate review'))
print(read(P/'CANDIDATE_AUDIT.json'))
