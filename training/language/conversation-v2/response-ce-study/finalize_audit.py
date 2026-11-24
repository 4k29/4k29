"""Publish only metadata and individually non-held candidate spans. No training authorization."""
import json,pathlib,gzip,hashlib,collections,statistics,re,unicodedata
from masks import make_pair
__import__('os').umask(0o077)
P=pathlib.Path(__file__).resolve().parent
load=lambda n:json.loads((P/n).read_text())
def write(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return ''.join(unicodedata.normalize('NFKC',s).split())
x=load('LOCAL_REVIEW_CARDS.json');x['train']+=load('LOCAL_SUPPLEMENT_CARDS.json');review=load('REVIEW.json');review['cases']+=load('SUPPLEMENT_REVIEW.json')['cases'];by={(r['partition'],r['id']):r for r in review['cases']};selection=load('SELECTION.json');pack={};summ={};san=[]
for part in ['train','dev']:
 rows=[];counter=collections.Counter();body=[];chars=[];speakers=set();families=set();texts=[];types=collections.Counter();source_positions=set()
 for r in x[part]:
  d=by[part,r['id']]
  public={k:v for k,v in r.items()if k not in ['history_text','response_text','prefix_ids','response_ids','serialized_ids']}
  public['input_SHA256']=hashlib.sha256(json.dumps(r['serialized_ids'],separators=(',',':')).encode()).hexdigest();public['decision']=d['decision'];san.append(public)
  if d['decision']!='conditional_candidate':continue
  start=r['response_source_span'][0];z=make_pair(r['serialized_ids'],start)
  teacher=z['teacher_ids'];mask=z['response_ce_mask'];body.append(len(r['response_ids'])-1);chars.append(len(r['response_text']));speakers.update(r['speakers']);families.add(r['family']);texts.append(r['response_text']);types[d['semantic_type']]+=1
  for i,t in enumerate(teacher):
   key=(r['document'],i+1);assert key not in source_positions;source_positions.add(key)
   counter['input_nonpadding']+=1;counter['A_loss_teachers']+=1;counter['B_loss_teachers']+=int(mask[i]);counter['A_EOS']+=t==2;counter['A_role']+=t in [3,4];counter['B_EOS']+=mask[i] and t==2;counter['B_role']+=mask[i] and t in [3,4]
   counter['history_body_teachers']+=not mask[i] and t>5;counter['response_body_teachers']+=mask[i] and t>5;counter['LF_A']+=t==16;counter['LF_B']+=mask[i] and t==16
  assert z['input_ids']==r['serialized_ids'][:-1];assert teacher==r['serialized_ids'][1:];assert sum(mask)==len(r['response_ids'])
  rows.append(dict(id=r['id'],document=r['document'],family=r['family'],speakers=r['speakers'],partition=part,source='RealPersona',source_sha256=r['source_sha256'],source_text_sha256=r['source_text_sha256'],source_url=r['source_url'],license=r['license'],attribution=r['attribution'],original_ordinal=r['target_ordinal'],role=r['role_token'],tokens=r['serialized_ids'],response_body_start=start,source_span=[0,len(r['serialized_ids'])],all_ce_mask=z['all_ce_mask'],response_ce_mask=mask,semantic_type=d['semantic_type'],approved_for_optimizer_updates=False))
 pack[part]=rows;summ[part]=dict(conditional_responses=len(rows),families=len(families),source_local_speakers=len(speakers),teacher_counts=dict(counter),response_tokens=sum(body),response_BPE_length=dict(min=min(body),median=statistics.median(body),max=max(body)),response_character_length=dict(min=min(chars),median=statistics.median(chars),max=max(chars)),response_types=dict(types),exact_unique_response_strings=len(set(norm(t)for t in texts)),punctuation_two_plus_proxy=sum(len(re.findall('[。！？!?]',t))>=2 for t in texts),normalization='one global active-token mean per batch',body_token_counts_are_existing_original_positions_not_new_corpus=True)
# Metadata only for held records: reversible token streams are not published for them.
write('SELECTION_METADATA.json',dict(full_private_selection_SHA256=sha(P/'SELECTION.json'),supplement_selection_SHA256=sha(P/'SUPPLEMENT_SELECTION.json'),protocol_sha256=selection['protocol_sha256'],input_SHA=selection['input_SHA'],pools=selection['pools'],global_counts=selection['counts'],selected=san,held_original_text_or_tokens_published=False,model_predictions_used_for_selection=False))
write('CANDIDATE_SPANS.json',dict(training_authorized=False,formal_TRAIN_admission=False,parts=pack))
order=sorted(range(len(pack['train'])),key=lambda i:hashlib.sha256(('response-ce-schedule-v1|'+pack['train'][i]['id']).encode()).hexdigest());batches=[order[i:i+4]for i in range(0,len(order),4)]
write('PREPARATION_SCHEDULE.json',dict(executable=False,reason='Data sufficiency not demonstrated; storage gate also fails locally',same_batches_for_A_B=True,batches=batches,planned_updates_if_later_approved=len(batches),actual_updates=0,one_pass=True))
write('DATA_SUMMARY.json',dict(parts=summ,selected_TRAIN_reviewed=256,selected_DEV_reviewed=24,supplementary_TRAIN_reviewed=64,review_decisions={k:dict(collections.Counter(r['decision']for r in review['cases']if r['partition']==k))for k in ['train','dev']},training_go=False,optimizer_calls=0,model_forwards=0,train_dev_speaker_overlap=len({s for r in pack['train']for s in r['speakers']}&{s for r in pack['dev']for s in r['speakers']}),train_dev_family_overlap=len({r['family']for r in pack['train']}&{r['family']for r in pack['dev']}),new_original_data_acquired=0,independent_human_evaluation=False,sealed_TEST_used=False))
print(json.dumps(summ,ensure_ascii=False))
