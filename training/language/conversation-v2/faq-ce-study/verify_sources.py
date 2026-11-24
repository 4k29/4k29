import pathlib,json,urllib.request,concurrent.futures,time,hashlib,re,html,unicodedata,collections
P=pathlib.Path(__file__).parent;D=P/'QUARANTINE/pages';D.mkdir(exist_ok=True);rs=json.loads((P/'QUARANTINE/CANDIDATES.json').read_text());urls=sorted({r['url'].split('#')[0]for r in rs})
def canon(s):return ''.join(unicodedata.normalize('NFKC',html.unescape(s)).split())
def fetch(u):
 h=hashlib.sha256(u.encode()).hexdigest();p=D/(h+'.html')
 try:
  if p.exists():b=p.read_bytes()
  else:
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ResearchCorpusAudit/1.0 (bounded FAQ source verification)'}),timeout=20)as f:b=f.read(4000000)
   p.write_bytes(b);time.sleep(.35)
  charset=re.search(br'charset\s*=\s*["\']?([\w-]+)',b[:2000]);cs=charset.group(1).decode()if charset else'utf-8'
  try:s=b.decode(cs)
  except (UnicodeDecodeError,LookupError):s=b.decode('utf-8',errors='replace')
  s=re.sub(r'<script\b.*?</script>|<style\b.*?</style>','',s,flags=re.S|re.I);plain=html.unescape(re.sub('<[^>]*>',' ',s));norm=canon(plain)
  return u,dict(ok=True,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),canonical=norm,last_modified_known=False,thirdparty_markers=bool(re.search('共同通信|朝日新聞|読売新聞|無断転載|転載を禁じ|転載禁止',plain)))
 except Exception as e:return u,dict(ok=False,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:pages=dict(ex.map(fetch,urls))
out=[];counts=collections.Counter()
for r in rs:
 p=pages[r['url'].split('#')[0]]
 if not p['ok']:counts['unavailable_original']+=1;continue
 if p['thirdparty_markers']:counts['possible_individual_rights_exception']+=1;continue
 q,a=canon(r['question']),canon(r['response']);text=p['canonical'];qa=text.find(q);aa=text.find(a,max(qa,0))
 if qa<0 or aa<0:counts['original_question_or_full_answer_not_matched']+=1;continue
 out.append(dict(r,source_page_sha256=p['sha256'],source_question_canonical_offset=qa,source_answer_canonical_offset=aa,snapshot_date='2026-11-13 JST acquisition; original answer update date unknown unless separately identified',knowledge_scope='external_knowledge_QA; no answer evidence added to input',rights='source official government terms compatible with CC-BY4; attributable prose only'))
(P/'VERIFIED_CANDIDATES.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')));(P/'SOURCE_FETCH.json').write_text(json.dumps(dict(pages={u:{k:v for k,v in z.items()if k!='canonical'}for u,z in pages.items()},counts=dict(counts),verified=len(out),body_tokens=sum(r['body_tokens']for r in out)),ensure_ascii=False,indent=2)+'\n');print('verified',len(out),sum(r['body_tokens']for r in out),'sources',dict(collections.Counter(r['source']for r in out)),'held',dict(counts))
