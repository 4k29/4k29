import os
"""Conservative literal paragraph extraction with original character intervals."""
import pathlib,json,re,hashlib,sys,html,urllib.parse
import mwparserfromhell as mw
SENT=re.compile('[。！？]')
def extract(obj,group=True):
 if not obj['revision']:return []
 rev=obj['revision'];raw=rev['slots']['main']['*'];code=mw.parse(raw);assert str(code)==raw
 unsafe=[];pos=0
 for node in code.nodes:
  st=str(node);end=pos+len(st)
  bad=isinstance(node,mw.nodes.Template)and str(node.name).strip().lower()not in['ruby','ふりがな']
  if isinstance(node,mw.nodes.Tag)and str(node.tag).lower()not in['span','small','font','b','i','em','strong']:bad=True
  if bad:unsafe.append((pos,end))
  pos=end
 assert pos==len(raw)
 splits=list(re.finditer(r'\n\s*\n|(?m:^={1,6}.*?={1,6}\s*$)',raw));bounds=[];last=0
 for d in splits:bounds.append((last,d.start()));last=d.end()
 bounds.append((last,len(raw)));rows=[]
 for i,(start,end)in enumerate(bounds):
  b=raw[start:end].strip()
  if not b or any(a<end and z>start for a,z in unsafe):continue
  if re.search(r'(?m)^\s*[*#;:!|{}]|\[\[(?:File|ファイル|Image|画像|Category|カテゴリ):|https?://|<\s*(?:ref|gallery|table|math|source)|ISBN|引用|転載|無断',b,re.I):continue
  if re.search(r'「[^」]{32,}」|“[^”]{32,}”|[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}',b):continue
  bc=mw.parse(b)
  for node in list(bc.filter_templates()):
   if str(node.name).strip().lower()in['ruby','ふりがな']and node.params:bc.replace(node,str(node.params[0].value))
  for node in list(bc.filter_comments()):bc.replace(node,'')
  plain=html.unescape(bc.strip_code(normalize=True,collapse=False)).strip();plain=re.sub(r'\n{2,}','\n',plain)
  if not 30<=len(plain)<=1800 or len(SENT.findall(plain))<1 or not plain.endswith(('。','）','！','？')):continue
  if re.search(r'(?m)\{\{|\}\}|@@|^\s*[*#;:!|]|\[\[|\]\]|\d{2,4}[-ー]\d{2,4}[-ー]\d{3,4}',plain):continue
  if len(re.findall(r'[A-Za-z]',plain))/len(plain)>.15 or len(re.findall(r'[0-9０-９]',plain))/len(plain)>.1:continue
  rows.append(dict(id=f"{obj['site']}:{obj['pageid']}:{rev['revid']}:{i}",source={'ja.wikibooks.org':'jawikibooks_new','ja.wikivoyage.org':'jawikivoyage_new','ja.wikinews.org':'jawikinews_new'}[obj['site']],site=obj['site'],pageid=obj['pageid'],revision=rev['revid'],timestamp=rev['timestamp'],last_editor=rev.get('user'),last_comment=rev.get('comment'),title=obj['title'],family=obj['title'].split('/')[0],text=plain,paragraph_index=i,original_raw_char_span=[start,end],sentences=len(SENT.findall(plain)),raw_wikitext_SHA=hashlib.sha256(raw.encode()).hexdigest(),raw_paragraph_SHA=hashlib.sha256(raw[start:end].encode()).hexdigest(),text_SHA=hashlib.sha256(plain.encode()).hexdigest(),source_url=f"https://{obj['site']}/w/index.php?oldid={rev['revid']}",history_url=f"https://{obj['site']}/w/index.php?title={urllib.parse.quote(obj['title'])}&action=history",license=obj['license'],retrieved_UTC=obj['retrieved_UTC'],BOS=True,EOS=False,transform='Whole original paragraph only with original character interval. Any overlap with omitted template/math/ref/nonprose excludes entire paragraph. Ruby base/display markup extraction and LF1 only; no fake paragraph EOS.'))
 if not group:return rows
 grouped=[];run=[]
 def flush():
  if not run:return
  first=run[0];last=run[-1];text='\n'.join(r['text']for r in run)
  if len(text)>=60 and sum(r['sentences']for r in run)>=2:
   q=dict(first);q.update(id=first['id']+'-'+str(last['paragraph_index']),text=text,text_SHA=hashlib.sha256(text.encode()).hexdigest(),sentences=sum(r['sentences']for r in run),original_paragraph_spans=[r['original_raw_char_span']for r in run],original_paragraph_hashes=[r['raw_paragraph_SHA']for r in run],original_raw_char_span=[first['original_raw_char_span'][0],last['original_raw_char_span'][1]],transform='Whole adjacent original safe prose paragraphs only; hard break at heading/unsafe/nonprose/omitted paragraph, no nonadjacent concatenation. Original display words/order retained, ruby base, LF1; no fake excerpt EOS.');q.pop('raw_paragraph_SHA');grouped.append(q)
 for r in rows:
  if run:
   gap=raw[run[-1]['original_raw_char_span'][1]:r['original_raw_char_span'][0]]
   if gap.strip()or sum(len(z['text'])for z in run)+len(r['text'])+len(run)>1400:flush();run=[]
  run.append(r)
 flush();return grouped
if __name__=='__main__':
 C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'));sys.path.insert(0,'/workspace/scratch/absorption/repo/training/language/conversation-v2');from new_tokenizer import Encoder
 V=pathlib.Path(__file__).resolve().parents[2];P=V/'novel-continuous-study';e=Encoder(json.loads((V/'data/tokenizer.json').read_text()));pieces=[bytes.fromhex(x)for x in json.loads((V/'data/tokenizer.json').read_text())['bytes']];rr=[]
 for f in sorted((C/'dev-raw').glob('*.json')):
  for r in extract(json.loads(f.read_text())):
   if r['sentences']<3:continue
   ts=[1]+e(r['text']);prefix=[];needle=r['text'][:r['text'].find('。')+1].encode();buf=b''
   for j,t in enumerate(ts):
    buf+=pieces[t]
    if buf==needle:prefix=ts[:j+1];break
    if len(buf)>len(needle):break
   if not 12<=len(prefix)<=112 or len(ts)-len(prefix)<24:continue
   r.update(tokens=ts,prefix=prefix,maxNewTokens=min(128,256-len(prefix)),teacher_continuation=ts[len(prefix):len(prefix)+32],rubric='New2–3coherent sentences excluding supplied first sentence; topic and causal/procedural relation retained, natural EOS and repetition separately scored; alternative continuation allowed',independent_TEST=False);rr.append(r)
 rr.sort(key=lambda r:hashlib.sha256(('novel-continuous-dev-v1|'+r['id']).encode()).hexdigest());seen={};selected=[]
 for r in rr:
  key=(r['site'],r['family']);n=seen.get(key,0)
  if n>=4 or sum(x['site']==r['site']for x in selected)>=8:continue
  seen[key]=n+1;selected.append(r)
 (P/'NEW_PROSE_DEV-all.json').write_text(json.dumps(dict(cases=rr),ensure_ascii=False,indent=2)+'\n')
 (P/'NEW_PROSE_DEV-candidates.json').write_text(json.dumps(dict(cases=selected,eligible=len(rr),selection_seed='novel-continuous-dev-v1',before_TRAIN_acquisition=True),ensure_ascii=False,indent=2)+'\n');print('DEV',len(selected),'eligible',len(rr))
 for r in selected:print(r['id'],r['title'],r['text'])
