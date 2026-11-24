"""Frozen B64 paired next-token conditions and8 optional8-token TF continuations."""
import argparse,pathlib,json,gzip,sys,datetime,os,platform,time
from metrics import sha,input_hash,summarize,js,aggregate,teacher_input,archive_logits
D=pathlib.Path(__file__).resolve().parent;B=D.parent;V=B.parent;ROOT=B.parents[3]
def write(name,d):(D/name).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 a=argparse.ArgumentParser();a.add_argument('--checkpoint',required=True);args=a.parse_args()
 assert not(D/'RESULTS.json').exists(),'Do not re-execute a completed study'
 freeze=json.loads((D/'FREEZE.json').read_text())
 for rel,want in freeze['sha256'].items():assert sha(ROOT/rel)==want,rel
 pairs=json.loads((D/'INPUT_PAIRS.json').read_text());proto=json.loads((D/'PROTOCOL.json').read_text());selection=json.loads((D/'SELECTION.json').read_text());labels=json.loads((D/'AUXILIARY_TOKEN_REVIEW.json').read_text())['specific_content_positions']
 assert len(pairs)==32 and sum(r['group']=='mata'for r in pairs)==16
 import torch,numpy as np
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 sys.path.insert(0,str(V));import core
 expected=proto['checkpoint_sha256'];assert sha(args.checkpoint)==expected
 manifest=json.loads((B/'artifacts/B-579/checkpoint.json').read_text());obj=torch.load(args.checkpoint,map_location='cpu',weights_only=False);assert core.digest(obj)==manifest['full_state_digest']and obj['active_cursor']==579
 with torch.random.fork_rng(devices=[]):model=core.decoder(obj['trajectory']['config'])
 model.load_state_dict(obj['trajectory']['model'],strict=True);model.eval();del obj
 model_hash=core.digest(model.state_dict());pieces=[bytes.fromhex(s)for s in json.loads((V/'data/tokenizer.json').read_text())['bytes']]
 cachepath=B/'newline-followup/top-candidates/LOGITS.json.gz';cachemeta=json.loads((cachepath.parent/'RESULTS.json').read_text());assert cachemeta['checkpoint_sha256']==expected and sha(cachepath)==cachemeta['all_logits_archive_sha256']
 old=json.load(gzip.open(cachepath,'rt'));cache={input_hash(r['input_tokens']):r['logits_FP32']for r in old}
 started=time.monotonic();calls=0;reused=0;records=[];rawmain=[];main_values={}
 journal=D/'FORWARD_LEDGER.jsonl';assert not journal.exists()
 def forward(ids,phase,index,kind):
  nonlocal calls
  with journal.open('a')as f:f.write(json.dumps(dict(event='intent',phase=phase,index=index,kind=kind))+'\n');f.flush();os.fsync(f.fileno())
  t=torch.tensor([ids],dtype=torch.long);z=model(t)[0];calls+=1
  assert torch.isfinite(z).all()
  with journal.open('a')as f:f.write(json.dumps(dict(event='completed',phase=phase,index=index,kind=kind))+'\n');f.flush();os.fsync(f.fileno())
  return z
 with torch.inference_mode():
  for r in pairs:
   stats={};probs={}
   for code,name in [('C','correct'),('U','unrelated')]:
    ids=r[name]['history_tokens'];assert len(ids)==len(r['positions'])and r['positions']==list(range(len(ids)))and ids[-2:]==[16,16]and all(t>=6 for t in ids)
    assert b''.join(pieces[t]for t in ids).decode('utf8')==r[name]['history_text']
    key=input_hash(ids)
    if key in cache:values=cache[key];reused+=1
    else:values=forward(ids,'primary',r['index'],code)[-1].tolist()
    s,p=summarize(values,r['gold']);stats[code]=s;probs[code]=p;rawmain.append(values);main_values[(r['index'],code)]=values
   row=dict(index=r['index'],group=r['group'],gold=r['gold'],gold_piece=r['gold_piece'],input_length=len(r['positions']),position_ids=r['positions'],
    correct_document=r['correct']['document_family'],unrelated_document=r['unrelated']['document_family'],year=r['correct']['year'],
    input_SHA256={k:input_hash(r[n]['history_tokens'])for k,n in [('C','correct'),('U','unrelated')]},C=stats['C'],U=stats['U'],
    delta=stats['C']['gold']['logP']-stats['U']['gold']['logP'],JS_nats=js(probs['C'],probs['U']),
    lexical_features={code:dict(history_mata_count=r[name]['history_tokens'].count(3749),history_LF_count=r[name]['history_tokens'].count(16),sentence_periods=r[name]['history_text'].count('。'))for code,name in [('C','correct'),('U','unrelated')]},
    unrelated_original_gold=r['unrelated']['gold'],same_original_next_token=r['same_original_next_token'])
   records.append(row)
   write('PRIMARY_PROGRESS.json',dict(conditions_completed=2*len(records),actual_forward_calls=calls,cached_vectors_reused=reused,optimizer_calls=0))
  main_archive=archive_logits(D/'PRIMARY_LOGITS.f32.gz',rawmain)
  primary=dict(freeze_sha256=sha(D/'FREEZE.json'),checkpoint_sha256=expected,cases=records,groups=aggregate(records),raw_logits=main_archive,raw_order='Each pair in index order, C then U.',primary_forward_calls=calls,cached_vectors_reused=reused,optimizer_calls=0,primary_completed_before_auxiliary=True)
  write('RESULTS.json',primary)
  primary_calls=calls;rawaux=[];aux=[];max_replay_error=0.;argmax_differences=0
  for index in selection['supplemental_representatives']:
   r=pairs[index];conditions={}
   for code,name in [('C','correct'),('U','unrelated')]:
    ids,positions=teacher_input(r[name]['history_tokens'],r['teacher_tail']);z=forward(ids,'auxiliary',index,code)
    selected=z[positions].tolist();err=max(abs(a-b)for a,b in zip(selected[0],main_values[(index,code)]));max_replay_error=max(max_replay_error,err)
    argmax_differences+=max(range(3997),key=lambda t:selected[0][t])!=max(range(3997),key=lambda t:main_values[(index,code)][t])
    assert err<=2e-4,'Auxiliary prefix-logit drift; preserve primary and stop auxiliary'
    steps=[]
    for j,(values,gold)in enumerate(zip(selected,r['teacher_tail'])):
     s,_=summarize(values,gold);s.update(position=j+1,gold_piece=pieces[gold].decode('utf8'),NLL=-s['gold']['logP'],specific_content_piece=j in labels.get(str(index),[]));steps.append(s);rawaux.append(values)
    conditions[code]=steps
   aux.append(dict(index=index,group=r['group'],tail_tokens=r['teacher_tail'],conditions=conditions,delta_by_position=[u['NLL']-c['NLL']for c,u in zip(conditions['C'],conditions['U'])]))
  aux_archive=archive_logits(D/'AUXILIARY_LOGITS.f32.gz',rawaux)
  write('AUXILIARY_RESULTS.json',dict(cases=aux,raw_logits=aux_archive,raw_order='Representative order, C then U, each8 target positions.',additional_forward_calls=calls-primary_calls,primary_first_logit_max_error=max_replay_error,first_argmax_differences=argmax_differences,not_free_generation=True,content_labels_are_manual_BPE_piece_annotations=True))
 assert core.digest(model.state_dict())==model_hash and sha(args.checkpoint)==expected
 for rel,want in freeze['sha256'].items():assert sha(ROOT/rel)==want,rel
 events=[json.loads(s)for s in journal.read_text().splitlines()];assert len([e for e in events if e['event']=='intent'])==len([e for e in events if e['event']=='completed'])==calls
 write('EXECUTION.json',dict(actual_model_forward_calls=calls,primary_forward_calls=primary_calls,auxiliary_forward_calls=calls-primary_calls,cached_primary_vectors_reused=reused,actual_optimizer_calls=0,failed_forward_calls=0,free_generations=0,checkpoint_and_model_tensors_unchanged=True,frozen_inputs_unchanged=True,
  checkpoint_sha256=expected,python=platform.python_version(),torch=torch.__version__,numpy=np.__version__,CPU_threads=torch.get_num_threads(),GPU_used=False,seconds=time.monotonic()-started,metadata_fetch_abort_and_prefreeze_selection_changes='history/; all before model loading',primary_result_sha256=sha(D/'RESULTS.json'),auxiliary_result_sha256=sha(D/'AUXILIARY_RESULTS.json')))
 print(json.dumps(dict(forward_calls=calls,reused=reused,optimizer_calls=0,groups={k:v['delta']for k,v in primary['groups'].items()}),ensure_ascii=False))
if __name__=='__main__':main()
