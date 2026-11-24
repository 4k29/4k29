"""Offline staged corpus audit and matched-budget preparation. Never imports a model.

Run after restoring the licensed PR117 and PR116 artifacts. Does not acquire data.
Only original admitted paragraphs, not risk-held/private pool texts, are public.
"""
import pathlib,json,gzip,hashlib,collections,statistics,sys
P=pathlib.Path(__file__).resolve().parent;V=P.parent
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(pathlib.Path(p).read_text())
def rows(p):return [json.loads(s) for s in gzip.decompress(pathlib.Path(p).read_bytes()).splitlines()]
def write(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def combined():return rows(V/'novel-continuous-study/REVIEWED_PROSE.jsonl.gz')+rows(P/'ADDITIONAL_PROSE.jsonl.gz')
def windows(rs):
 for j,r in enumerate(rs):
  t=r['tokens']
  for a in range(1,len(t),192):
   end=min(a+192,len(t));yield dict(record=j,input_start=max(0,end-257),target_start=a,end=end,targets=end-a)
def pack(refs,limit=None):
 """Split active positions, not documents; preserve <=256-token left histories.
 A split's left history can repeat as input; each teacher position occurs once.
 """
 batches=[];batch=[];used=0;total=0
 for z in refs:
  a=z['target_start']
  while a<z['end'] and (limit is None or total<limit):
   n=min(z['end']-a,1024-used,limit-total if limit is not None else 1024)
   e=a+n;batch.append(dict(record=z['record'],input_start=max(z['input_start'],e-257),target_start=a,end=e,targets=n))
   a=e;used+=n;total+=n
   if used==1024:batches.append(batch);batch=[];used=0
  if limit is not None and total==limit:break
 if batch:batches.append(batch)
 assert limit is None or total==limit
 return batches

def audit_schedule(rs,bs):
 seen=set();counts=collections.Counter();lengths=[];input_tokens=0
 for b in bs:
  for z in b:
   r=rs[z['record']];t=r['tokens'];a=z['input_start'];e=z['end'];s=z['target_start'];x=t[a:e-1];y=t[a+1:e]
   assert x[1:]==y[:-1] and 0<len(x)<=256 and a<s<e
   assert z['targets']==e-s
   lengths.append(len(x));input_tokens+=len(x)
   for k in range(s,e):
    identity=(r['id'],k);assert identity not in seen;seen.add(identity)
    q=t[k];assert q!=0 and q!=1
    counts['EOS' if q==2 else 'role' if q in (3,4,5) else 'LF' if q==16 else 'body_nonLF']+=1
 return dict(targets=len(seen),types=dict(counts),batches=len(bs),windows=len(lengths),input_nonPAD=input_tokens,repeated_history_input_positions_allowed=True,duplicate_teacher_positions=0,input_length=dict(min=min(lengths),median=statistics.median(lengths),max=max(lengths)),per_batch_targets=[sum(z['targets']for z in b)for b in bs])

def main():
 rs=combined();sys.path.insert(0,str(V));from new_tokenizer import Encoder
 tok=read(V/'data/tokenizer.json');enc=Encoder(tok);pieces=[bytes.fromhex(s)for s in tok['bytes']]
 assert len(pieces)==3997
 for r in rs:
  assert [1]+enc(r['text'])+([2]if r['EOS']else[])==r['tokens']
  assert b''.join(pieces[k]for k in r['tokens']if k>=6)==r['text'].encode()
  assert hashlib.sha256(r['text'].encode()).hexdigest()==r['text_SHA']
  assert not r['EOS'] and 2 not in r['tokens']
 assert len({r['text_SHA']for r in rs})==len(rs)
 dev=read(V/'novel-continuous-study/NEW_PROSE_DEV.json')['cases'];assert not {r['family']for r in rs}&{r['family']for r in dev}
 # Inherit PR117 full-pool novelty screen, then validate the newly selected IDs/tokens
 # against the frozen pool when private cache is present. Never publish held texts.
 pool=V/'novel-continuous-study/narrowed-pool-private.jsonl.gz'
 if pool.exists():
  idx={r['id']:r for r in rows(pool)}
  for r in rows(P/'ADDITIONAL_PROSE.jsonl.gz'):assert r['id']in idx and r['tokens']==idx[r['id']]['tokens'] and r['text_SHA']==idx[r['id']]['text_SHA']
 T=sum(len(r['tokens'])-1 for r in rs);c=pack(windows(rs));old=read(V/'foundation-absorption-study/SCHEDULE.json');b=pack((z for batch in old['batches']for z in batch),T)
 br=rows(V/'foundation-absorption-study/corpus.jsonl.gz');ca=audit_schedule(rs,c);ba=audit_schedule(br,b)
 assert ca['targets']==ba['targets']==T and ca['batches']==ba['batches'] and ca['per_batch_targets']==ba['per_batch_targets']
 write('SCHEDULE.json',dict(status='PREPARATION ONLY; no training GO',one_pass=True,teachers=T,optimizer_updates_if_authorized=ca['batches'],C_small=c,B_small=b,C_record_order=[r['id']for r in rs],B_source_schedule_SHA=sha(V/'foundation-absorption-study/SCHEDULE.json'),B_source_corpus_SHA=sha(V/'foundation-absorption-study/corpus.jsonl.gz')))
 write('TEACHER_AUDIT.json',dict(byte_BPE_exact=True,shift_verified=True,no_padding_as_teacher=True,no_fake_EOS=True,C=ca,B=ba,source_records_never_concatenated=True,identical_per_update_teacher_counts=True,not_single_factor_due_to_source_and_shapes=True,forwards=0,optimizer_calls=0))
 print(json.dumps(dict(C=ca,B=ba),ensure_ascii=False))
if __name__=='__main__':main()
