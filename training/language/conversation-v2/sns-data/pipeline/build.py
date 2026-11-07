"""Preserve published human chat structure; never infer reply parents from addressees."""
import collections,gzip,hashlib,importlib.util,json,pathlib,re,unicodedata
HERE=pathlib.Path(__file__).resolve().parents[1]; V2=HERE.parent

def sha(x):return hashlib.sha256(x).hexdigest()
def anon(source,value):return sha((source+'|'+value).encode())[:24]
def canonical(text):return re.sub(r'\s+','',unicodedata.normalize('NFC',text))
ACK=re.compile(r'^(はい|うん|ええ|そう(です|なんです|なんですね|ですね|なんだ|だね)?|なるほど|いいですね|わかりま(す|した)|ありがとう(ございます)?|おはよう(ございます)?|こんにちは|こんばんは|よろしく(お願いします)?|笑|w+|[!！?？。 、…]+)+[!！?？。 、…]*$')
PII={'email':r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}','phone':r'(?<!\d)0\d{1,3}[-ー ]\d{2,4}[-ー ]\d{3,4}(?!\d)','url':r'https?://\S+','address':r'(?:都|道|府|県).{1,15}(?:市|区|町).{0,10}\d+(?:丁目|番地|号)'}
def flags(text):
 jp=bool(re.search(r'[ぁ-んァ-ヶ一-龯]',text)); ack=bool(ACK.fullmatch(text.strip()))
 return {'japanese':'script-evidence' if jp else 'ambiguous-not-automatically-rejected','acknowledgement_proxy':ack,'substantive_proxy':jp and len(text.strip())>=12 and not ack,'pii_review':[k for k,p in PII.items()if re.search(p,text)],'advertising_review':bool(re.search(r'(購入はこちら|送料無料|キャンペーン|フォロー.*RT)',text)),'human_authorship':'publisher-human-research-chat-not-detector-proof'}
class Union:
 def __init__(self,ids):self.p={x:x for x in ids}
 def get(self,x):
  while self.p[x]!=x:self.p[x]=self.p[self.p[x]];x=self.p[x]
  return x
 def join(self,a,b):
  a,b=self.get(a),self.get(b)
  if a!=b:self.p[max(a,b)]=min(a,b)
