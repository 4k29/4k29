import os
import json,pathlib,urllib.request,urllib.parse,time,hashlib,concurrent.futures
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'))
UA='ConversationV2CorpusResearch/1.0 (https://github.com/4k29/4k29; noncommercial research; sequential requests)'
def get(u):
 return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=30).read()
def api(site,**kw):return json.loads(get('https://'+site+'/w/api.php?'+urllib.parse.urlencode(dict(format='json',**kw))))
def one(site):
 rows=[];cont={}
 for n in range(20):
  d=api(site,action='query',list='allpages',aplimit=500,apnamespace=0,**cont);rows+=d['query']['allpages']
  if'continue'not in d:break
  cont=d['continue'];time.sleep(1)
 (C/(site+'.titles.json')).write_text(json.dumps(rows,ensure_ascii=False));return site,len(rows),[x['title']for x in rows if any(k in x['title']for k in ['料理','旅行保険','荷造','キャンプ','温泉','買い物','健康','ハイキング','旅の基本'])][:70]
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=1)as e:print(list(e.map(one,['ja.wikibooks.org','ja.wikivoyage.org'])))
