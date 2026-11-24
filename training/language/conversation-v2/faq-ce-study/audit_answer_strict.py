"""Reject source-substring matches that do not reach a real original block ending."""
import pathlib,json,re,html,unicodedata,hashlib
from html.parser import HTMLParser
P=pathlib.Path(__file__).parent;C=P.parent/'faq-ce-clean-study';d=json.loads((C/'DATA.json').read_text());canon=lambda s:''.join(unicodedata.normalize('NFKC',html.unescape(s)).split())
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.text='';self.ends=set();self.starts=set();self.skip=0
 def handle_starttag(self,t,a):
  if t in ['script','style']:self.skip+=1
  if not self.skip and t in ['p','dd','dt','td','th','li','div','h1','h2','h3','h4','h5','h6','section','br','hr']:self.starts.add(len(self.text))
  if not self.skip and t in ['br','hr']:self.ends.add(len(self.text))
 def handle_endtag(self,t):
  if t in ['script','style']:self.skip=max(0,self.skip-1)
  if not self.skip and t in ['p','dd','dt','td','th','li','div','h1','h2','h3','h4','h5','h6','section']:self.ends.add(len(self.text))
 def handle_data(self,s):
  if not self.skip:self.text+=canon(s)
cache={};ok=[];held=[];proof=[]
for part,rs in d['parts'].items():
 for r in rs:
  u=r['url'].split('#')[0]
  if u not in cache:
   b=(P/'QUARANTINE/pages'/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_bytes();m=re.search(br'charset\s*=\s*["\']?([\w-]+)',b[:2000]);cs=m.group(1).decode()if m else'utf-8'
   try:s=b.decode(cs)
   except (UnicodeDecodeError,LookupError):s=b.decode('utf-8',errors='replace')
   z=Parser();z.feed(s);cache[u]=z
  z=cache[u];q,a=canon(r['question']),canon(r['response']);qp=z.text.find(q);ap=z.text.find(a,max(qp+len(q),0));end=ap+len(a);natural=r['response'].rstrip().endswith(('。','！','？','!','?','）',')','」'));block=ap>=0 and end in z.ends;start=ap in z.starts or any(0<=ap-k<=12 and re.fullmatch(r'[AＡa答回答0-9()\[\].、:：?？・■●◇◆○⇒→-]*',z.text[k:ap])for k in z.starts if k<=ap);good=qp>=0 and block and natural and start
  row=dict(id=r['id'],partition=part,source_page_SHA=r['source_page_sha256'],question_offset=qp,answer_offset=ap,answer_end=end,at_original_block_start=start,at_original_block_end=block,natural_terminal=natural,pass_end_contract=good)
  proof.append(row)
  if good:ok.append(r['id'])
  else:held.append(row)
(P/'ANSWER_BOUNDARY_STRICT_AUDIT.json').write_text(json.dumps(dict(method='Normalized full original Q and A, answer end must match original DOM block boundary AND natural punctuation/date closure; no partial-field EOS. List-only block endings conservatively held, not called incorrect.',rows=proof,pass_ids=ok,held=held,cases=len(proof),specific_truncation_rejected=next(x for x in proof if x['id']=='jagov:12541')['pass_end_contract']==False,optimizer_calls=0,model_forwards=0),ensure_ascii=False,indent=2)+'\n');print('pass',len(ok),'held',len(held),'TRAIN',sum(x['pass_end_contract']and x['partition']=='train'for x in proof),'DEV',sum(x['pass_end_contract']and x['partition']=='dev'for x in proof));print('DEV held',[x for x in held if x['partition']=='dev'])
