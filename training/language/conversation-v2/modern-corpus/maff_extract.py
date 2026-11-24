"""Reuse previously audited MAFF answer-section parser, without acquisition side effects.
Origin: diverse-foundation/future_maff.py Article; source text never paraphrased.
"""
from html.parser import HTMLParser
import re
class Article(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.depth=0;self.start=None;self.tag=None;self.buf=[];self.title='';self.paragraphs=[];self.done=False
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='div':
   self.depth+=1
   if a.get('class')=='content_left':self.start=self.depth
  if self.start is None or self.done:return
  if t in ['h1','h2','h3','p','li']:self.tag=t;self.buf=[]
 def handle_endtag(self,t):
  if t=='div':
   if self.start==self.depth:self.start=None
   self.depth-=1
  if t==self.tag:
   s=''.join(self.buf).strip();self.tag=None
   if re.match('参考資料|お問い合わせ|お問合せ|出典|関連情報',s):self.done=True;return
   if t=='h1':self.title=s
   elif t in ['p','li']and s:self.paragraphs.append(s)
 def handle_data(self,s):
  if self.start is not None and self.tag and not self.done:self.buf.append(s)
