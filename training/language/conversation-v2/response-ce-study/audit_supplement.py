"""Fixed later-turn source audit, no model or acquisition."""
import json,pathlib,os,importlib.util,re,collections,hashlib
__import__('os').umask(0o077)
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get('CE_V2_ROOT','/workspace/4k29/training/language/conversation-v2'))
load=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 protocol=load(P/'SUPPLEMENT_PROTOCOL.json');spec=importlib.util.spec_from_file_location('own',V/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);tok=load(V/'data/tokenizer.json');enc=m.Encoder(tok);pieces=[bytes.fromhex(t)for t in tok['bytes']]
 first=load(P/'LOCAL_REVIEW_CARDS.json');excluded={r['document']for rr in first.values()for r in rr};excluded.update(r['id'].rsplit(':',1)[0]for r in load(V/'reply-focus/REPLY_SAMPLE_REVIEW.json')['cases']);excluded.update(load(V/'allocation-study/PLAN.json')['ids']);sensitive=re.compile(load(V/'sns-data/pipeline/publication-policy.json')['sensitive_topic_regex']);pool=[];counter=collections.Counter()
 for line in (V/'data/train.docs.jsonl').open():
  d=json.loads(line);us=d['utterances'];text='\n'.join(u['text']for u in us)
  if d['id'] in excluded or sensitive.search(text)or re.search(r'https?://|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',text):continue
  full=[1]
  for j,u in enumerate(us):
   ids=enc(u['text']);assert b''.join(pieces[t]for t in ids)==u['text'].encode();role_start=len(full);body=role_start+1;full.extend([u['localRoleToken']]+ids+[2])
   if j<8:continue
   if len(full)>257:counter['later_position_over_full_context']+=1;continue
   if not 1<=len(ids)<=96:continue
   a=us[j-1]['text'];b=u['text'];tags=[];question=bool(re.search('[?？]|教えて|知りたい|どうすれば|どうしたら',a))
   if question and re.search('なぜ(?!か)|どうして(?!も|ます)|理由',a):tags.append('reason')
   if question and re.search('どちら(?!に|へ|です|を経験)|どっち|比較|比べ',a):tags.append('comparison')
   if question and re.search('おすすめ|オススメ|どうすれば|どうしたら|困っ|悩',a):tags.append('advice')
   if question and re.search('なら|場合|だったら|とき',a):tags.append('condition')
   if question and re.search('教えて|どうやって|方法|どのよう',a):tags.append('explanation')
   if question and len(re.findall('[。！？!?]',b))>=2:tags.append('multi_sentence_question_response')
   if not tags:continue
   pool.append(dict(id=d['id']+':'+str(j),document=d['id'],family=d['normalizedDocumentFamily'],speakers=d['speakers'],partition='train',target_ordinal=j,prefix_ids=full[:body],response_ids=full[body:],serialized_ids=full[:],response_source_span=[body,len(full)],retrieval_tags=tags,source_sha256=d['sourceSha256'],source_text_sha256=d['sourceTextSha256'],source_url=d['sourceUrl'],license=d['license'],attribution=d['attribution'],role_token=u['localRoleToken'],true_EOS=True,history_text=[z['text']for z in us[:j]],response_text=b))
 used=set();selected=[];counts={}
 for tag,quota in protocol['quotas'].items():
  count=0
  for r in sorted((x for x in pool if tag in x['retrieval_tags']),key=lambda r:hashlib.sha256((protocol['seed']+'|'+tag+'|'+r['id']).encode()).hexdigest()):
   if r['family']in used:continue
   selected.append(dict(r,selection_stratum=tag));used.add(r['family']);count+=1
   if count==quota:break
  counts[tag]=count
 (P/'LOCAL_SUPPLEMENT_CARDS.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
 receipt=dict(protocol_SHA256=sha(P/'SUPPLEMENT_PROTOCOL.json'),raw_selection_SHA256=sha(P/'LOCAL_SUPPLEMENT_CARDS.json'),source_SHA256=sha(V/'data/train.docs.jsonl'),pool=len(pool),pool_tags=dict(collections.Counter(t for r in pool for t in r['retrieval_tags'])),selection_counts=counts,exclusions=dict(counter),selected=[dict(id=r['id'],document=r['document'],family=r['family'],ordinal=r['target_ordinal'],stratum=r['selection_stratum'],input_SHA256=hashlib.sha256(json.dumps(r['serialized_ids'],separators=(',',':')).encode()).hexdigest())for r in selected],model_predictions_seen=False,optimizer_calls=0)
 (P/'SUPPLEMENT_SELECTION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='selected'}))
if __name__=='__main__':main()
