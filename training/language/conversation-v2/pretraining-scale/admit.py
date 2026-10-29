"""Bounded research admission, exact source bytes, conservative family holds and near duplicate audit."""
import collections,re,zlib,statistics
from common import *
# Written only after reading every byte of the preregistered 72-row sample.
HOLD={0:'historical occupation/violence concentration outside daily prose priority',3:'military operation numeric roster',4:'military engine specification and attributed testimonial',5:'warship numeric specification',6:'unverified biomedical efficacy assertions',8:'attributed living-person claims and third-party quotations',9:'broken reference marker and third-party deathbed quotation',11:'living-person private routine and attributed quotations',12:'incorrect historical attribution of beryllium naming',13:'graphic execution narrative',14:'missing antecedent 前述 and specialist race chronology',16:'missing 前述 dependency',18:'technical aircraft specification concentration',20:'truncated Japanese とた and missing source context',22:'後述 dependency',24:'specialist dynastic violence concentration',27:'ungrammatical joined final clause and crime reportage',29:'short isolated biography rather than continuous explanation',31:'前述 dependency',32:'dated current-tense rankings',34:'missing particle and unverified categorical admission claim',35:'third-party slogan and fictional plot quotation',37:'internally inconsistent Gregorian/era year',39:'specialist potentially poisonous mushroom identification',41:'authorship speculation and quotation dependencies',43:'dense dynastic numeric chronology',44:'unbound このステンドグラス',46:'military diplomatic chronology',47:'unbound 上述 and inconsistent author spelling',48:'overbroad current admission advice',49:'code/manual formatting and broken fragment',51:'factually wrong food example and list format',52:'legal policy source and archaic orthography',53:'false average lifespan claim',56:'obsolete exam regime and speculative inverse-score advice',57:'overstated ecology causal advice',60:'technical course dependency with missing source scope',62:'incorrect biological chromosome valence terminology',63:'specialist drug chemical synthesis fragment',64:'current legal/immigration advice not verified',65:'broken translation 大きな意味を守る',66:'unverified road safety advice',67:'external-reference navigation rather than explanation',68:'unverified current driving-license advice',71:'HTML entity and current travel safety context'}
sample=read(P/'QUALITY_SAMPLE.json');heldfamilies={sample[i]['component']:reason for i,reason in HOLD.items()}
heldfamilies.update({'jawikivoyage|オー＝ド＝フランス地方':'additional review: unverified reassurance about travel safety','jawikivoyage|飲食を楽しむ':'additional review: unverified legal/food-taboo advice'})
write(P/'QUALITY_REVIEW.json',dict(reviewer='main assistant, not independent native human',sample_sha256=sha(P/'QUALITY_SAMPLE.json'),all_72_read_in_full=True,decisions=[dict(id=r['id'],component=r['component'],decision='hold_entire_family'if i in HOLD else'bounded_prose_candidate',reason=HOLD.get(i,'Coherent explanatory prose, no identified privacy/quotation exception; not a full independent fact certification'))for i,r in enumerate(sample)],held_families=heldfamilies,remaining_risks=['Complete contributor/human-only authorship unknown','Source citations retained, all factual claims not exhaustively checked','No formal human quality evaluation']))
rows=gzrows(P/'candidates.jsonl.gz');old=gzrows(H/'data.jsonl.gz');oldcanon={canon(r['text'])for r in old if r['split']=='train'}
# Some old admitted groups joined consecutive paragraphs; compare each constituent too.
oldpositions={(r['provenance']['id'],i)for r in old if r['split']=='train'for i in r['paragraph_ordinals']}
extra_bad=re.compile(r'GNU|Octave|マニュアル|センター試験|基本方針|プログラム|プログラミング|数学|法学|法令|法規|医療|医学|薬|病|毒|戦艦|戦闘機|作戦|占領|軍事')
text_bad=re.compile(r'要出典|要リンク|リンク切れ|前述|上述|後述|下記|上記|この表|この図|参照|&[a-zA-Z]+;|平均寿命.{0,3}[1１][0０][0０]|このページ|本ページ|本節|画像:|File:|小説から|転載|引用|[「『][^」』]{12,}[」』]')
accepted=[];holds=collections.Counter();rejections=[]
for r in rows:
 reason=heldfamilies.get(r['component'])
 if not reason and extra_bad.search(r['title']):reason='source/genre restriction'
 if not reason and text_bad.search(r['text']):reason='unbound_reference_quote_or_markup_proxy'
 if not reason and '\n'in r['text']and len(r['text'].split('\n')[0].strip())<16 and not r['text'].split('\n')[0].endswith('。'):reason='list_or_heading_fragment_proxy'
 if reason:holds[reason]+=1;rejections.append(dict(id=r['id'],component=r['component'],reason=reason));continue
 accepted.append(r)
