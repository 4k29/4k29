"""Original Japanese, human-annotated full ancestry paths; no translated/model samples."""
import collections,gzip,hashlib,json,pathlib
from build import HERE,V2,Union,anon,sha,flags,encode_loader

def main():
 raw=HERE/'raw/oasst2-ja-original.jsonl.gz';receipt=json.loads((HERE/'raw/oasst-acquisition.json').read_text());assert sha(raw.read_bytes())==receipt['japanese_subset_sha256']
 rows=[json.loads(l)for l in gzip.open(raw,'rt')];eligible={r['source_record']['message_id']:r['source_record']for r in rows if not r['eligibility_flags']};invalid=collections.Counter();paths=[]
 for key,d in sorted(eligible.items()):
  if d['role']!='assistant':continue
  path=[];seen=set();cur=d
  while cur is not None:
   k=cur['message_id']
   if k in seen:invalid['cycle']+=1;break
   seen.add(k);path.append(cur);parent=cur['parent_id']
   if parent is None:
    path.reverse()
    if path[0]['role']!='prompter' or any(x['role']==y['role']for x,y in zip(path,path[1:])):invalid['invalid-role-path']+=1;break
    paths.append(path);break
   if parent not in eligible:invalid['missing-ineligible-or-nonJapanese-ancestor']+=1;break
   cur=eligible[parent]
 # One maximal assistant-ending branch per leaf. A short prefix is not a new conversation.
 leafpaths=[p for p in paths if not any(len(p)<len(q) and [x['message_id']for x in p]==[x['message_id']for x in q[:len(p)]]for q in paths)]
 enc,tok=encode_loader();vocab=[bytes.fromhex(x)for x in tok['bytes']];docs=[]
 for path in leafpaths:
  ident='oasst2:'+path[-1]['message_id'];tree='oasst2:'+path[0]['message_tree_id'];turns=[]
  for d in path:
   text=d['text'];tokens=enc(text);assert b''.join(vocab[i]for i in tokens)==text.encode()
   f=flags(text);f['source_labels_review']={k:v.get('value')for k,v in (d.get('labels')or{}).items()if k in ['spam','pii','not_appropriate','fails_task','quality']};f['synthetic_explicit_false']=d['synthetic']is False
   turns.append({'id':'oasst2:'+d['message_id'],'speaker_id':anon('oasst2',d['user_id'])if d.get('user_id')else None,'source_role':d['role'],'text':text,'parent_id':'oasst2:'+d['parent_id']if d['parent_id']else None,'previous_in_order_id':'oasst2:'+d['parent_id']if d['parent_id']else None,'published_at':d['created_date'],'reply_relation':'explicit-source-parent','body_tokens':len(tokens),'quality_flags':f,'text_sha256':sha(text.encode())})
  docs.append({'source':'oasst2','id':ident,'conversation_id':tree,'conversation_family':tree,'speakers':sorted({u['speaker_id']for u in turns if u['speaker_id']}),'published_at':turns[0]['published_at'],'source_url':receipt['source_url'],'source_sha256':receipt['source_compressed_sha256'],'license':'Apache-2.0','rights_status':'rights-cleared-quality-pending','admission':'hold-quality-privacy-family','metadata':{'human_authorship':'publisher-crowdsourced-and-synthetic-false-not-detector-proof','role_serialization':'semantic-prompter-assistant-not-two-human-personas','true_reply_parent_available':True,'original_japanese':True,'independent_source_messages':len(turns)},'utterances':turns})
 union=Union([d['id']for d in docs]);sp={};families={};texts={};exactlinks=0
 for d in docs:
  for value,lookup in [(x,sp)for x in d['speakers']]+[(d['conversation_family'],families)]+[(u['text_sha256'],texts)for u in d['utterances']if len(u['text'])>=20]:
   if value in lookup:union.join(d['id'],lookup[value]);exactlinks+=lookup is texts
   else:lookup[value]=d['id']
 for d in docs:
  c=union.get(d['id']);bucket=int(sha(('sns-speaker-component-v1|'+c).encode()),16)%100;d['component']=c;d['split']='DEV'if bucket<15 else'reserve-not-test'if bucket<20 else'TRAIN'
 out=HERE/'derived/oasst-conversations.jsonl.gz'
 with out.open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for d in docs:z.write((json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 unique={u['id']:u for d in docs for u in d['utterances']};components=collections.Counter(d['component']for d in docs)
 metrics={'source':'oasst2','original_japanese_rows':receipt['original_japanese_rows'],'public_original_japanese_rows':len(rows),'rows_eligibility_flags':sum(bool(r['eligibility_flags'])for r in rows),'eligible_original_rows':len(eligible),'complete_assistant_ending_paths_before_prefix_dedup':len(paths),'maximal_branches':len(docs),'conversation_trees':len(families),'unique_messages_used':len(unique),'serialized_messages_including_shared_ancestors':sum(len(d['utterances'])for d in docs),'unique_body_tokens':sum(u['body_tokens']for u in unique.values()),'serialized_body_tokens':sum(u['body_tokens']for d in docs for u in d['utterances']),'source_local_known_authors':len(sp),'missing_author_messages':sum(u['speaker_id']is None for u in unique.values()),'invalid_paths':dict(invalid),'speaker_family_exact_connected_components':len(components),'component_branch_counts':dict(components),'split_documents':dict(collections.Counter(d['split']for d in docs)),'explicit_parent_nonroot':sum(u['parent_id']is not None for u in unique.values()),'paths_2turn':sum(len(d['utterances'])==2 for d in docs),'paths_3plus':sum(len(d['utterances'])>=3 for d in docs),'whole_context256_fit':sum(1+sum(u['body_tokens']+2 for u in d['utterances'])<=257 for d in docs),'ack_proxy_unique_messages':sum(u['quality_flags']['acknowledgement_proxy']for u in unique.values()),'substantive_proxy_unique_messages':sum(u['quality_flags']['substantive_proxy']for u in unique.values()),'pii_review_unique_messages':sum(bool(u['quality_flags']['pii_review'])or(u['quality_flags']['source_labels_review'].get('pii')or 0)>0 for u in unique.values()),'rights_cleared_quality_pending':True,'training_admitted_dialogues':0,'actual_optimizer_updates':0,'sealed_test_created_or_read':False,'derived_sha256':sha(out.read_bytes()),'tokenizer_sha256':sha((V2/'data/tokenizer.json').read_bytes()),'all_texts_byte_roundtrip':True,'limitations':['source human and synthetic metadata are not a perfect authorship detector','source ready export is not an untouched sealed TEST','shared ancestors are not independent new messages','all original source worker identities only hashed within source','exact-text and speaker splits do not prove semantic-family independence']}
 (HERE/'derived/oasst-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n');print(json.dumps(metrics,ensure_ascii=False))
if __name__=='__main__':main()