def encode_loader():
 spec=importlib.util.spec_from_file_location('sns_own_encoder',V2/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 tok=json.loads((V2/'data/tokenizer.json').read_text());return m.Encoder(tok),tok

def main():
 receipt=json.loads((HERE/'raw/acquisition.json').read_text());raw=HERE/'raw/mrmpc-dialogues.jsonl.gz';assert sha(raw.read_bytes())==receipt['archiveSha256']
 rows=[json.loads(l)for l in gzip.open(raw,'rt')];docs=[];originals={};enc,tok=encode_loader();vocab=[bytes.fromhex(x)for x in tok['bytes']]
 for row in rows:
  if row.get('withheld'):continue
  d=row['data'];ident='mrmpc:'+d['dialogue_id'];speakers={x:anon('mrmpc',x)for x in d['interlocutors']};turns=[]
  assert len({u['utterance_id']for u in d['utterances']})==len(d['utterances'])
  assert [u['utterance_id']for u in d['utterances']]==list(range(len(d['utterances'])))
  for i,u in enumerate(d['utterances']):
   assert u['interlocutor_id']in speakers and all(s in speakers for s in u['mention_to'])
   text=u['text'];ids=enc(text);assert b''.join(vocab[x]for x in ids)==text.encode()
   turns.append({'id':ident+':'+str(u['utterance_id']),'speaker_id':speakers[u['interlocutor_id']],'text':text,'parent_id':None,'previous_in_order_id':ident+':'+str(i-1)if i else None,'mention_to':[speakers[x]for x in u['mention_to']],'reply_relation':'addressee-only-not-parent'if u['mention_to']else'chronological-only-not-parent','published_at':None,'body_tokens':len(ids),'quality_flags':flags(text),'text_sha256':sha(text.encode())})
  doc={'source':'mrmpc','id':ident,'conversation_id':ident,'conversation_family':'mrmpc:'+d['dialogue_id'][:4],'speakers':sorted(speakers.values()),'published_at':None,'source_url':row['url'],'source_sha256':row['sha256'],'license':'CC-BY-SA-4.0','rights_status':'rights-cleared-quality-pending','metadata':{'dialogue_type':d['dialogue_type'],'role_serialization':'ineligible-more-than-two-speakers'if len(speakers)>2 else'eligible-pending-review','true_reply_parent_available':False,'raw_path':row['path']},'utterances':turns}
  docs.append(doc);originals[ident]='\n'.join(u['text']for u in turns)
 union=Union([d['id']for d in docs]);speaker_first={};family_first={};exact_first={};exact=[]
 for d in docs:
  for key,lookup in [(x,speaker_first)for x in d['speakers']]+[(d['conversation_family'],family_first)]:
   if key in lookup:union.join(d['id'],lookup[key])
   else:lookup[key]=d['id']
  key=sha(canonical(originals[d['id']]).encode())
  if key in exact_first:union.join(d['id'],exact_first[key]);exact.append([exact_first[key],d['id']])
  else:exact_first[key]=d['id']
 # Bounded retrieval followed by exact full-set Jaccard. Not exhaustive semantic dedup.
 grams={k:{v[i:i+5]for i in range(len(v)-4)}for k,v in originals.items()};posts=collections.defaultdict(list);near=[];comparisons=0
 for key,g in grams.items():
  candidates=collections.Counter(x for signature in sorted(g,key=lambda s:sha(s.encode()))[:16]for x in posts[signature])
  for other,n in candidates.items():
   if n<2 or min(len(originals[key]),len(originals[other]))/max(len(originals[key]),len(originals[other]))<.8:continue
   comparisons+=1;j=len(g&grams[other])/len(g|grams[other])
   if j>=.85:union.join(key,other);near.append([other,key,j])
  for sig in sorted(g,key=lambda s:sha(s.encode()))[:16]:posts[sig].append(key)
 comps=collections.defaultdict(list)
 for d in docs:comps[union.get(d['id'])].append(d['id'])
 for d in docs:
  component=union.get(d['id']);bucket=int(sha(('sns-speaker-component-v1|'+component).encode()),16)%100
  d['component']=component;d['split']='DEV'if bucket<15 else'reserve-not-test'if bucket<20 else'TRAIN'
  issues=sorted({p for u in d['utterances']for p in u['quality_flags']['pii_review']})
  d['admission']='hold-multiparty-serialization'if len(d['speakers'])>2 else'hold-quality';d['review_flags']=issues
 out=HERE/'derived/conversations.jsonl.gz'
 with out.open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for d in docs:z.write((json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 stats={'source':'mrmpc','acquired_dialogues':receipt['dialogues'],'public_retained_dialogues':len(docs),'privacy_withheld_dialogues':receipt.get('public_pack_withheld_records',0),'dialogues':len(docs),'utterances':sum(len(d['utterances'])for d in docs),'distinct_source_local_speakers':len(speaker_first),'body_tokens':sum(u['body_tokens']for d in docs for u in d['utterances']),'characters':sum(len(u['text'])for d in docs for u in d['utterances']),'explicit_reply_parent_rate':0,'addressee_is_not_reply_parent':True,'three_or_more_utterance_dialogues':sum(len(d['utterances'])>=3 for d in docs),'two_role_compatible_whole_dialogues':sum(len(d['speakers'])<=2 for d in docs),'speaker_connected_components':len(comps),'components':{k:len(v)for k,v in comps.items()},'split_documents':dict(collections.Counter(d['split']for d in docs)),'split_tokens':dict((s,sum(u['body_tokens']for d in docs if d['split']==s for u in d['utterances']))for s in ['TRAIN','DEV','reserve-not-test']),'whole_context256_fit':sum(1+sum(u['body_tokens']+2 for u in d['utterances'])<=257 for d in docs),'adjacent_pair_context256_fit':sum(sum(x['body_tokens']+2 for x in d['utterances'][i-1:i+1])+1<=257 for d in docs for i in range(1,len(d['utterances']))),'adjacent_pairs':sum(len(d['utterances'])-1 for d in docs),'ack_proxy_utterances':sum(u['quality_flags']['acknowledgement_proxy']for d in docs for u in d['utterances']),'substantive_proxy_utterances':sum(u['quality_flags']['substantive_proxy']for d in docs for u in d['utterances']),'pii_review_utterances':sum(bool(u['quality_flags']['pii_review'])for d in docs for u in d['utterances']),'genre_metadata':dict(collections.Counter(d['metadata']['dialogue_type']for d in docs)),'exact_duplicate_conversations':exact,'verified_near_conversations':near,'near_comparisons':comparisons,'near_method':'16 minimum SHA256 character5grams retrieval >=2 shared; lengthratio >=.8; actual Jaccard >=.85; not semantic-exhaustive','derived_sha256':sha(out.read_bytes()),'tokenizer_sha256':sha((V2/'data/tokenizer.json').read_bytes()),'all_texts_byte_roundtrip':True,'training_admitted_dialogues':0,'actual_optimizer_updates':0,'sealed_test_created_or_read':False,'limitations':['heuristic Japanese/PII/ack flags are not semantic or human-authorship proof','chronological next turn is not verified reply parent','all source speech retained; no false EOS or speaker conflation','source-local pseudonyms do not establish cross-source identity independence']}
 (HERE/'derived/metrics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(json.dumps(stats,ensure_ascii=False)[:7000])
if __name__=='__main__':main()
