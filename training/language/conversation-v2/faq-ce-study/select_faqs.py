import pathlib,json,hashlib,collections,urllib.parse,gzip,unicodedata,difflib,re
P=pathlib.Path(__file__).parent;V=pathlib.Path('/workspace/4k29/training/language/conversation-v2');rs=json.loads((P/'VERIFIED_CANDIDATES.json').read_text());canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split());fam=lambda u:urllib.parse.urlsplit(u).netloc+urllib.parse.urlsplit(u).path
priorfamilies=set();priorstrings=set()
for path in [V/'diverse-foundation/corpus.jsonl.gz',V/'paragraph-foundation/corpus.jsonl.gz']:
 for line in gzip.open(path,'rt'):
  r=json.loads(line);u=r.get('provenance',{}).get('url');
  if u:priorfamilies.add(fam(u))
  if r.get('text'):
   priorstrings.add(canon(r['text']));priorstrings.update(canon(t)for t in r['text'].split('\n')if len(t)>=20)
held=[];pool=[];seenq=set();seena=set()
for r in sorted(rs,key=lambda r:hashlib.sha256(('faq-dedup-v1|'+r['id']).encode()).hexdigest()):
 reason=None;q,a=canon(r['question']),canon(r['response'])
 if any(x in r['url']for x in ['/clarinet/1403613_00003.htm','/space/jigyou/detail/1406357_00006.htm','/guide/info/eco-first/faq/faq2.html','/chemi/prtr/notification/qa/busshitsu.html']):reason='Individually identified missing programme/logo/legal scope family'
 elif r['index']in[19798,12511,12961]:reason='Orphan service, unsettled adjustment, or nonessential outside-video scope'
 elif re.search('本委託費|今回の規制|本制度|本事業|本調査',r['question']+r['response']):reason='Unidentified policy/programme context'
 elif re.search('ご覧|参照|ホームページ|PDF|お問い合わせ|お問合せ|問い合わせ|御了承|今後|想定|本アプリ|本サービス|本ガイドライン|今回のガイドライン|第[0-9]+節',r['question']+r['response'])or '/vaccinecert/'in r['url']:reason='Missing outside reference, unresolved future policy, or orphan service context'
 elif r['index']in[19769,11925,11938]:reason='Individually read orphan context/unspecified dispatch or selection process'
 elif r['source']=='農林水産省':reason='Preserve historical MAFF source-held-out status, no TRAIN adoption'
 elif r['family']in priorfamilies:reason='Prior learned/evaluated original URL family'
 elif q in seenq or a in seena:reason='Canonical question/answer duplicate'
 elif q in priorstrings or a in priorstrings:reason='Exact canonical overlap with prior TRAIN/DEV body or paragraph'
 elif re.search('避難|服用|投与|受診|診断|医薬品|治療|罰則|法律第|政令第|申請者|請求者|円を|賠償|許諾|転載|著作権者',r['question']+r['response']):reason='High-risk individual guidance or third-party rights reference not adopted'
 if reason:held.append(dict(id=r['id'],reason=reason));continue
 seenq.add(q);seena.add(a);pool.append(r)
# Connect near questions OR near answers into indivisible family components before splitting.
parent={r['family']:r['family']for r in pool}
def find(x):
 while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
 return x
def union(a,b):
 a,b=find(a),find(b)
 if a!=b:parent[max(a,b)]=min(a,b)
near=[]
for i,r in enumerate(pool):
 for s in pool[:i]:
  if r['family']==s['family']:continue
  q1,q2=canon(r['question']),canon(s['question']);a1,a2=canon(r['response']),canon(s['response'])
  qr=difflib.SequenceMatcher(None,q1,q2,autojunk=False).ratio()if min(len(q1),len(q2))/max(len(q1),len(q2))>=.85 else 0
  ar=difflib.SequenceMatcher(None,a1,a2,autojunk=False).ratio()if min(len(a1),len(a2))/max(len(a1),len(a2))>=.9 else 0
  if qr>=.85 or ar>=.9:union(r['family'],s['family']);near.append([r['id'],s['id'],qr,ar])
for r in pool:r['split_family']=find(r['family'])
groups=collections.defaultdict(list)
for r in pool:groups[r['split_family']].append(r)
# Two modest whole-page families per source; >=6 DEV cases when possible. No outputs inspected.
devfamilies=set()
for source in sorted({r['source']for r in pool}):
 gs=[(f,z)for f,z in groups.items()if {r['source']for r in z}=={source}and 3<=len(z)<=20]
 gs.sort(key=lambda fz:hashlib.sha256(('faq-family-dev-v1|'+fz[0]).encode()).hexdigest())
 devfamilies.update(f for f,z in gs[:2])
train=[r for r in pool if r['split_family']not in devfamilies];devpool=[r for r in pool if r['split_family']in devfamilies];dev=[]
for source in sorted({r['source']for r in devpool}):
 z=sorted([r for r in devpool if r['source']==source],key=lambda r:hashlib.sha256(('faq-dev-case-v1|'+r['id']).encode()).hexdigest());dev.extend(z[:6])
# Fixed stratified TRAIN reading sample source x category x answer-length bin, one per observed stratum.
strata=collections.defaultdict(list)
for r in train:strata[(r['source'],r['category_proxy'],'short'if r['body_tokens']<=60 else'medium'if r['body_tokens']<=120 else'long')].append(r)
sample=[sorted(z,key=lambda r:hashlib.sha256(('faq-quality-read-v1|'+r['id']).encode()).hexdigest())[0]for k,z in sorted(strata.items())]
(P/'PROTOCOL-QUALITY.json').write_text(json.dumps(dict(seed='faq-quality-read-v1',rule='One per observed source/category/length stratum; read every DEV; deterministic gates in profile.py/select.py; errors may quarantine identified risk-family before any optimizer, never based on model outputs',full_unreviewed_corpus_not_passed=True,pre_model_updates=0,dev_family_seed='faq-family-dev-v1',near_thresholds={'question':.85,'answer':.9},MAFF='fully held out'),indent=2)+'\n')
(P/'PREPARED.json').write_text(json.dumps(dict(train=train,dev=dev,unused_dev_family=[r['id']for r in devpool if r['id']not in {x['id']for x in dev}],held=held,near_links=near,quality_sample_ids=[r['id']for r in sample]),ensure_ascii=False,separators=(',',':')))
print('TRAIN',len(train),sum(r['body_tokens']for r in train),'DEV',len(dev),'SAMPLE',len(sample),'sources',dict(collections.Counter(r['source']for r in train)))
for label,z in [('S',sample),('D',dev)]:
 (P/(label+'-READING.txt')).write_text('\n'.join(f"{label} {r['id']} {r['source']} {r['category_proxy']} {r['url']}\nQ {r['question']}\nA {r['response']}"for r in z))
