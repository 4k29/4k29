import pathlib,json,sys,re,collections,hashlib,urllib.parse
P=pathlib.Path(__file__).parent;V=pathlib.Path('/workspace/4k29/training/language/conversation-v2');sys.path.insert(0,str(V));from new_tokenizer import Encoder
enc=Encoder(json.loads((V/'data/tokenizer.json').read_text()));rs=[json.loads(x)for x in(P/'QUARANTINE/data.jsonl').read_text().splitlines()];out=[];stats=collections.Counter()
for i,r in enumerate(rs):
 if r['copyright']not in ['気象庁','農林水産省','環境省','文部科学省','デジタル庁']:continue
 u=urllib.parse.urlsplit(r['url']);host={'気象庁':['www.jma.go.jp','www.data.jma.go.jp'],'農林水産省':['www.maff.go.jp'],'環境省':['www.env.go.jp'],'文部科学省':['www.mext.go.jp'],'デジタル庁':['www.digital.go.jp']}[r['copyright']]
 if u.netloc not in host:stats['subdomain_hold']+=1;continue
 q,a=r['Question'],r['Answer'];reason=[]
 if '.pdf'in u.path.lower():reason.append('PDF')
 if re.search('https?://|<[^>]+>|図[0-9０-９]|表[0-9０-９]|下記|以下の表|次の図|こちら|別添|別紙|前述|上述|問[0-9０-９]|Q[0-9０-９]|（注|参考文献|出典',q+a):reason.append('missing_reference_or_third_party')
 if re.search('補助金|申請|申告|年金|保険|税額|令和|平成|年度|現在|令[0-9]|改正|医師|治療|診断|放射線量|電話|メール',q+a):reason.append('time_or_highrisk_policy')
 if re.search(r'[\w.+-]+@[\w.-]+\.\w+|0\d{1,3}-\d{2,4}-\d{3,4}',q+a):reason.append('contacts')
 if '\ufffd'in q+a or '\\'in q+a:reason.append('extraction_escape')
 if reason:stats.update(reason);continue
 qt,at=enc(q),enc(a);t=[1,3]+qt+[2,4]+at+[2]
 if len(t)>257:stats['context_overflow']+=1;continue
 if len(at)<12:stats['too_short_retrieval_stratum']+=1;continue
 family=u.netloc+u.path # whole page held together, fragments ignored
 kind='reason'if re.search('なぜ|どうして|理由|原因',q)else'procedure'if re.search('どのように|どうすれ|方法|やり方',q)else'comparison'if re.search('違い|異な|どちら',q)else'condition'if re.search('場合|とき|できますか|可能',q)else'definition'
 out.append(dict(index=i,id='jagov:'+str(i),source=r['copyright'],url=r['url'],family=family,question=q,response=a,tokens=t,response_body_start=4+len(qt),body_tokens=len(at),category_proxy=kind))
(P/'QUARANTINE/CANDIDATES.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
summary={s:dict(cases=sum(r['source']==s for r in out),reply_tokens=sum(r['body_tokens']for r in out if r['source']==s),families=len({r['family']for r in out if r['source']==s}))for s in ['気象庁','農林水産省','環境省','文部科学省','デジタル庁']};(P/'PROFILE.json').write_text(json.dumps(dict(counts=dict(stats),candidate_sources=summary,proxy_not_adoption=True),ensure_ascii=False,indent=2)+'\n');print(summary);print(dict(stats))
