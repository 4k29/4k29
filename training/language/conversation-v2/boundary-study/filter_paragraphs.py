import collections,re
from common import *
from prepare import rank

def main():
 d=json.loads((N/'paragraph-candidates.json').read_text());sample=json.loads((N/'paragraph-review.json').read_text());held={sample[i]['id']:r for i,r in {1:'unbound 他にも and categorical fraud claims',2:'page meta-text and unfulfilled recipe promise',3:'time-sensitive future spaceflight claim',4:'overstated guaranteed game advantage',6:'list rather than coherent paragraph',8:'bad translation and external events pointer',10:'unverified water safety advice',13:'missing phrase 揚げ餃子や楽しめます and unstable ranking',14:'current legal speed advice',15:'unverified geopolitical safety advice',16:'unnatural translated dialect claims',17:'unverified historical population claim',18:'unverified specific routes and current operation',20:'2021 current train schedule not current advice',22:'ungrammatical and historically uncertain prison narrative'}.items()};counts=collections.Counter();out={}
 for split,rows in d.items():
  kept=[]
  for r in rows:
   s=r['text'];reason=held.get(r['id'])
   if not reason and re.search(r'このページ|この記事|ご紹介|目次|詐欺|名簿屋|打ち上げ|予定|計画|飲料水|水道水|速度制限|警戒|刑務所|国道\d|インターチェンジ|号線|発着|運行|日本一',s):reason='meta/list/current advisory or unverifiable specificity guard'
   if not reason and(re.match(r'^(他にも|ここでは)',s)or s.count('：')>=3):reason='unbound continuation or list'
   if reason:counts[reason]+=1;continue
   kept.append(r)
  out[split]=kept
 write(N/'paragraph-filtered.json',out);write(N/'PARAGRAPH_REVIEW.json',dict(reviewer='main assistant only, not independent native human',initial_sample_count=len(sample),all_initial_sample_read=True,held=held,reason='New EOS requires whole source paragraph AND standalone semantic/quality review, punctuation alone insufficient',source_rights='PR101 bounded admission/source-specific licenses retained',remaining='No full authorship certification or exhaustive fact check; no rewrite of source',counts=dict(counts)))
 new=sorted(out['train'],key=lambda r:rank('postfilter|'+r['id']))[:16];write(N/'paragraph-validation.json',new);print('filtered',[(k,len(v),sum(len(r['body_tokens'])for r in v))for k,v in out.items()])
 for i,r in enumerate(new):print(i,r['id'],r['title'],r['text'])
if __name__=='__main__':main()
