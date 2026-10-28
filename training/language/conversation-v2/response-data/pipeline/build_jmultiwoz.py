"""Official TRAIN-only human Wizard dialogue adapter; hidden DB is not input text."""
import collections,gzip,hashlib,importlib.util,json,pathlib,re
from build_candidates import HERE,V2,encoder,sha,write_gz
RAW=pathlib.Path('/dev/shm/response-jmultiwoz/train.jsonl.gz')
REV='a78dd334b907e12318b76bb23d0a9ed1498b8d15'

def anon(value):return sha(('response-jmultiwoz|'+value).encode())[:24]
def canonical(text):return re.sub(r'\s+','',text)
def normalize(row,enc,tok):
 d=row['data'];assert row['official_split']=='train';ident='jmultiwoz:'+row['source_id'];authors={'USER':anon(d['user_name']),'SYSTEM':anon(d['system_name'])};utterances=[];stream=[1];vocab=[bytes.fromhex(x)for x in tok['bytes']];reasons=[];fixtures=[]
 for t in d['turns']:
  assert t['speaker']in authors
  state=t.get('dialogue_state',{});entity=state.get('db_result',{}).get('active_entity')or{}
  fixtures.append(entity)
 contacts={re.sub(r'\D','',str(e['phone']))for e in fixtures if e.get('phone')}
 for i,t in enumerate(d['turns']):
  assert t['turn_id']==i and t['speaker']==('USER'if i%2==0 else'SYSTEM')
  text=t['utterance'];ids=list(enc(text));assert b''.join(vocab[x]for x in ids)==text.encode();stream +=[3 if t['speaker']=='USER'else 4]+ids+[2]
  entity=fixtures[i];detected=[]
  for number in re.findall(r'(?<!\d)0\d{1,3}[-ー ]?\d{2,4}[-ー ]?\d{3,4}(?!\d)',text):
   if re.sub(r'\D','',number)not in contacts:detected.append('unresolved-contact-number')
  if re.search(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}',text):detected.append('email-review')
  if detected:reasons.extend(detected)
  utterances.append({'id':ident+':'+str(i),'parent_id':ident+':'+str(i-1)if i else None,'speaker_id':authors[t['speaker']],'source_role':'prompter'if t['speaker']=='USER'else'assistant','text':text,'body_tokens':len(ids),'text_sha256':sha(text.encode()),'privacy_flags':detected,'source_operator_had_hidden_db':bool(entity),'hidden_db_fields':sorted(entity),'hidden_db_sha256':sha(json.dumps(entity,ensure_ascii=False,sort_keys=True).encode()),'hidden_db_not_in_model_input':True})
 return {'source':'jmultiwoz','id':ident,'family':ident,'official_partition':'train','partition':'TRAIN-candidate','authors':sorted(authors.values()),'role_semantics':'human-customer-human-Wizard; not AI-generated SYSTEM','source_id':row['source_id'],'source_object_sha256':row['source_object_sha256'],'source_license':'CC-BY-SA-4.0','source_url':'https://github.com/nu-dialogue/jmultiwoz/blob/'+REV+'/dataset/JMultiWOZ_1.0.zip','source_revision':REV,'source_attribution':'Atsumoto Ohashi, Ryu Hirai, Shinya Iizuka, Ryuichiro Higashinaka, JMultiWOZ, nu-dialogue/jmultiwoz','admitted_for_training':False,'source_goal_domains':sorted(d['goal']),'utterances':utterances,'serialized_ids':stream,'token_audit':{'full_serialized_tokens':len(stream),'whole_context256_fit':len(stream)<=257,'byte_roundtrip':True,'false_eos_inserted':False},'privacy_hold_reasons':sorted(set(reasons))}

def main():
 enc,tok=encoder();raw=[json.loads(l)for l in gzip.open(RAW,'rt')];assert len(raw)==3646
 docs=[normalize(r,enc,tok)for r in raw];held=[d for d in docs if d['privacy_hold_reasons']];kept=[d for d in docs if not d['privacy_hold_reasons']]
 out=HERE/'derived/jmultiwoz-train-candidates.jsonl.gz';write_gz(out,kept)
 metrics={'source':'JMultiWOZ-new-official-TRAIN','acquired_train_dialogues':len(raw),'acquired_train_source_sha256':sha(RAW.read_bytes()),'public_candidate_dialogues':len(kept),'public_candidate_utterances':sum(len(d['utterances'])for d in kept),'source_local_authors':len({a for d in kept for a in d['authors']}),'unique_body_tokens':sum(u['body_tokens']for d in kept for u in d['utterances']),'system_response_count':sum(u['source_role']=='assistant'for d in kept for u in d['utterances']),'operator_turns_with_hidden_db_entity':sum(u['source_role']=='assistant'and u['source_operator_had_hidden_db']for d in kept for u in d['utterances']),'whole_context256_fit':sum(d['token_audit']['whole_context256_fit']for d in kept),'privacy_held_dialogues':len(held),'training_admitted':0,'actual_optimizer_updates':0,'source_test_read':False,'candidate_archive_sha256':sha(out.read_bytes()),'tokenizer_sha256':sha((V2/'data/tokenizer.json').read_bytes()),'limitations':['automatic contact check is not full privacy or third-party-rights certification','source SYSTEM is a human Wizard with DB access; hidden DB is deliberately not supplied as model text','official TRAIN partition is not a new speaker-independent split','quality sample does not admit all corpus responses','no synthetic model answers or body repairs']}
 (HERE/'derived/jmultiwoz-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
 (HERE/'audit/jmultiwoz-privacy-holds.json').write_text(json.dumps({'source':'jmultiwoz','held':[{'id':d['id'],'source_object_sha256':d['source_object_sha256'],'reasons':d['privacy_hold_reasons']}for d in held],'note':'Withheld raw bodies remain temporary, not durable public artifacts; no edits to retained original text.'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(metrics,ensure_ascii=False))
if __name__=='__main__':main()
