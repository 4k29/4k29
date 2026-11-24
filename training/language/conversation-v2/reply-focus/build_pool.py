"""TRAIN-wide syntactic retrieval, no automatic semantic quality certification."""
import array,collections,gzip,hashlib,importlib.util,json,pathlib,re
H=pathlib.Path(__file__).resolve().parent;V=H.parent
ACK=re.compile(r'^(はい|うん|ええ|そうですね|そうです|なるほど|いいですね|わかりました|ありがとう(?:ございます)?|こんにちは|こんばんは|おはよう(?:ございます)?|よろしく(?:お願いします)?|笑|w|[!！?？。 、…😊])+[!！?？。 、…]*$')
TOPICS={'food':'料理|食べ|ご飯|寿司|ケーキ|アイス|野菜|パスタ','travel':'旅行|観光|温泉|ホテル|海外','media':'映画|ドラマ|アニメ|漫画|テレビ','music':'音楽|歌|バンド|ラップ|K-pop','games':'ゲーム|プレステ|ドラクエ|Switch','sports':'サッカー|野球|スポーツ|運動|筋トレ','pets':'ペット|犬|猫|めだか','work':'仕事|職場|勤務|転職','shopping':'買い物|洋服|ブランド|通販|ショッピング','education':'学校|大学|勉強|授業|資格','weather':'天気|暑|寒|台風|エアコン','other':r'(?!)'}
def rank(s):return hashlib.sha256(('reply-focus-v1|'+s).encode()).hexdigest()
def write(n,d):(H/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 path=V/'data/train.docs.jsonl';docs=[json.loads(l)for l in path.open()];meta=json.loads((V/'data/data.json').read_text());pol=json.loads((V/'sns-data/pipeline/publication-policy.json').read_text());sensitive=re.compile(pol['sensitive_topic_regex']);old=set(json.loads((V/'allocation-study/PLAN.json').read_text())['ids'])
 spec=importlib.util.spec_from_file_location('own',V/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);enc=m.Encoder(json.loads((V/'data/tokenizer.json').read_text()));windows=meta['trainWindows'];bydoc=collections.defaultdict(list)
 for i,w in enumerate(windows):bydoc[w['document']].append(i)
 candidates=[];ordinary=[];counter=collections.Counter();allmeta=[];review={}
 for d in docs:
  us=d['utterances'];text='\n'.join(u['text']for u in us);hold=bool(sensitive.search(text)or re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|https?://',text));genre=next((k for k,p in TOPICS.items()if re.search(p,text)),'other');counter['documents']+=1
  if hold:counter['common_privacy_topic_hold_docs']+=1
  pos=1;bounds=[]
  for u in us:
   n=len(enc(u['text']));bounds.append((pos,pos+n+2));pos+=n+2
  for j,(a,b)in enumerate(zip(us,us[1:]),1):
   if a['speakerId']==b['speakerId']:continue
   tags=[]
   if re.search('[?？]',a['text']):tags.append('question-answer')
   if re.search('なぜ|どうして|理由',a['text'])and re.search('から|ので|ため',b['text']):tags.append('reason')
   if re.search('どちら|どっち|比べ',a['text']):tags.append('comparison')
   if re.search('なら|場合|とき',a['text'])and not ACK.fullmatch(b['text'].strip()):tags.append('condition')
   nonack=not bool(ACK.fullmatch(b['text'].strip()));focus=bool(tags and nonack and re.search('[ぁ-んァ-ヶ一-龯]',b['text']))
   row={'id':d['id']+':'+str(j),'document':d['id'],'turn':j,'family':d['normalizedDocumentFamily'],'speakers':d['speakers'],'genre_proxy':genre,'retrieval_tags':tags,'focus_proxy':focus,'ack_proxy':not nonack,'common_hold':hold,'parent_sha256':hashlib.sha256(a['text'].encode()).hexdigest(),'reply_sha256':hashlib.sha256(b['text'].encode()).hexdigest()}
   counter['different_speaker_pairs']+=1;counter['focus_proxy_pairs']+=focus;counter['ack_proxy_pairs']+=not nonack
   eligible=not hold and d['id']not in old
   if eligible:
    ordinary.append(row)
    if focus:candidates.append(row)
   allmeta.append(row)
  if not hold and d['id']not in old:
   for k in bydoc[d['id']]:review[k]={'document':d['id'],'genre':genre,'family':d['normalizedDocumentFamily'],'speakers':d['speakers']}
 # Fixed small semantic calibration samples, one reply/family, before any new generated results.
 samples={}
 for name,pool in [('focus',candidates),('ordinary',ordinary)]:
  picked=[];seen=set()
  for r in sorted(pool,key=lambda r:rank(name+'|'+r['id'])):
   if r['family']in seen:continue
   picked.append(r);seen.add(r['family'])
   if len(picked)==20:break
  samples[name]=picked
 with (H/'retrieval-metadata.jsonl.gz').open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for r in allmeta:z.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 write('RETRIEVAL.json',{'counts':dict(counter),'eligible_focus_pairs':len(candidates),'eligible_ordinary_pairs':len(ordinary),'eligible_window_count':len(review),'samples':samples,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'semantic_acceptance_automatic':False,'privacy_filter_same_in_both_pools':True,'prior20pilot_documents_excluded':True,'retrieval_does_not_remove_short_specific_replies':True})
 write('eligible-windows.json',{str(k):v for k,v in review.items()});print(dict(counter),len(candidates),len(review))
if __name__=='__main__':main()
