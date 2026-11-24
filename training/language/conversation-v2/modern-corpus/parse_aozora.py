"""Source main_text extraction, no spelling modernization or generated repair."""
from html.parser import HTMLParser
import pathlib,json,gzip,hashlib,re
D=pathlib.Path(__file__).resolve().parent
class MainText(HTMLParser):
 def __init__(self):super().__init__();self.depth=0;self.ignore=0;self.parts=[];self.closed=False;self.gaiji=0
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='div':
   if self.depth:self.depth+=1
   elif'main_text'in a.get('class','').split():self.depth=1
  if not self.depth:return
  if t in ['rt','rp']:self.ignore+=1
  if t=='img'and'gaiji'in a.get('class',''):self.gaiji+=1
  if t=='br'and not self.ignore:self.parts.append('\n')
 def handle_endtag(self,t):
  if t in ['rt','rp']and self.ignore:self.ignore-=1
  if t=='div'and self.depth:
   self.depth-=1
   if not self.depth:self.closed=True
 def handle_data(self,s):
  if self.depth and not self.ignore:self.parts.append(s)
def main():
 selected=json.loads((D/'AOZORA_PILOT_SELECTION.json').read_text())['selected'];receipts={r['name']:r for r in json.loads((D/'AOZORA_ACQUISITION.json').read_text())};rows=[]
 for r in selected:
  receipt=receipts[r['作品ID']+'-work'];b=gzip.decompress((D/receipt['local_snapshot']).read_bytes());assert hashlib.sha256(b).hexdigest()==receipt['sha256'];encoding=r['XHTML/HTMLファイル符号化方式'];s=b.decode(encoding);parser=MainText();parser.feed(s);text=''.join(parser.parts).strip();assert text and parser.closed
  rows.append(dict(id=r['作品ID'],title=r['作品名'],author=r['姓']+r['名'],text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),source=receipt,first_publication=r['初出'],orthography=r['文字遣い種別'],work_PD_flag=r['作品著作権フラグ'],person_PD_flag=r['人物著作権フラグ'],gaiji_images=parser.gaiji,original_main_region_complete=parser.closed,admission='candidate pending era/style/rights/quality/split review',EOS_approved=False))
 with gzip.open(D/'private/aozora-candidates.jsonl.gz','wt')as f:
  for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 summary=dict(works=len(rows),characters=sum(len(r['text'])for r in rows),authors=len({r['author']for r in rows}),gaiji_affected_works=sum(bool(r['gaiji_images'])for r in rows),admitted_tokens=0,optimizer_updates=0,processing='Original main_text order, ruby rt/rp excluded, br to newline, no paraphrase, no modern spelling replacement; bibliographic footer excluded; unknown gaiji requires hold')
 (D/'AOZORA_EXTRACTION.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(summary)
 for r in rows:print(r['id'],r['title'],'characters',len(r['text']),'publication',r['first_publication'],'opening',r['text'][:550])
if __name__=='__main__':main()
