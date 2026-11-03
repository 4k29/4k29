"""Original ordered HTML prose events. No sentence repair or cross-gap joining."""
from html.parser import HTMLParser
import re,hashlib
VOID={'br','hr','img','meta','link','input','source','wbr','area','base','embed'}
class Paragraphs(HTMLParser):
 def __init__(self,root_id='main'):
  super().__init__(convert_charrefs=True);self.root_id=root_id;self.stack=[];self.events=[];self.current=None;self.heading=None;self.ordinal=0;self.main_marker=False
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs);parent=self.stack[-1]if self.stack else dict(inside=False,blocked=False)
  if self.root_id=='main' and attrs.get('id')=='main':self.main_marker=True
  if self.root_id=='main' and attrs.get('id')=='footer':self.finish();self.main_marker=False
  inside=(self.main_marker if self.root_id=='main' else parent['inside']or attrs.get('id')==self.root_id or(self.root_id=='legacy_body'and tag=='body'))
  classes=set(attrs.get('class','').split());blocked=parent['blocked']or tag in {'script','style','table','blockquote','figure','nav','footer'}or bool(classes&{'column','figblock','fig','caption','source','contact','inquiry'})
  if tag not in VOID:self.stack.append(dict(tag=tag,inside=inside,blocked=blocked))
  if not inside:return
  if blocked and not parent['blocked']:
   if self.current:self.current['blocked']=True
   else:self.events.append(dict(kind='barrier',reason='omitted_DOM_block'))
  if tag=='li':self.finish();self.events.append(dict(kind='barrier',reason='independent_list_item'))
  if tag in {'h1','h2','h3','h4','h5','h6'}:
   self.finish();self.heading=dict(kind='heading',level=int(tag[1]),parts=[],blocked=blocked)
  elif tag=='p':
   self.finish();self.ordinal+=1;self.current=dict(kind='paragraph',index=self.ordinal,parts=[],blocked=blocked,has_image=False,external_links=[])
  elif tag=='img':
   if self.current:self.current['has_image']=True
   else:self.events.append(dict(kind='barrier',reason='omitted_image'))
  elif tag=='br'and self.current:self.current['parts'].append('\n')
  elif tag=='a'and self.current:
   href=attrs.get('href','')
   if href:self.current['external_links'].append(href)
 def handle_endtag(self,tag):
  if tag=='p':self.finish()
  if tag in {'h1','h2','h3','h4','h5','h6'}and self.heading:
   h=self.heading;self.heading=None;text=self.clean(h.pop('parts'));h['text']=text;self.events.append(h)
  matches=[i for i,x in enumerate(self.stack)if x['tag']==tag]
  if matches:self.stack=self.stack[:matches[-1]]
 def handle_data(self,text):
  if self.current:self.current['parts'].append(text)
  elif self.heading:self.heading['parts'].append(text)
 def finish(self):
  if self.current:
   p=self.current;self.current=None;p['text']=self.clean(p.pop('parts'));p['sha256']=hashlib.sha256(p['text'].encode()).hexdigest();self.events.append(p)
 @staticmethod
 def clean(parts):return re.sub(r'[ \t\r\n]+',' ',''.join(parts)).strip()

def exclusion(event):
 text=event.get('text','')
 if event.get('blocked'):return 'excluded_DOM_third_party_or_nonprose'
 if event.get('has_image'):return 'embedded_image_dependency'
 if len(text)<30:return 'short_fragment'
 if re.match(r'^\s*(?:\[\d+\]|[（(]\d+[）)]|[①②③④⑤⑥⑦⑧⑨⑩])',text):return 'numbered_list_not_continuous_prose'
 if re.search(r'図[0-9０-９一二三四五六七八九十]|図表|図を参照',text)or any(x in text for x in ['写真','下記','上記','前述','後述','以下のとおり','次のとおり','資料：','資料:','出典','問い合わせ','問合せ','電話番号','リンク先','マップをご覧']):return 'external_or_omitted_context_dependency'
 if re.search(r'https?://|[\w.+-]+@[\w.-]+|\d{2,4}[-－]\d{2,4}[-－]\d{3,4}',text):return 'contact_or_URL'
 if re.search(r'「[^」]{20,}」|“[^”]{20,}”|と語|と述べ|氏は|インタビュー',text):return 'quotation_or_attributed_voice'
 if len(re.findall(r'法律第|法第.{0,12}条|施行令|施行規則|閣議決定|予算額|条約第',text))>=2:return 'legal_dense'
 if sum(c.isdigit()for c in text)/len(text)>.085:return 'number_dense'
 if not re.search(r'[。！？]$',text):return 'unfinished_paragraph'
 return None

def units(events):
 """Consecutive original paragraphs under one original heading; hold gaps are barriers."""
 result=[];block=[];heading='';reasons={};serial=0;at_section_start=True;block_section_start=False
 def flush(natural_end):
  nonlocal block,serial
  if not block:return
  body='\n\n'.join(p['text']for p in block);serial+=1
  independent=not re.match(r'^(この|その|これ|それ|また|したがって|さらに|こうした|これら|これまで|例えば)',block[0]['text'])
  if body.count('。')>=3 and independent:
   result.append(dict(text=body,heading=heading,paragraph_indices=[p['index']for p in block],BOS=block_section_start,EOS=natural_end,original_section_start=block_section_start,original_section_end=natural_end,serial=serial))
  else:reasons['insufficient_sentences_or_initial_context_dependency']=reasons.get('insufficient_sentences_or_initial_context_dependency',0)+1
  block=[]
 for event in events:
  if event['kind']=='barrier':flush(False);at_section_start=False;continue
  if event['kind']=='heading':
   flush(not event.get('blocked',False))
   if not event.get('blocked',False):heading=event['text'];at_section_start=True
   else:at_section_start=False
   continue
  why=exclusion(event)
  if why:flush(False);at_section_start=False;reasons[why]=reasons.get(why,0)+1
  else:
   if not block:block_section_start=at_section_start
   block.append(event);at_section_start=False
 flush(True)
 return result,reasons
