import os
import pathlib,json,re,hashlib,html,sys
from bs4 import BeautifulSoup
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'))

def paragraphs(d,web):
 if d['modified_gmt']>='2022-01-01'or d['status']!='publish':return []
 s=BeautifulSoup(web,'html.parser');credits=[]
 for x in s.select('#post-header-credit .contributor-name'):
  a=x.find('a',class_='user-link');label=x.find(class_='credit-label')
  if a:credits.append(dict(role=label.get_text(' ',strip=True)if label else'',name=a.get_text(' ',strip=True),url=a.get('href')))
 originals=[a.get('href')for a in s.select('.post-translation-en a')if a.get('href','').startswith('https://globalvoices.org/')]
 if not originals:originals=[a.get('href')for a in s.select('.post-translations a')if a.get_text(' ',strip=True)=='English'and a.get('href','').startswith('https://globalvoices.org/')]
 if not credits or not any('翻訳'in c['role']for c in credits)or not any('記者'in c['role']for c in credits)or not originals:return []
 if not any('creativecommons.org/licenses/by/3.0'in a.get('href','')for a in s.find_all('a')):return []
 soup=BeautifulSoup(d['content']['rendered'],'html.parser');rows=[]
 if re.search('転載|再掲載|提供記事|パートナー|提携|The Conversation|theconversation',soup.get_text(' ',strip=True),re.I):return []
 all_p=soup.find_all('p');top_positions={id(x):i for i,x in enumerate(soup.find_all(recursive=False))}
 for i,p in enumerate(all_p):
  if p.parent is not soup:continue
  if p.find_parent(['blockquote','figure','figcaption','table','ul','ol','pre'])or p.find_parent(class_=re.compile('caption|twitter|instagram|embed|translation|quote')):continue
  if p.find(['img','iframe','video','audio','script','blockquote','code'])or p.get('class')and any(re.search('caption|credit|quote|translation',c)for c in p['class']):continue
  text=p.get_text('',strip=False).strip();text=re.sub(r'\n{2,}','\n',text)
  if not 40<=len(text)<=2400 or len(re.findall('[。！？]',text))<1 or not text.endswith(('。','！','？')):continue
  if re.search(r'「[^」]{24,}」|“[^”]{24,}”|"[^"]{24,}"|引用|転載|翻訳注|訳注|次のよう|こう述べ|語った|述べた|話した|によれば|によると|ツイート|ツイッター|Twitter|インスタ|Facebook|フェイスブック|ブログで|投稿した|動画|写真をご|上の写真|下の写真|映像|こちら|記事を|インタビュー|以下|上述|先述|前述|下記|図表|@|https?://|メール|電話|住所|殺害|虐殺|自殺|暴力|性交|性被害|診断|治療|病気|差別|逮捕|政権|植民地主義|共産|戦争|紛争',text):continue
  if any(a.get('href','').startswith(('https://twitter.com','https://t.co','https://www.facebook.com','https://www.instagram.com'))for a in p.find_all('a')):continue
  if len(re.findall('[A-Za-z]',text))/len(text)>.12 or len(re.findall('[0-9０-９]',text))/len(text)>.08:continue
  # Start expressions requiring unseen quoted/previous context are not standalone excerpts.
  if re.match(r'^(?:このように|そのように|それについて|彼は|彼女は|その結果|しかしながら|それでも|それらは|これらは)',text):continue
  rows.append(dict(id=f"globalvoices:{d['id']}:{i}",source='globalvoices_human_translation_new',family=originals[0].rstrip('/'),title=html.unescape(d['title']['rendered']),text=text,paragraph_index=i,top_element_index=top_positions[id(p)],source_url=d['link'],original_GV_URL=originals[0],attribution=credits,revision=d['modified_gmt'],timestamp=d['date_gmt'],retrieved_UTC=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),raw_content_SHA=hashlib.sha256(d['content']['rendered'].encode()).hexdigest(),page_HTML_SHA=hashlib.sha256(web).hexdigest(),raw_paragraph_SHA=hashlib.sha256(str(p).encode()).hexdigest(),text_SHA=hashlib.sha256(text.encode()).hexdigest(),license='CC BY3.0; official Japanese article republication grant; author/translator/article/original GV attribution preserved',sentences=len(re.findall('[。！？]',text)),BOS=True,EOS=(i==len(all_p)-1 and p.parent is soup and p.find_next_sibling()is None),transform='Unquoted standalone original paragraph only; no images/embeds/quotes or their introductions, no joining across omitted paragraphs; HTML display tags stripped and LF1; true EOS only if last standalone paragraph is original content final top-level element, otherwise no EOS.',author_status='Named reporter + credited volunteer Japanese translator; published and last modified before2022. Individual workflow not exhaustively verified; not Japanese-original prose; no model-generated teacher.'))
 groups=[];current=[]
 def finish():
  if not current:return
  first=current[0];last=current[-1];text='\n'.join(r['text']for r in current)
  if len(text)>=80 and sum(r['sentences']for r in current)>=2:
   r=dict(first);r.update(id=first['id']+'-'+str(last['paragraph_index']),text=text,text_SHA=hashlib.sha256(text.encode()).hexdigest(),sentences=sum(z['sentences']for z in current),EOS=last['EOS'],original_paragraph_hashes=[z['raw_paragraph_SHA']for z in current],source_span_positions=[dict(p=z['paragraph_index'],top_element=z['top_element_index'])for z in current],transform='Only adjacent safe top-level original paragraphs, exact order with LF1, hard break at every omitted quote/image/heading/unsafe block; no invented prose, no nonadjacent concatenation. EOS only original article content end.')
   r.pop('raw_paragraph_SHA');groups.append(r)
 for r in rows:
  if current and (r['top_element_index']!=current[-1]['top_element_index']+1 or sum(len(z['text'])for z in current)+len(r['text'])+len(current)>2400):finish();current=[]
  current.append(r)
 finish();return groups
if __name__=='__main__':
 out=[]
 for f in(C/'gv-raw').glob('*.json'):
  if f.name=='ERRORS.jsonl':continue
  web=f.with_suffix('.html')
  if web.exists():out+=paragraphs(json.loads(f.read_text()),web.read_bytes())
 (C/'gv-parsed.json').write_text(json.dumps(out,ensure_ascii=False));print('GV paragraphs',len(out),'chars',sum(len(x['text'])for x in out))
