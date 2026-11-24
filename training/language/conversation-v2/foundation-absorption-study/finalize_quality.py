"""Final pre-update, content-based holds; no refill and no output-based selection."""
import pathlib,json,gzip,hashlib,re,collections
P=pathlib.Path(__file__).resolve().parent;assert not(P/'PLAN.json').exists(),'Do not overwrite frozen study; rebuild in a new directory';sha=lambda b:hashlib.sha256(b).hexdigest();r=[json.loads(x)for x in gzip.decompress((P/'corpus.jsonl.gz').read_bytes()).splitlines()];q=json.loads((P/'QUALITY_SAMPLE.json').read_text());previous=json.loads((P/'QUALITY_REVIEW.json').read_text())if(P/'QUALITY_REVIEW.json').exists()else{};sample=q.get('cases',previous.get('rows',[]));ids={'jaquad:9486b852360cb49e9397cdcf:2':'Historical persecution biography outside intended prose focus','jaquad:51bc6fd3d5e7e781ec91e0b7:9':'Inconsistent/unclear chick-development timeline and malformed phrase','jaquad:b937b59d66927be8cdd611d2:14':'Potentially identifiable private-person disaster anecdote','jaquad:d3b7beed30f2c0927bc8a681:8':'Atmospheric numerical comparisons not independently resolved','jawikibooks:3689:0':'Outdated entry rules, speculative and informal unsupported institutional claims','jawikibooks:21171:26':'Force classification absolute statement missing school-physics scope'};ids.update({x:'Annual whitepaper near-duplicate paragraph, no replacement'for x in ['env:env-h26-hj14020602.gz:22','env:env-h24-hj12020608.gz:20','env:env-r01-hj19020609.gz:1']});families={x['family']:ids[x['id']]for x in r if x['id']in ids and x['source']=='jaquad'};held=previous.get('held',[]);kept=[]
for x in r:
 why=ids.get(x['id'],families.get(x['family']))
 if x['source']=='realpersona'and re.search('ダイエット|診断|妊娠|減量|病気|持病|障害',x['text']):why='Privacy/health or personalized health guidance held'
 if why:held.append(dict(id=x['id'],source=x['source'],family=x['family'],reason=why,body_SHA=sha(x['text'].encode())))
 else:kept.append(x)
held=list({x['id']:x for x in held}.values())
# Preserve original sample IDs/ordering, publish text only for admitted rows.
kh={x['id']:x for x in kept};hh={x['id']:x for x in held};review=[]
for x in sample:
 review.append(dict(id=x['id'],source=x['source'],status='adopt-bounded-research'if x['id']in kh else'hold',reason=hh.get(x['id'],{}).get('reason','Full original sample read: natural linked prose or original human dialogue/caption; no formal independent factual guarantee'),text=x['text']if x['id']in kh else None))
(P/'QUALITY_REVIEW.json').write_text(json.dumps(dict(fixed_sample_count=len(sample),reviewer='main assistant only, no independent human evaluator',pre_update=True,no_model_predictions_seen=True,raw_held_text_not_republished=True,rows=review,held=held,earlier_gates=['War/religious third-party references and date lists','Biology page19758 held after misleading tRNA explanation; not source text repair']),ensure_ascii=False,indent=2)+'\n');(P/'QUALITY_SAMPLE.json').write_text(json.dumps(dict(seed='quality-fixed-v1',initial_fixed_ids=[x['id']for x in sample],adopted_sample=[x for x in sample if x['id']in kh],holds=[x for x in held if x['id']in{x['id']for x in sample}]),ensure_ascii=False,indent=2)+'\n')
(P/'corpus.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))for x in kept)+'\n').encode(),mtime=0));windows=[]
for i,x in enumerate(kept):
 for start in range(1,len(x['tokens']),192):
  end=min(len(x['tokens']),start+192);windows.append(dict(record=i,input_start=max(0,end-257),target_start=start,end=end,targets=end-start))
buckets=collections.defaultdict(list)
for w in windows:buckets[(w['end']-w['input_start']-2)//32].append(w)
batches=[]
for _,ws in sorted(buckets.items()):
 b=[];active=0;T=0
 for w in ws:
  n=w['end']-w['input_start']-1
  if b and(active+w['targets']>1024 or(len(b)+1)*max(T,n)>4096 or len(b)>=48):batches.append(b);b=[];active=0;T=0
  b.append(w);active+=w['targets'];T=max(T,n)
 if b:batches.append(b)
batches.sort(key=lambda b:sha(('LM-batch-order-v1|'+json.dumps(b,separators=(',',':'))).encode()));sc=dict(batches=batches,one_pass=True,targets=sum(x['targets']for x in windows),body_nonLF_targets=sum(sum(t>=6 and t!=16 for t in x['tokens'][1:])for x in kept),unique_original_records=len(kept),stride=192,max_input=256,epoch_repeats=0)
(P/'SCHEDULE.json').write_text(json.dumps(sc,separators=(',',':'))+'\n');audit=json.loads((P/'SOURCE_AUDIT.json').read_text());audit.update(final_quality_hold_count=len(held),final_sources={s:dict(records=len(a),all_targets=sum(len(x['tokens'])-1 for x in a),body_nonLF=sum(sum(t>=6 and t!=16 for t in x['tokens'][1:])for x in a),EOS=sum(x['tokens'][1:].count(2)for x in a),role=sum(sum(t in[3,4]for t in x['tokens'][1:])for x in a))for s in sorted({x['source']for x in kept})if(a:=[x for x in kept if x['source']==s])},final_targets=sc['targets'],final_updates=len(batches),sample_remaining=sum(x['id']in kh for x in sample),sampling='Length-bucketed batch order, whole original token sequence within every window; windows may visit different document positions in shuffled batch order, no target repeated');(P/'SOURCE_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print('FINAL',len(kept),sc['body_nonLF_targets'],sc['targets'],len(batches),audit['final_sources'])
