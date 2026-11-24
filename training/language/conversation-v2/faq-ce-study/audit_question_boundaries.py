import pathlib,json,re,html,hashlib,unicodedata
from html.parser import HTMLParser
P=pathlib.Path(__file__).parent;d=json.loads((P/'DATA.json').read_text());canon=lambda s:''.join(unicodedata.normalize('NFKC',html.unescape(s)).split())
class DOM(HTMLParser):
 def __init__(self):super().__init__();self.root=['root',[]];self.stack=[self.root]
 def handle_starttag(self,t,a):
  n=[t,[]];self.stack[-1][1].append(n)
  if t not in ['br','hr','img','meta','link','input','source','wbr','area','base','embed','param','track','col']:self.stack.append(n)
 def handle_endtag(self,t):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i][0]==t:self.stack=self.stack[:i];break
 def handle_data(self,x):
  if not any(n[0]in['script','style']for n in self.stack):self.stack[-1][1].append(x)
def blocks(n):
 out=[];texts=[]
 for x in n[1]:
  if isinstance(x,str):texts.append(x)
  else:
   s,b=blocks(x);texts.append(s);out+=b
 s=''.join(texts)
 if n[0]in['p','td','th','dt','li','h1','h2','h3','h4','h5','h6','div']:out.append((n[0],canon(s)))
 return s,out
cache={};proof=[];flag=[];unresolved=[]
for r in sum(d['parts'].values(),[]):
 u=r['url'].split('#')[0]
 if u not in cache:
  b=(P/'QUARANTINE/pages'/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_bytes();m=re.search(br'charset\s*=\s*["\']?([\w-]+)',b[:2000]);cs=m.group(1).decode()if m else'utf-8'
  try:s=b.decode(cs)
  except (UnicodeDecodeError,LookupError):s=b.decode('utf-8',errors='replace')
  z=DOM();z.feed(s);cache[u]=blocks(z.root)[1]
 q=canon(r['question']);c=[(tag,t)for tag,t in cache[u]if q in t and len(t)<=len(q)+80];c.sort(key=lambda x:len(x[1]));valid=[]
 for tag,t in c:
  before=t[:t.find(q)]
  if re.fullmatch(r'[Qq問質問0-9()\[\].、:：?？・■●◇◆○番号-]*',before):valid.append((tag,t))
 row=dict(id=r['id'],question=r['question'],partition='train'if r in d['parts']['train']else'dev')
 if valid:row['status']='boundary_marker_or_exact_block_match'
 elif c:row.update(status='flag_nonmarker_prefix',tag=c[0][0],source_block=c[0][1]);flag.append(row)
 else:row['status']='unresolved_inline_or_large_container';unresolved.append(r['id'])
 proof.append(row)
(P/'QUESTION_BOUNDARY_AUDIT.json').write_text(json.dumps(dict(cases=len(proof),flags=flag,unresolved=unresolved,rows=proof,method='Smallest source DOM block versus normalized full question; ordinary Q/number labels permitted; flags require individual reading; unresolved is not a pass',timing='post-training supplementary QC; frozen inputs not silently modified'),ensure_ascii=False,indent=2)+'\n');print('flags',flag,'unresolved',len(unresolved))
