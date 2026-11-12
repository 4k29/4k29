"""Retrieve actual operator replies, not customer preferences; official TRAIN/DEV only."""
import pathlib,json,re,hashlib,sys,collections,unicodedata
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path('/workspace/4k29/training/language/conversation-v2');sys.path.insert(0,str(V));from new_tokenizer import Encoder
T=json.loads((V/'data/tokenizer.json').read_text());enc=Encoder(T);pieces=[bytes.fromhex(t)for t in T['bytes']];records=json.loads((P/'PRIVATE/RECORDS.json').read_text());out=[];counts=collections.Counter();seen={}
canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split()).casefold()
# Retrieval is deliberately narrow. All semantic adoption still requires original-QA reading.
for r in records:
 us=r['utterances'];tokens=[1];history=[]
 for i,u in enumerate(us):
  ids=enc(u['text']);assert b''.join(pieces[t]for t in ids)==u['text'].encode();start=len(tokens)+1;tokens += [4 if u['role']=='agent'else 3]+ids+[2];history.append(u)
  if u['role']!='agent'or i==0 or us[i-1]['role']!='user':continue
  counts['true_agent_reply_positions']+=1
  if len(tokens)>257:counts['full_history_context_overflow']+=1;continue
  if not 24<=len(ids)<=100:continue
  text='\n'.join(q['text']for q in history)
  if re.search(r'https?://|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b0\d{1,3}-\d{2,4}-\d{3,4}\b|[▁│]',text):counts['technical_privacy_marker_hold']+=1;continue
  if not re.search('[?？]|でしょうか|ますか|ですか|教えて|お聞かせ|お伺い',u['text']):continue
  # Do not learn unsupported hotel inventory/facility assertions, even in earlier all-CE history.
  if any(re.search('ございます|ご用意|完備|対応しており|利用できま|付いており|備えて|当ホテル|当館|この宿|こちらのホテル|可能でございます|提供して',z['text'])and not re.search('[?？]|でしょうか|ますか|ですか',z['text'])for z in history if z['role']=='agent'):counts['possible_DB_assertion_hold']+=1;continue
  key=hashlib.sha256(canon('\n'.join(z['text']for z in history)).encode()).hexdigest()
  if key in seen:counts['exact_case_duplicate']+=1;continue
  id0=r['id']['id']if isinstance(r['id'],dict)else r['id'];parent=r['meta'].get('original_doc_id',r['meta'].get('original_id',id0));topic=r['meta'].get('topic','main'if r['file'].startswith('data/main')else r['file'].split('/')[-1].split('.')[0]);row=dict(id=id0+':agent:'+str(i),document=id0,family=parent,partition=r['partition'],source_file=r['file'],topic=topic,history=history[:-1],response=u['text'],tokens=tokens[:],response_body_start=start,body_tokens=len(ids),original_ordinal=i,original_speaker=u['original_name'],author_ids_available=r['file'].startswith('data/main'),source_roles_preserved=True,license='CC-BY-4.0',source_revision='f37d6575c73602adcb8ae3687520726793baa672',retrieval_proxy_only=True)
  seen[key]=row['id'];out.append(row)
# One response per original/extended family to avoid repeating causal teacher positions.
seed='public-dialogue-agent-v1';selected=[];by={};
for part in ['train','dev']:
 pool=[r for r in out if r['partition']==part];groups=collections.defaultdict(list)
 for r in pool:groups[r['topic']].append(r)
 seenfamily=set();n=0
 for topic in sorted(groups):
  rr=sorted(groups[topic],key=lambda r:hashlib.sha256((seed+'|'+r['id']).encode()).hexdigest())
  quota=12 if part=='train'else 3
  for r in rr:
   if r['family']in seenfamily:continue
   selected.append(r);seenfamily.add(r['family']);n+=1;quota-=1
   if quota==0:break
 by[part]=dict(pool=len(pool),topics=len(groups),selected=n)
(P/'PRIVATE/CANDIDATES.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')));(P/'PRIVATE/REVIEW_CARDS.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2));(P/'RETRIEVAL.json').write_text(json.dumps(dict(seed=seed,counts=dict(counts),partitions=by,selection=[{k:r[k]for k in ['id','family','partition','source_file','topic','body_tokens']}for r in selected],optimizer_updates=0,model_forwards=0,proxy_not_semantic_adoption=True),indent=2)+'\n');print(dict(counts));print(by);print('selection topic counts',dict(collections.Counter((r['partition'],r['topic'])for r in selected)))
