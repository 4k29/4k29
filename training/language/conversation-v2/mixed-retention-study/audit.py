"""Independent shift/mask/byte audit against unchanged prior admitted source records."""
import pathlib,json,gzip,hashlib,collections,sys
P=pathlib.Path(__file__).resolve().parent;V=P.parent
read=lambda p:json.loads(p.read_text());c=json.load(gzip.open(P/'corpus.json.gz','rt'));maps=json.load(gzip.open(P/'POSITION_MAP.json.gz','rt'));s=json.load(gzip.open(P/'schedule.json.gz','rt'));ids={r['id'] for r in c};orig={}
for path in [V/'modern-corpus/next-foundation/corpus.jsonl.gz',V/'paragraph-foundation/corpus.jsonl.gz']:
 for l in gzip.open(path,'rt'):
  r=json.loads(l)
  if r['id'] in ids:assert r['id'] not in orig;orig[r['id']]=r
assert len(orig)==len(c);pieces=[bytes.fromhex(x) for x in read(V/'data/tokenizer.json')['bytes']];seen=set();cnt=collections.Counter();source=collections.Counter();padding=0;overlap_context=0
for r,m in zip(c,maps):
 old=orig[r['id']];keep=m['new_to_original_token_position'];assert [old['tokens'][i] for i in keep]==r['tokens'];assert [x for x in old['tokens'] if x!=16]==[x for x in r['tokens'] if x!=16];assert [v for v in old['tokens'] if v<6]==[v for v in r['tokens'] if v<6]
 if r['source']=='realpersona':
  for a,b in zip(old['utterances'],r['utterances']):assert a['speakerId']==b['speakerId'] and a['localRoleToken']==b['localRoleToken']
 else:assert b''.join(pieces[v] for v in r['tokens'] if v>5)==r['text'].encode()
for batch in s:
 width=max(r['length']-1 for r in batch);assert width<=256 and len(batch)*width<=2048
 for ref in batch:
  i=ref['record'];row=c[i]['tokens'][ref['start']:ref['start']+ref['length']];x=row[:-1];y=row[1:];assert len(row)==ref['length'];assert 0 not in row and 5 not in row;assert all(a==c[i]['tokens'][ref['start']+j] and b==c[i]['tokens'][ref['start']+j+1] for j,(a,b) in enumerate(zip(x,y)));padding+=width-len(y);overlap_context+=ref['start']>0
  for j,v in enumerate(y,ref['start']+1):
   original=(c[i]['id'],maps[i]['new_to_original_token_position'][j]);assert original not in seen;seen.add(original);cnt['targets']+=1;cnt['body_nonLF']+=v>5 and v!=16;cnt['LF']+=v==16;cnt['EOS']+=v==2;cnt['role']+=v in [3,4];cnt['BOS']+=v==1;source[c[i]['source']]+=1
control=json.load(gzip.open(V/'lf-boundary-study/schedule-LF1.json.gz','rt'));assert [sum(r['length']-1 for r in b) for b in s]==[sum(r['length']-1 for r in b) for b in control];assert cnt['targets']==590144 and cnt['BOS']==0
additional={k:dict(document_families=len({r.get('document_family',r['family']) for r in c if r['source']==k}),licenses=sorted({str(r.get('license',r.get('provenance',{}).get('license','Inherited fixed source LICENSE_NOTICE.md'))) for r in c if r['source']==k})) for k in source}
x=dict(passed=True,teacher_counts=dict(cnt),per_source_targets=dict(source),same_per_update_target_budgets_as_control=True,unique_original_teacher_positions=len(seen),padding_positions_ignored=padding,overlap_context_rows_not_duplicate_targets=overlap_context,no_cross_document_concatenation=True,role_speakers_unchanged=True,no_fake_EOS=True,source_details=additional,prior_rights_scope='Existing bounded exploratory admissions only; author/human-only and semantic near-duplicate independence not proven')
(P/'TEACHER_AUDIT.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');print(json.dumps(x,ensure_ascii=False))
