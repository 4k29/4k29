import os
import pathlib,json,re,hashlib,sys
from acquire import snapshot
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'));P=pathlib.Path(__file__).resolve().parents[1];assert(P/'NEW_PROSE_DEV.json').exists();old=json.loads((C/'PRIOR_INDEX.json').read_text());dev=json.loads((P/'DEV_RESERVED_FAMILIES.json').read_text());selection={};held={}
for site,file,oldkey in [('ja.wikibooks.org','books-expanded.titles.json','jawikibooks'),('ja.wikivoyage.org','ja.wikivoyage.org.titles.json','jawikivoyage')]:
 rows=json.loads((C/file).read_text());seenroot={r['title'].split('/')[0]for r in old[oldkey].values()};seenids={int(k.split(':')[1])for k in old[oldkey]};reserve=set(dev['reserved_family'][oldkey]);ok=[];counts={}
 for r in rows:
  title=r['title'];root=title.split('/')[0];reason=None
  if r['pageid']>(30000 if oldkey=='jawikibooks'else 4000):reason='conservative_metadata_age_cap_before_more_fetch'
  elif root in seenroot or r['pageid']in seenids:reason='previous_page_or_root_family'
  elif root in reserve or ('国立公園'in title if oldkey=='jawikivoyage'else False):reason='DEV_reserved_family'
  elif re.search(r'法律|法第|法令|法学|コンメンタール|憲法|判例|数学|算数|化学|物理|生物|理科|プログラ|アセンブリ|Python|Java|C言語|ソフトウェア|言語/|医学|看護|薬学|歴史|戦争|戦役|世界史|日本史|東洋史|中国史|古典|漢文|古文',title):reason='non_target_genre_or_high_risk'
  elif oldkey=='jawikivoyage'and re.search(r'会話集|メインページ|おすすめ|今月|注目|Help|珍しい|日本国$|ノート|方針|Wikivoyage|ユーザー',title):reason='navigation_language_or_portal'
  if reason:counts[reason]=counts.get(reason,0)+1
  else:ok.append(r)
 ok.sort(key=lambda r:hashlib.sha256(('novel-corpus-acquire-v1|'+str(r['pageid'])).encode()).hexdigest());selection[site]=ok;held[site]=counts
(P/'ACQUISITION_SELECTION.json').write_text(json.dumps(dict(selected_pages=selection,metadata_exclusion_counts=held,DEV_SHA=hashlib.sha256((P/'NEW_PROSE_DEV.json').read_bytes()).hexdigest(),no_TRAIN_prose_before_DEV_freeze=True,source_policy='Each fixed pre2022 revision, remove risky quoted/nonprose blocks; wiki human/bot individual authorship not guaranteed'),ensure_ascii=False,indent=2)+'\n');print('metadata_selected',[(k,len(v))for k,v in selection.items()],flush=True)
for site,rows in selection.items():
 out=snapshot(site,rows,'train-raw');print('downloaded',site,len(out),'pre2022found',sum(bool(x['revision'])for x in out),flush=True)
