"""Bounded exploratory admission candidates; reused source audit, no model learning."""
import collections,gzip,hashlib,importlib.util,json,pathlib,re,unicodedata
H=pathlib.Path(__file__).resolve().parent;V=H.parent;F=V/'foundation-data'
def rank(s):return hashlib.sha256(('modern-foundation-v1|'+s).encode()).hexdigest()
spec=importlib.util.spec_from_file_location('own_bpe',V/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
BOOK=re.compile(r'^(料理本|学習方法|独学ガイド|高校受験ガイド|小学校理科|中学校理科 第[12]分野|中学校社会 地理|中学校社会 歴史|高等学校生物|高等学校美術I|中学校保健体育|高等学校保健体育|小学校家庭科|将棋|囲碁|園芸|家庭|音楽|天体観測|Wikijunior:太陽系)$')
JA=re.compile(r'コーヒー|ワイン|生物|動物|ヤマネコ|ハッカ|テリア|ウナギ|オウム|カジキ|藻|魚|鳥|植物|白菜|和紙|杉原紙|宇宙|地球|惑星|木星|水星|オーロラ|彗星|鉄道|電車|トンネル|橋|電力|発電|電気|変電所|貨幣|貿易|三貨|時計|玩具|蜂蜜|茶|うどん|焼そば|もつ煮|牛汁|焼酎|図書館|美術館|博物館|建築|気候|海|遺産|温泉|山|島|公園|湾|湖|川|言語|日本語|建物|交通|軌間|石炭|紙|砂|地理|作物|農業|科学技術史|祭|オリンピック|黄砂|雨氷|アフリカ|アトランタ|ワシントン|アウクスブルク|アルゼンチン|カタルーニャ|アクロン|ローリー|ローテンブルク|カリフォルニア')
BAD_TITLE=re.compile(r'メインページ|一覧|古文|古典|法第|事件|殺人|虐殺|戦争|死刑|事故|災害|震災|精神|障害|感染|医療|病|薬|ワクチン|ウイルス|聖書|歌詞|詩集|漫画|ゲーム|アイルノーツ|ユメミライ')
BAD_TEXT=re.compile(r'https?://|www\.|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:\d[ -]?){9,}|住所[：:]|電話[：:]|無断転載|引用[：:]|歌詞|ChatGPT|OpenAI|生成AI|\b(?:def|class|return|printf)\b|[{}<>]|[「『][^」』]{25,}[」』]')
def eligible(text):
 if not 90<=len(text)<=2400:return 'length'
 if BAD_TEXT.search(text):return 'privacy_quote_code_or_AI_marker'
 if text.count('。')<2:return 'not_continuous_sentences'
 if sum('ぁ'<=c<='ゖ'for c in text)/len(text)<.15:return 'low_hiragana'
 if text[-1]not in '。！？':return 'incomplete_end'
 if any(text.count(a)!=text.count(b)for a,b in [('「','」'),('『','』'),('（','）')]):return 'unbalanced_fragment'
 return None
def main():
 tok=json.loads((V/'data/tokenizer.json').read_text());enc=m.Encoder(tok);c=collections.Counter();docs=[]
 source_sha=hashlib.sha256((F/'corpus/documents.jsonl.gz').read_bytes()).hexdigest()
 for l in gzip.open(F/'corpus/documents.jsonl.gz','rt'):
  d=json.loads(l);s=d['source']
  if d['split']not in ['train','dev']:c['reserve_not_used']+=1;continue
  if BAD_TITLE.search(d['title']):c['title_hold']+=1;continue
  if s=='jaquad'and not JA.search(d['title']):c['topic_not_selected']+=1;continue
  if s=='jawikibooks'and not BOOK.fullmatch(d['family'].split('|',1)[-1]):c['topic_not_selected']+=1;continue
  if s!='jaquad'and('bot'in d['lastContributorUsername'].lower()or not d['lastContributorId']):c['bot_or_missing_last_author']+=1;continue
  selected=[]
  for p in d['paragraphs']:
   if not p['keepForCandidateTraining']:c['old_dedup_removed']+=1;continue
   text=p['normalizedText'];reason=eligible(text)
   if reason:c[reason]+=1;continue
   selected.append(p)
  if selected:docs.append((d,selected))
 # Freeze source/family caps before model evaluation; do not target a desired result.
 cap={'jaquad':650000,'jawikibooks':550000,'jawikivoyage':400000};used=collections.Counter();family=collections.Counter();chosen=[]
 for d,ps in sorted(docs,key=lambda x:rank(x[0]['id'])):
  keep=[]
  for p in ps:
   n=p['ownBpeTokens'];k=(d['split'],d['source']);fk=(d['split'],d['family'])
   if d['split']=='train'and(used[k]+n>cap[d['source']]or family[fk]+n>100000):c['source_or_family_cap']+=1;continue
   used[k]+=n;family[fk]+=n;keep.append(p)
  if keep:chosen.append((d,keep))
 train_authors={(d['source'],d.get('lastContributorId'))for d,p in chosen if d['split']=='train'and d['source']!='jaquad'}
 rows=[];author_holds=0
 for d,ps in chosen:
  if d['split']=='dev'and d['source']!='jaquad'and(d['source'],d.get('lastContributorId'))in train_authors:author_holds+=1;continue
  groups=[]
  for p in ps:
   if d['source']=='jaquad'or not groups or groups[-1][-1]['ordinal']+1!=p['ordinal']:groups.append([p])
   else:groups[-1].append(p)
  for group in groups:
   text='\n\n'.join(p['normalizedText']for p in group);ids=enc(text);begin=d['source']!='jaquad'and group[0]['ordinal']==0;end=d['source']!='jaquad'and group[-1]['ordinal']==len(d['paragraphs'])-1
   sequence=([1]if begin else[])+ids+([2]if end else[])
   provenance={k:v for k,v in d.items()if k not in ['paragraphs','extractionCounts']}
   rows.append(dict(id=rank(d['id']+'|'+str(group[0]['ordinal'])),source=d['source'],split=d['split'],title=d['title'],family=d['family'],component=d['component'],paragraph_ordinals=[p['ordinal']for p in group],text=text,tokens=sequence,body_tokens=len(ids),true_processed_page_start=begin,true_processed_page_end=end,provenance=provenance))
 rows.sort(key=lambda r:rank(r['id']));out=H/'candidates.jsonl.gz'
 with out.open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for r in rows:z.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 sample=[]
 for split,count in [('train',18),('dev',6)]:
  for source in ['jaquad','jawikibooks','jawikivoyage']:
   pool=[r for r in rows if r['split']==split and r['source']==source];sample+=sorted(pool,key=lambda r:rank('review|'+r['id']))[:count]
 (H/'quality-sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2)+'\n')
 summary=dict(source_corpus_sha256=source_sha,candidate_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),counts=dict(c),source_body_tokens={str(k):v for k,v in used.items()},author_dev_documents_held=author_holds,last_author_overlap_after_filter=0,full_author_independence_unknown=True,jaquad_article_excerpts_no_BOS_or_EOS=True,rows=len(rows),sample=len(sample),status='candidates_pending_fixed_sample_review_no_training')
 (H/'CANDIDATE_AUDIT.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
