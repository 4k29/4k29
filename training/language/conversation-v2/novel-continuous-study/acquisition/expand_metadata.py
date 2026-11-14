import os
from metadata import api
import pathlib,json,time
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'))
rows=[]
# Explicit broad nonlegal book roots; metadata only, before prose acquisition.
for prefix in ['料理','中学校','小学校','高等学校','高校','音楽','写真','囲碁','将棋','園芸','生活','家庭','旅','日本語','Wikijunior','地理','心理','学習','スポーツ','美術','絵画','折り紙','釣り','ダンス','ヨガ','教養','社会','情報','経済','マーケティング','読書','文章','コミュニケーション','仕事','インターネット','持続可能','デザイン','習慣','DIY','掃除','洗濯','食']:
 cont={}
 for n in range(10):
  d=api('ja.wikibooks.org',action='query',list='allpages',apprefix=prefix,aplimit=500,apfilterredir='nonredirects',**cont);rows+=d['query']['allpages']
  if'continue'not in d:break
  cont=d['continue'];time.sleep(.4)
 time.sleep(.3)
(C/'books-expanded.titles.json').write_text(json.dumps(list({r['pageid']:r for r in rows}.values()),ensure_ascii=False));print('books',len(rows))
# News metadata avoids politics/crime/legal lists; license separately audited before acquisition.
rows=[];cont={}
for n in range(20):
 d=api('ja.wikinews.org',action='query',list='allpages',aplimit=500,apfilterredir='nonredirects',**cont);rows+=d['query']['allpages']
 if'continue'not in d:break
 cont=d['continue'];time.sleep(.4)
(C/'news.titles.json').write_text(json.dumps(rows,ensure_ascii=False));print('news',len(rows))
