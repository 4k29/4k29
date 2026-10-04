"""Prepare attributable modern technical Japanese for a subsequent experiment.

This separate corpus does not modify the currently frozen binding experiment.
Documentation prose is CC BY-SA 2.5 or later; extracted data uses CC BY-SA 4.0.
No Wikipedia, model API, code samples, images or outside tokenizer/weights.
"""
import datetime
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request
from collect_web_language import Page,VOID,USER_AGENT
HERE=pathlib.Path(__file__).resolve().parent
POLICY='https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Attrib_copyright_license'
LICENSE='https://creativecommons.org/licenses/by-sa/4.0/'
class Prose(Page):
    def __init__(self):super().__init__();self.finished=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id')=='feedback':self.finished=True
        if tag not in VOID:self.stack.append((tag,a))
        excluded=any(t in ['script','style','nav','header','footer','pre','table'] for t,_ in self.stack)
        if not self.finished and self.scoped() and not excluded and tag in ['h1','h2','h3','p'] and self.block is None:self.block=[tag,len(self.stack),[]]
    def handle_data(self,text):
        if any(t in ['script','style','pre','table'] for t,_ in self.stack):return
        if self.block:self.block[2].append(text)
        if any(t=='title' for t,_ in self.stack):self.title.append(text)
def fetch(url):
    if urllib.parse.urlparse(url).hostname!='developer.mozilla.org':raise ValueError('Source domain is not approved')
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT})
    with urllib.request.urlopen(req,timeout=30) as r:
        if urllib.parse.urlparse(r.url).hostname!='developer.mozilla.org':raise ValueError('Redirect left approved source')
        raw=r.read();headers=dict(finalUrl=r.url,lastModified=r.headers.get('Last-Modified'),contentType=r.headers.get('Content-Type'))
    html=raw.decode('utf-8');page=Prose();page.feed(html);return page,html,raw,headers
def main():
    policy,html,raw,headers=fetch(POLICY)
    policy_digest=hashlib.sha256(raw).hexdigest()
    if 'creativecommons.org/licenses/by-sa/2.5/' not in html or 'any later version' not in html:raise ValueError('Review changed MDN license before collection')
    paths=['JavaScript/Guide/Introduction','JavaScript/Guide/Grammar_and_types','JavaScript/Guide/Control_flow_and_error_handling','JavaScript/Guide/Loops_and_iteration','JavaScript/Guide/Functions','JavaScript/Guide/Expressions_and_operators','JavaScript/Guide/Numbers_and_strings','JavaScript/Guide/Indexed_collections','JavaScript/Guide/Keyed_collections','JavaScript/Guide/Working_with_objects','JavaScript/Guide/Using_classes','JavaScript/Guide/Using_promises','JavaScript/Guide/Modules','JavaScript/Reference/Global_Objects/Array','JavaScript/Reference/Global_Objects/Object','JavaScript/Reference/Global_Objects/String','JavaScript/Reference/Global_Objects/Map','JavaScript/Reference/Global_Objects/Set','JavaScript/Reference/Global_Objects/JSON','JavaScript/Reference/Statements/const','JavaScript/Reference/Statements/let','JavaScript/Reference/Operators/typeof','HTML/Element','HTML/Element/input','HTML/Element/textarea','CSS/color','CSS/font-family','CSS/overflow-wrap','CSS/display','CSS/flex']
    documents=[];sources=[];failed=[]
    for index,path in enumerate(paths):
        url='https://developer.mozilla.org/ja/docs/Web/'+path
        try:page,html,raw,headers=fetch(url)
        except Exception as error:failed.append(dict(url=url,error=str(error)));continue
        blocks=[b for b in page.blocks if not re.search(r'このページは.*変更|MDN の寄稿者|フィードバック|改善する方法|Report feedback',b['text'])]
        text='\n'.join(b['text'] for b in blocks)
        if len(re.findall(r'[一-龯ぁ-ゖァ-ヺ]',text))<500:failed.append(dict(url=url,error='Insufficient Japanese prose'));continue
        partition='test' if index%10==9 else 'validation' if index%10==8 else 'train'
        digest=hashlib.sha256(text.encode()).hexdigest()
        document=dict(id='mdn:'+str(index),site='mdn',url=url,partition=partition,title=''.join(page.title).strip(),blocks=blocks,text=text,textSha256=digest)
        documents.append(document)
        sources.append(dict(id=document['id'],author='MDN contributors',url=url,title=document['title'],partition=partition,license='CC BY-SA 4.0',licenseUrl=LICENSE,originalLicense='CC BY-SA 2.5 or any later version',originalLicenseUrl='https://creativecommons.org/licenses/by-sa/2.5/',policyUrl=POLICY,attribution=document['title']+' — MDN contributors, '+url+'; adapted under CC BY-SA 4.0.',modifications='Extracted main prose and headings, normalized whitespace, excluded code blocks/tables/navigation/feedback. No images or attachments. Not yet used in binding training.',htmlSha256=hashlib.sha256(raw).hexdigest(),textSha256=digest,**headers))
        print(json.dumps(dict(url=url,characters=len(text),partition=partition),ensure_ascii=False),flush=True)
    result=dict(schemaVersion=1,retrievedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),excludedSources=['Wikipedia','pretrained models','generative AI APIs'],status='Prepared raw prose for a subsequent experiment; not part of binding training or its reported results.',license='CC BY-SA 4.0',licenseUrl=LICENSE,policySnapshot=dict(url=POLICY,htmlSha256=policy_digest,paragraphs=policy.blocks),documents=len(documents),characters=sum(len(d['text']) for d in documents),partitions={p:sum(d['partition']==p for d in documents) for p in ['train','validation','test']},sources=sources,failed=failed)
    (HERE/'mdn-language-documents.jsonl').write_text('\n'.join(json.dumps(d,ensure_ascii=False,separators=(',',':')) for d in documents)+'\n')
    (HERE/'mdn-language-sources.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['documents','characters','partitions','failed']},ensure_ascii=False))
if __name__=='__main__':main()
