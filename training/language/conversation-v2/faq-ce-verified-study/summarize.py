"""Collect immutable numerical receipts across three explicitly separate experiments."""
import pathlib,json,collections,statistics,hashlib,math
P=pathlib.Path(__file__).resolve().parent;V=P.parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();series=[('faq-ce-study',99,50),('faq-ce-clean-study',97,49),('faq-ce-verified-study',93,47)];out=[];index=[]
for folder,n,mid in series:
 p=V/folder;d=read(p/'DATA.json');r=read(p/'RESULT.json');u=[json.loads(x)for x in(p/'UPDATES.jsonl').read_text().splitlines()];returned=[x for x in u if x['event']=='returned'];entry=dict(folder=folder,primary=folder==P.name,PLAN_sha256=sha(p/'PLAN.json'),DATA_sha256=sha(p/'DATA.json'),train_cases=len(d['parts']['train']),reply_body=sum(z['body_tokens']for z in d['parts']['train']),initial=read(p/'SOURCE_STATE.json'),execution=r,resource=read(p/'RESOURCE.json'),calls_by_phase=dict(collections.Counter(z['phase']for z in returned)),arms={},evaluation={})
 for arm in 'AB':
  t=[z['trace']for z in returned if z['phase']=='study-retained'and z['arm']==arm];g=[z['gradient_norm']for z in t];entry['arms'][arm]=dict(updates=len(t),input_nonPAD=sum(z['input_tokens']for z in t),active_teachers=sum(z['active_teachers']for z in t),body_teachers=sum(z['response_body_teachers']for z in t),response_EOS=sum(z['response_EOS_teachers']for z in t),loss_first=t[0]['loss'],loss_last=t[-1]['loss'],train_loss_weighted=sum(z['loss']*z['active_teachers']for z in t)/sum(z['active_teachers']for z in t),gradient_norm=dict(min=min(g),mean=statistics.mean(g),median=statistics.median(g),max=max(g)),clipped=sum(z['clipped']for z in t),LR=sorted({z['lr']for z in t}))
  delta=p/'UPDATE_DELTAS.jsonl'
  if delta.exists():
   ds=[json.loads(s)for s in delta.read_text().splitlines()];ds=[s for s in ds if s['phase']=='study-retained'and s['arm']==arm];entry['arms'][arm]['per_update_weight_L2']=dict(count=len(ds),first=ds[0]['delta_L2'],last=ds[-1]['delta_L2'],mean=statistics.mean(s['delta_L2']for s in ds))
  for k in [mid,n]:
   m=read(p/f'artifacts/{arm}-FAQ{k}/checkpoint.json');c=read(p/f'COLD-{arm}-{k}.json');index.append({**m,'folder':folder,'step':k,'manifest':f'{folder}/artifacts/{arm}-FAQ{k}/checkpoint.json','cold':c})
 sources={row['id']:row['source']for rows in d['parts'].values()for row in rows}
 for name in ['initial',f'A-study{mid}',f'A-study{n}',f'B-study{mid}',f'B-study{n}']:
  path=p/f'evaluation/{name}.json'
  if not path.exists():continue
  e=read(path);nll=e['NLL'];z={}
  for part in ['pilot_train','dev']:
   rows=[x for x in nll if x['partition']==part];z[part]=dict(cases=len(rows),body=sum(x['body_sum']for x in rows)/sum(x['body_tokens']for x in rows),with_response_EOS=sum(x['with_EOS_sum']for x in rows)/sum(x['with_EOS_tokens']for x in rows))
   if part=='dev':
    z['source_dev']={s:dict(cases=len(a),body=sum(x['body_sum']for x in a)/sum(x['body_tokens']for x in a),with_response_EOS=sum(x['with_EOS_sum']for x in a)/sum(x['with_EOS_tokens']for x in a))for s in sorted(set(sources[x['id']]for x in rows))if(a:=[x for x in rows if sources[x['id']]==s])}
    strict=set(read(P/'ANSWER_BOUNDARY_STRICT_AUDIT.json')['pass_ids']);a=[x for x in rows if x['id']in strict];z['strict_format_dev17']=dict(cases=len(a),body=sum(x['body_sum']for x in a)/sum(x['body_tokens']for x in a))
  z['panels']={panel:dict(cases=len(rows),EOS=sum(x['eos']for x in rows),repeat4gram_proxy=sum(bool(x['repeated4gram'])for x in rows),blank_only=sum(not(x['text']or'').strip()for x in rows),strict_UTF8=sum(x['strictUtf8']for x in rows))for panel in sorted({x['panel']for x in e['cases']})if(rows:=[x for x in e['cases']if x['panel']==panel])};z['source_sha256']=sha(path);entry['evaluation'][name]=z
 out.append(entry)
summary=dict(series=out,actual_optimizer_calls=sum(x['execution']['actual_optimizer_returns']for x in out),retained=sum(x['execution']['retained']for x in out),discarded_original=sum(x['execution']['discarded_original']for x in out),replay=sum(x['execution']['resume_replay']for x in out),model_forwards=sum(x['execution']['model_forward_returns']for x in out),model_seconds=sum(x['execution']['seconds']for x in out),initial_failed_import_optimizer_calls=0,initial_failed_import_model_forwards=0,analysis_optimizer_calls=0,analysis_model_forwards=0)
(P/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');(P/'CHECKPOINT_INDEX.json').write_text(json.dumps(dict(initial='mixed-retention-study/artifacts/MIX-579/checkpoint.json',initial_SHA=out[-1]['initial']['checkpoint_sha256'],states=index,all_12_remote_only_cold=True,total_fullstate_bytes=sum(x['bytes']for x in index)),ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in summary.items()if k!='series'})
for row in out:
 print(row['folder'],[(k,round(v['dev']['body'],6))for k,v in row['evaluation'].items()])
