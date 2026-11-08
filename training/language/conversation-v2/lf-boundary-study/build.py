"""Project existing B rows onto LF1 tokens without selecting/reordering any body target."""
import gzip,json,hashlib,pathlib,collections,sys
P=pathlib.Path(__file__).resolve().parent;V=P.parent;OLD=V/'paragraph-foundation'
sys.path.insert(0,str(V));from new_tokenizer import Encoder

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gzwrite(p,x):
 with p.open('wb') as f:
  with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0) as g:g.write(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode())
def collapse(t):
 # Token LF has its own vocabulary entry; longer runs are rejected, not silently normalized.
 assert not any(t[i:i+3]==[16]*3 for i in range(len(t)-2))
 keep=[i for i,v in enumerate(t) if not(v==16 and i and t[i-1]==16)]
 return [t[i] for i in keep],keep

def main():
 assert not(P/'PLAN.json').exists(),'Frozen experiment must not be rebuilt'
 corpus=[json.loads(l) for l in gzip.open(OLD/'corpus.jsonl.gz','rt')];sched=json.load(gzip.open(OLD/'schedule.json.gz','rt'))['arms']['B'];ids=sorted({r['record'] for b in sched for r in b});tok=json.loads((V/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(t) for t in tok['bytes']];enc=Encoder(tok)
 units=[];maps={};lookup={};LF2=0;bytes_ok=0;boundary_coverage=collections.Counter()
 for i in ids:
  r=corpus[i];t=r['tokens'];new,keep=collapse(t);deleted=sorted(set(range(len(t)))-set(keep));LF2+=len(deleted)
  body=lambda ids:b''.join(pieces[v] for v in ids if v>5)
  assert body(t).decode()==r['text']; text=r['text'].replace('\n\n','\n');assert body(new).decode()==text
  assert enc(text)==[v for v in new if v>5];bytes_ok+=1
  assert [v for v in t if v!=16]==[v for v in new if v!=16]
  newrow={**r,'text':text,'tokens':new,'body_token_count':sum(v>5 for v in new),'research_transform':'LF2 to LF1; source unchanged','original_text_sha256':r['text_sha256'],'text_sha256':hashlib.sha256(text.encode()).hexdigest()}
  lookup[i]=len(units);units.append(newrow);maps[i]=dict(original_record=i,source_id=r['id'],new_to_original_token_position=keep,deleted_original_LF_positions=deleted,original_length=len(t),transformed_length=len(new))
 batches=[];seenold=set();seennew=set();originalcounts=collections.Counter();newcounts=collections.Counter();boundarysplit=0;inputchanges=0;rows=0
 for bi,b in enumerate(sched):
  batch=[]
  for ri,r in enumerate(b):
   i=r['record'];a=r['start'];end=a+r['length'];t=corpus[i]['tokens'];keep=maps[i]['new_to_original_token_position'];old2new={v:k for k,v in enumerate(keep)}
   targets=[p for p in range(a+1,end) if p in old2new]
   assert targets
   start=old2new[targets[0]]-1;length=len(targets)+1
   assert start>=0 and [keep[k] for k in range(start+1,start+length)]==targets
   row=dict(record=lookup[i],start=start,length=length,original_record=i,original_start=a,original_length=r['length'],original_batch=bi,original_row=ri)
   batch.append(row);rows+=1;inputchanges+=length!=r['length']
   for pos in range(a+1,end):
    assert(i,pos)not in seenold;seenold.add((i,pos));originalcounts[str(t[pos])]+=1
    if pos>=2 and t[pos-2:pos]==[16,16]:boundary_coverage['visible' if pos-2>=a else 'split']+=1
   for pos in targets:
    assert(i,pos)not in seennew;seennew.add((i,pos));newcounts[str(t[pos])]+=1
  batches.append(batch)
 nonLFold={x for x in seenold if corpus[x[0]]['tokens'][x[1]]!=16};nonLFnew={x for x in seennew if corpus[x[0]]['tokens'][x[1]]!=16};assert nonLFold==nonLFnew
 def stats(c):return dict(total_targets=sum(c.values()),LF_targets=c['16'],EOS_targets=c['2'],BOS_targets=c['1'],role_targets=c['3']+c['4'],nonLF_targets=sum(v for k,v in c.items() if k!='16'),body_nonLF_targets=sum(v for k,v in c.items() if int(k)>5 and k!='16'))
 audit=dict(LF2_source_boundaries=LF2,LF1_conversions=LF2,units=len(units),original_body_tokens=sum(corpus[i]['body_token_count'] for i in ids),LF1_body_tokens=sum(r['body_token_count'] for r in units),all_nonboundary_tokens_preserved=True,byte_and_BPE_roundtrip_units=bytes_ok,LF2=stats(originalcounts),LF1=stats(newcounts),updates=len(batches),rows=rows,rows_with_shortened_input=inputchanges,original_row_budget_and_order_preserved=True,boundary_teacher_visibility=dict(boundary_coverage),duplicate_targets=0,mean_input_length_LF2=sum(r['length']-1 for b in sched for r in b)/rows,mean_input_length_LF1=sum(r['length']-1 for b in batches for r in b)/rows,new_rechunking=False,comparison_limitations=['Same batch membership/order; shorter row/positions changes dropout consumption and per-update CE normalization.','Mapped preceding survivor is used when original first input token was deleted.','No extra targets or repeated epoch to fill budget.'])
 assert LF2==1853
 gzwrite(P/'corpus-LF1.json.gz',units);gzwrite(P/'POSITION_MAP.json.gz',list(maps.values()));gzwrite(P/'schedule-LF1.json.gz',batches);write(P/'TRANSFORM_AUDIT.json',audit)
 print(json.dumps(audit,ensure_ascii=False))
if __name__=='__main__':main()
