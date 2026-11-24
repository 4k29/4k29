"""Exact positions, FAQ/prose near-overlap, ancestral exposure and LF-only mapping."""
import pathlib,json,gzip,hashlib,zlib,heapq,collections,unicodedata,os
P=pathlib.Path(__file__).resolve().parent;assert not(P/'PLAN.json').exists(),'Do not overwrite frozen study; rebuild in a new directory';V=P.parent;C=pathlib.Path(os.environ.get('ABSORPTION_CACHE','/workspace/scratch/absorption'));rd=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(x)for x in gzip.decompress(p.read_bytes()).splitlines()];canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split());sha=lambda b:hashlib.sha256(b).hexdigest();r=lines(P/'corpus.jsonl.gz');prior=lines(C/'diverse-foundation/corpus.jsonl.gz')+lines(C/'paragraph-foundation/corpus.jsonl.gz');orig={x['id']:x for x in prior};old=lines(C/'modern-corpus/next-foundation/corpus.jsonl.gz');past={x['id']for x in old};mixed=json.loads(gzip.decompress((C/'mixed-retention-study/corpus.json.gz').read_bytes()));mixedids={x['id']for x in mixed};faq=rd(V/'faq-ce-verified-study/DATA.json');dev=rd(P/'PROSE_DEV.json')['cases'];refs=[dict(id=x['id']+':'+k,text=x[k])for rs in faq['parts'].values()for x in rs for k in['question','response']]+[dict(id=x['id'],text=x['text'])for x in dev]
def shingles(text):
 t=canon(text);return {zlib.crc32(t[i:i+13].encode())for i in range(max(0,len(t)-12))}
refsets=[shingles(x['text'])for x in refs];idx=collections.defaultdict(set)
for i,ss in enumerate(refsets):
 for v in heapq.nsmallest(64,ss):idx[v].add(i)
cross=[];maprows=[];exposure=collections.Counter();internal_idx=collections.defaultdict(set);internal=[];ss_cache=[]
for i,x in enumerate(r):
 assert x['id']not in mixedids;oldts=orig[x['id']]['tokens'];keep=[j for j,t in enumerate(oldts)if not(t==16 and j and oldts[j-1]==16)];assert [oldts[j]for j in keep]==x['tokens'],x['id'];maprows.append(dict(id=x['id'],original_length=len(oldts),removed_LF_positions=[j for j in range(len(oldts))if j not in set(keep)],mapping_SHA=sha(json.dumps(keep,separators=(',',':')).encode())))
 exposure[(x['source'],'PR105_selected'if x['id']in past else'not_PR105_or_MIX_selected')]+=sum(t>=6 and t!=16 for t in x['tokens'][1:]);ss=shingles(x['text']);sig=heapq.nsmallest(64,ss);hits=collections.Counter(j for h in sig for j in idx[h])
 for j,n in hits.items():
  if n>=4 and min(len(ss),len(refsets[j]))>=16 and len(ss&refsets[j])/min(len(ss),len(refsets[j]))>=.85:cross.append(dict(train=x['id'],reference=refs[j]['id']))
 hits=collections.Counter(j for h in sig for j in internal_idx[h])
 for j,n in hits.items():
  other=ss_cache[j]
  if n>=4 and min(len(ss),len(other))>=16 and len(ss&other)/min(len(ss),len(other))>=.85:internal.append(dict(left=r[j]['id'],right=x['id'],same_family=r[j]['family']==x['family']))
 ss_cache.append(ss)
 for h in sig:internal_idx[h].add(i)
assert not cross,cross
seen=set();source=collections.Counter();context=0;pad=0;windows=0
for b in rd(P/'SCHEDULE.json')['batches']:
 T=max(w['end']-w['input_start']-1 for w in b);pad+=len(b)*T
 for w in b:
  x=r[w['record']];assert 1<=w['target_start']<=w['end']-1;assert w['end']-w['input_start']-1<=256;context+=w['target_start']-w['input_start']-1;pad-=w['end']-w['input_start']-1;windows+=1
  for k in range(w['target_start'],w['end']):
   assert (x['id'],k)not in seen;seen.add((x['id'],k));source[x['source']]+=1
assert len(seen)==rd(P/'SCHEDULE.json')['targets'];assert all((x['id'],k)in seen for x in r for k in range(1,len(x['tokens'])));assert len({canon(x['text'])for x in r})==len(r)
out=dict(passed=True,all_original_nonboundary_tokens_preserved=True,LF_only_position_mapping=True,target_positions=len(seen),repeated_active_teacher_positions=0,left_context_reexposure=context,PAD_ignored=pad,windows=windows,source_targets=dict(source),FAQ_and_PROSE_DEV_near_cross=cross,internal_near_pairs=internal,near_method='13-character crc32 shingles,64 minimum signatures,>=4candidate hits then85%shorter-set containment; not exhaustive semantic guarantee',historical_exposure=[dict(source=s,status=e,nonLF_body_targets=n)for(s,e),n in exposure.items()],MIX579_selected_record_cross=0,PLAN_not_yet_frozen=True,optimizer_calls=0,model_forwards=0)
(P/'POSITION_MAP.json.gz').write_bytes(gzip.compress((json.dumps(maprows,separators=(',',':'))+'\n').encode(),mtime=0));(P/'POSITION_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('audit',len(seen),'context-only',context,'near cross',len(cross),'internalpairs',len(internal),'exposure',out['historical_exposure'])