# All source DEV components protected, never used to fit tokenizer/weights.
train=[r for r in accepted if r['split']=='train'];dev=[r for r in accepted if r['split']=='dev'];devcomp={r['component']for r in rows if r['split']=='dev'};assert not({r['component']for r in train}&devcomp)
# Protect known original last author: hold evaluation documents with any observed TRAIN last-author collision.
authors={(r['source'],r['provenance'].get('lastContributorId'))for r in train if r['source']!='jaquad'}
dev=[r for r in dev if r['source']=='jaquad'or(r['source'],r['provenance'].get('lastContributorId'))not in authors]
# Fixed character shingle fingerprints generate pairs; full 13-char shingles verify them.
# This measures surface overlap, never claims semantic-family/complete-author independence.
def shingles(s):return{s[i:i+13]for i in range(max(1,len(s)-12))}
def fps(s):return set(sorted({zlib.crc32(s[i:i+13].encode())for i in range(max(1,len(s)-12))})[:64])
index=collections.defaultdict(list);stored=[];canonical={};near=[]
def add(r,protect=False):
 s=canon(r['text']);key=hashlib.sha256(s.encode()).hexdigest();fs=fps(s);hit=collections.Counter(j for h in fs for j in index[h]);reason=None
 if key in canonical:reason=('canonical_duplicate',canonical[key])
 else:
  for j,n in hit.items():
   if n<4:continue
   other=stored[j];t=other[1];a=shingles(s);b=shingles(t);inter=len(a&b);jac=inter/len(a|b);contain=inter/min(len(a),len(b))
   if jac>=.8 or contain>=.85:
    reason=('near_duplicate',other[0]['id']);near.append(dict(id=r['id'],matches=other[0]['id'],jaccard=jac,containment=contain,protected_DEV=other[0]['split']=='dev'));break
 if reason and not protect:rejections.append(dict(id=r['id'],reason=reason[0],matches=reason[1]));holds[reason[0]]+=1;return False
 j=len(stored);stored.append((r,s));canonical[key]=r['id']
 for h in fs:index[h].append(j)
 return True
for r in dev:add(r,True)
train=[r for r in sorted(train,key=lambda r:(not r['old_admission'],rank(r['id'])))if add(r)]
# Freeze 20 newly exposed DEV families before generation; upstream official TRAIN-derived local DEV only.
olddev={r['component']for r in old if r['split']=='dev'};newdev=[];seen=set()
for r in sorted(dev,key=lambda r:rank('new-dev|'+r['id'])):
 if r['component']in olddev or r['component']in seen or len(r['text'])<140:continue
 seen.add(r['component']);newdev.append(r)
 if len(newdev)==20:break
enc=Encoder(read(V/'data/tokenizer.json'));pieces=[bytes.fromhex(x)for x in enc.tok['bytes']];final=[];roundtrip=0
for r in train+newdev:
 ids=enc(r['text']);assert b''.join(pieces[i]for i in ids)==r['text'].encode();assert 0 not in ids and all(i>=6 for i in ids)
 r={**r,'body_tokens':ids,'BOS':r['source']!='jaquad'and r['original_page_start'],'EOS':r['source']!='jaquad'and r['original_page_end'],'admission':'bounded_exploratory_pretraining_not_formal_model_adoption','new_vs_PR101':(r['provenance']['id'],r['paragraph_ordinal'])not in oldpositions}
 # No arbitrary paragraph EOS added. This preserves source extraction page edges only.
 r['tokens']=([1]if r['BOS']else[])+ids+([2]if r['EOS']else[]);final.append(r);roundtrip+=1
 if roundtrip%1000==0:print('roundtrip',roundtrip,flush=True)
gzipwrite(P/'corpus.jsonl.gz',final);write(P/'REJECTIONS.json',rejections);write(P/'NEAR_DUPLICATES.json',near)
tr=[r for r in final if r['split']=='train'];dv=[r for r in final if r['split']=='dev'];lengths=[len(r['body_tokens'])for r in tr]
write(P/'CORPUS_AUDIT.json',dict(train_paragraphs=len(tr),dev_paragraphs=len(dv),train_body_tokens=sum(lengths),newly_admitted_vs_PR101_tokens=sum(len(r['body_tokens'])for r in tr if r['new_vs_PR101']),reused_vs_PR101_tokens=sum(len(r['body_tokens'])for r in tr if not r['new_vs_PR101']),newly_acquired_tokens=0,unique_canonical_paragraphs=len({canon(r['text'])for r in tr}),source_tokens={s:sum(len(r['body_tokens'])for r in tr if r['source']==s)for s in sorted({r['source']for r in tr})},components=len({r['component']for r in tr}),last_author_DEV_overlap=0,complete_author_independence_unknown=True,semantic_family_independence_not_proven=True,byte_roundtrip_all=roundtrip,document_context_exceeds256=sum(n>256 for n in lengths),length_quantiles={str(q):sorted(lengths)[int((len(lengths)-1)*q)]for q in [0,.25,.5,.75,.9,1]},EOS_units=sum(r['EOS']for r in tr),BOS_units=sum(r['BOS']for r in tr),jaquad_added_EOS=0,held=dict(holds),source_sha256=sha(V/'foundation-data/corpus/documents.jsonl.gz'),corpus_sha256=sha(P/'corpus.jsonl.gz'),sealed_TEST_used=False,formal_human_review=False))
write(P/'NEW_DEV_SOURCES.json',dv);print(read(P/'CORPUS_AUDIT.json'))
