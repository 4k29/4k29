"""Read existing human corpus only; no model import, update or semantic auto-approval."""
import pathlib,json,gzip,re,collections,hashlib,importlib.util,sys,os
__import__('os').umask(0o077)
P=pathlib.Path(__file__).resolve().parent
V=pathlib.Path(os.environ.get('CE_V2_ROOT','/workspace/4k29/training/language/conversation-v2'))
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rank(s):return hashlib.sha256(('response-ce-audit-20261111-v1|'+s).encode()).hexdigest()
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 spec=importlib.util.spec_from_file_location('own',V/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);tok=load(V/'data/tokenizer.json');enc=m.Encoder(tok);pieces=[bytes.fromhex(t) for t in tok['bytes']]
 policy=load(V/'sns-data/pipeline/publication-policy.json');sensitive=re.compile(policy['sensitive_topic_regex']);old=load(V/'reply-focus/REPLY_SAMPLE_REVIEW.json');oldids={x['id'] for x in old['cases']};olddocs={i.rsplit(':',1)[0] for i in oldids};olddocs.update(load(V/'allocation-study/PLAN.json')['ids'])
 prior_eval=load(V/'data/benchmark-dev.json');olddevdocs={r.get('document') for r in prior_eval.get('cases',[])}
 docs={part:[json.loads(l)for l in (V/'data'/f'{part}.docs.jsonl').open()] for part in ['train','dev']};speaker_sets={k:{s for d in ds for s in d['speakers']}for k,ds in docs.items()};family_sets={k:{d['normalizedDocumentFamily'] for d in ds}for k,ds in docs.items()};assert not speaker_sets['train']&speaker_sets['dev'];assert not family_sets['train']&family_sets['dev']
 counter={};pools={};rows={};allsource=[]
 for part,ds in docs.items():
  c=collections.Counter();c['documents']=len(ds);c['utterances']=sum(len(d['utterances'])for d in ds);c['speakers']=len(speaker_sets[part]);pool=[]
  for d in ds:
   assert d['partition']==part and d['license']=='CC-BY-SA-4.0';us=d['utterances'];full=[1];bounds=[];hold=bool(sensitive.search('\n'.join(u['text']for u in us)) or re.search(r'https?://|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','\n'.join(u['text']for u in us)))
   for u in us:
    ids=enc(u['text']);assert b''.join(pieces[t]for t in ids)==u['text'].encode();start=len(full);full.extend([u['localRoleToken']]+ids+[2]);bounds.append((start,start+1,len(full)))
   for j in range(1,len(us)):
    a,b=us[j-1],us[j];assert a['speakerId']!=b['speakerId'];c['different_speaker_pairs']+=1;atext,btext=a['text'],b['text'];c['question_proxy']+=bool(re.search(r'[?？]|ですか|ますか',atext));c['causal_response_proxy']+=bool(re.search('から|ので|ため',btext));c['multi_sentence_response_proxy']+=len(re.findall('[。！？!?]',btext))>=2
    if not 1<=j<=7:continue
    s,body,e=bounds[j];prefix=full[:body];response=full[body:e]
    if len(full[:e])>257:c['full_history_over_context']+=1;continue
    if len(response)-1>96 or len(response)<2:c['response_length_excluded']+=1;continue
    if hold:c['privacy_topic_hold_eligible_pairs']+=1;continue
    if d['id'] in olddocs or (part=='dev' and d['id'] in olddevdocs):c['prior_review_or_evaluation_doc_excluded']+=1;continue
    tags=[]
    if re.search('なぜ|どうして|理由',atext):tags.append('reason')
    if re.search('どちら|どっち|比べ|比較',atext):tags.append('comparison')
    if re.search('おすすめ|オススメ|どうすれば|どうしたら|教えて|困っ|悩',atext):tags.append('advice')
    if re.search('なら|場合|とき|時',atext):tags.append('condition')
    if re.search('[?？]|ですか|ますか',atext):tags.append('question')
    if j>=3:tags.append('followup')
    if not tags:continue
    ident=d['id']+':'+str(j);r=dict(id=ident,document=d['id'],family=d['normalizedDocumentFamily'],speakers=d['speakers'],partition=part,target_ordinal=j,prefix_ids=prefix,response_ids=response,serialized_ids=full[:e],response_source_span=[body,e],retrieval_tags=tags,source_sha256=d['sourceSha256'],source_text_sha256=d['sourceTextSha256'],source_url=d['sourceUrl'],license=d['license'],attribution=d['attribution'],role_token=us[j]['localRoleToken'],true_EOS=True,history_text=[u['text']for u in us[:j]],response_text=btext)
    pool.append(r)
   allsource.append(dict(document=d['id'],partition=part,family=d['normalizedDocumentFamily'],source_sha256=d['sourceSha256']))
  quotas={'reason':32,'comparison':24,'advice':24,'condition':24,'question':64,'followup':24} if part=='train' else {'reason':4,'comparison':3,'advice':3,'condition':3,'question':8,'followup':3}
  used=set();selected=[];counts={}
  for tag,quota in quotas.items():
   chosen=[]
   for r in sorted((x for x in pool if tag in x['retrieval_tags']),key=lambda r:rank(part+'|'+tag+'|'+r['id'])):
    if r['family'] in used:continue
    chosen.append(dict(r,selection_stratum=tag));used.add(r['family'])
    if len(chosen)==quota:break
   selected.extend(chosen);counts[tag]=len(chosen)
  rows[part]=selected;pools[part]=dict(eligible=len(pool),available_tags=dict(collections.Counter(t for r in pool for t in r['retrieval_tags'])),selected_strata=counts);counter[part]=dict(c)
 write('SELECTION.json',dict(protocol_sha256=sha(P/'PRE_AUDIT_PROTOCOL.json'),input_SHA={str(p.relative_to(V)):sha(p) for p in [V/'data/train.docs.jsonl',V/'data/dev.docs.jsonl',V/'data/tokenizer.json',V/'data/split.json',V/'reply-focus/REPLY_SAMPLE_REVIEW.json',V/'sns-data/pipeline/publication-policy.json']},selected={k:[{x:v for x,v in r.items()if x not in ['history_text','response_text']}for r in rr]for k,rr in rows.items()},counts=counter,pools=pools,train_dev_speaker_overlap=0,train_dev_family_overlap=0,optimizer_calls=0,semantic_approval_automatic=False))
 write('LOCAL_REVIEW_CARDS.json',rows)
 write('ENVIRONMENT.json',dict(root_disk_free_bytes=__import__('shutil').disk_usage('/workspace').free,working_directory=str(P),RAM_backed_not_durable=True,old_Git_alternate_missing=True,training_storage_gate_passed=False,optimizer_calls=0))
 print(json.dumps(dict(counts=counter,pools=pools,selection_SHA=sha(P/'SELECTION.json')),ensure_ascii=False))
if __name__=='__main__':main()
