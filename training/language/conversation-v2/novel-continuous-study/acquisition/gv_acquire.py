import os
import json,pathlib,re,sys,time,hashlib,html
from metadata import get
from bs4 import BeautifulSoup
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'));P=pathlib.Path(__file__).resolve().parents[1];assert(P/'NEW_PROSE_DEV.json').exists()
cats=[]
for page in range(1,6):
 try:cats+=json.loads(get(f'https://jp.globalvoices.org/wp-json/wp/v2/categories?per_page=100&page={page}'))
 except Exception:break
(C/'gv-categories.json').write_text(json.dumps(cats,ensure_ascii=False));allow={r['id']for r in cats if r['slug']in ['arts-culture','food','travel','music','film','photography','literature','sports','science','education','language','environment','humor']};old=json.loads((C/'gv-old-census.json').read_text());chosen=[]
for r in old:
 if r['date_gmt']>='2022-01-01'or r['modified_gmt']>='2022-01-01':continue
 if not(allow.intersection(r['categories'])or re.search('料理|食文化|コーヒー|お茶|伝統|美術|写真|音楽|読書|祭り|旅行|趣味|博物館',r['title'])):continue
 if re.search('戦争|紛争|虐殺|殺害|殺人|自殺|暴力|暴行|選挙|独裁|政府|迫害|難民|コロナ|感染|病気|薬|ガザ|パレスチナ|ウイグル|ロックダウン|LGBT|レイプ|セックス|性別|ジェンダー|政治|抗議|人権|差別|テロ|麻薬',r['title']):continue
 if r.get('whole_article_hold'):continue
 chosen.append(r)
chosen.sort(key=lambda r:hashlib.sha256(('new-GV-v1|'+str(r['id'])).encode()).hexdigest());(P/'GV_ACQUISITION_SELECTION.json').write_text(json.dumps(dict(selected_ids=[r['id']for r in chosen],selected_count=len(chosen),category_allow=sorted(allow),pre2022_modified_required=True,TRAIN_in_all_prior_runs=0,old_census_SHA=hashlib.sha256((C/'gv-old-census.json').read_bytes()).hexdigest(),license_policy='Official Japanese republication page CC BY3.0 covers articles/translations; retain article, author, translator, original GV link; exclude all embedded/quoted/third-party material, attributed introductions and lacking-context paragraphs. No assumption that every article paragraph passes.'),ensure_ascii=False,indent=2)+'\n');print('GV selected',len(chosen),'categories',[(r['id'],r['slug'])for r in cats if r['id']in allow],flush=True)
out=C/'gv-raw';out.mkdir(exist_ok=True)
for i,r in enumerate(chosen):
 f=out/f"{r['id']}.json";web=out/f"{r['id']}.html"
 if f.exists()and web.exists():continue
 try:
  b=get('https://jp.globalvoices.org/wp-json/wp/v2/posts/'+str(r['id']));d=json.loads(b)
  if d['modified_gmt']>='2022-01-01':f.write_bytes(b);continue
  f.write_bytes(b);web.write_bytes(get(d['link']));time.sleep(.35)
  if i%50==0:print('GV progress',i,flush=True)
 except Exception as e:
  (out/'ERRORS.jsonl').open('a').write(json.dumps(dict(id=r['id'],error=str(e)))+'\n');print('GV stopped',i,str(e),flush=True);break
