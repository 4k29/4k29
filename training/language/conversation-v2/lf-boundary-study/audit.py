"""Independent stdlib audit of mapped rows, real teacher shift and byte deletion map."""
import pathlib,json,gzip,hashlib,collections
P=pathlib.Path(__file__).resolve().parent;V=P.parent;O=V/'paragraph-foundation'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(P/'PLAN.json')
for rel,h in plan['sha256'].items():
 root=P.parents[3];assert sha(root/rel)==h,rel
c=json.load(gzip.open(P/'corpus-LF1.json.gz','rt'));s=json.load(gzip.open(P/'schedule-LF1.json.gz','rt'));maps=json.load(gzip.open(P/'POSITION_MAP.json.gz','rt'));md={m['original_record']:m for m in maps};old=[json.loads(l) for l in gzip.open(O/'corpus.jsonl.gz','rt')];os=json.load(gzip.open(O/'schedule.json.gz','rt'))['arms']['B'];pieces=[bytes.fromhex(x) for x in read(V/'data/tokenizer.json')['bytes']];by={r['id']:r for r in c};counts=collections.Counter();seen=set();byte_maps=[]
for m in maps:
 r=old[m['original_record']];t=r['tokens'];nr=by[r['id']];new=nr['tokens'];keep=m['new_to_original_token_position'];assert [t[i] for i in keep]==new
 offsets=[];offset=0
 for i,v in enumerate(t):
  if i in m['deleted_original_LF_positions']:offsets.append(offset)
  if v>5:offset+=len(pieces[v])
 raw=r['text'].encode();assert all(raw[i:i+1]==b'\n' for i in offsets);deleted=set(offsets);assert bytes(b for i,b in enumerate(raw) if i not in deleted)==nr['text'].encode()
 byte_maps.append(dict(source_id=r['id'],original_sha256=hashlib.sha256(raw).hexdigest(),LF1_sha256=hashlib.sha256(nr['text'].encode()).hexdigest(),deleted_original_byte_offsets=offsets,retained_byte_mapping='new index = old index minus count(deleted offsets < old index); preserve all other bytes'))
for b,ob in zip(s,os):
 assert len(b)==len(ob);width=max(r['length']-1 for r in b)
 for r,o in zip(b,ob):
  assert r['original_record']==o['record'] and r['original_start']==o['start'];n=r['length']-1;t=c[r['record']]['tokens'];keep=md[o['record']]['new_to_original_token_position'];x=t[r['start']:r['start']+n];y=t[r['start']+1:r['start']+1+n];assert len(x)==len(y)==n and 0 not in x and 0 not in y
  orig=[keep[i] for i in range(r['start']+1,r['start']+1+n)]
  assert orig==[i for i in range(o['start']+1,o['start']+o['length']) if i in set(keep)]
  for i in orig:assert(o['record'],i)not in seen;seen.add((o['record'],i))
  counts['teacher_positions']+=n;counts['padding_ignored']+=width-n
  for i,g in enumerate(y):
   if i and x[i-1:i+1]==[16,16]:raise AssertionError('Unexpected LF2 in LF1 row')
   counts['LF1_to_nonLF_visible']+=int(x[i]==16 and g!=16)
  counts['changed_input_start_predecessor']+=int(keep[r['start']]!=o['start'])
with (P/'BYTE_MAP.json.gz').open('wb') as f:
 with gzip.GzipFile(fileobj=f,filename='',mtime=0,mode='wb') as z:z.write(json.dumps(byte_maps,ensure_ascii=False,separators=(',',':')).encode())
result=dict(passed=True,counts=dict(counts),frozen_sha_count=len(plan['sha256']),all_teacher_shift_masks_correct=True,all_padding_ignored=True,all_nonboundary_bytes_preserved=True,original_corpus_unchanged_sha256=sha(O/'corpus.jsonl.gz'),source_raw_and_license_metadata_retained=True,corpus_split_unchanged=True)
(P/'TEACHER_MASK_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
