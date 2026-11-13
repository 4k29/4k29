import pathlib,json,hashlib,re,html,unicodedata,collections
P=pathlib.Path(__file__).parent;d=json.loads((P/'DATA.json').read_text());rows=sum(d['parts'].values(),[]);allrows=[json.loads(l)for l in(P/'QUARANTINE/data.jsonl').read_text().splitlines()];by=collections.defaultdict(list)
canon=lambda s:''.join(unicodedata.normalize('NFKC',html.unescape(s)).split())
for r in allrows:by[r['url'].split('#')[0]].append(canon(r['Question']))
cache={};proof=[];bad=[]
for r in rows:
 u=r['url'].split('#')[0]
 if u not in cache:
  b=(P/'QUARANTINE/pages'/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_bytes();m=re.search(br'charset\s*=\s*["\']?([\w-]+)',b[:2000]);cs=m.group(1).decode()if m else'utf-8'
  try:s=b.decode(cs)
  except (UnicodeDecodeError,LookupError):s=b.decode('utf-8',errors='replace')
  s=re.sub(r'<script\b.*?</script>|<style\b.*?</style>','',s,flags=re.S|re.I);cache[u]=canon(re.sub('<[^>]*>',' ',s))
 t=cache[u];q,a=canon(r['question']),canon(r['response']);aa=t.find(a,t.find(q)+len(q));qq=t.rfind(q,0,aa+1);assert qq>=0 and aa>qq
 intervening=[other for other in by[u]if other!=q and t.find(other,qq+len(q),aa)>=0]
 if intervening:bad.append(dict(id=r['id'],intervening=len(intervening)))
 proof.append(dict(id=r['id'],question_offset=qq,answer_offset=aa,other_known_questions_between=len(intervening)))
(P/'PAIR_ADJACENCY_AUDIT.json').write_text(json.dumps(dict(cases=len(proof),bad=bad,proof=proof,method='Closest preceding exact normalized original question to full original answer; other known FAQ questions between checked; not a full DOM/semantic correctness guarantee',optimizer_calls=0,model_forwards=0),indent=2)+'\n');print('adjacency',len(proof),'bad',bad)
