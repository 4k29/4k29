"""Frozen-corpus boundary frequencies. Stdlib only; no optimizer/model imports."""
import bisect,collections,gzip,hashlib,json,pathlib,re
P=pathlib.Path(__file__).resolve().parent
V=P.parents[1]
ROOT=V.parents[2]
OUT=P/'outputs'
MATA_TEXT='また'
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb')as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
def write(name,d):
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/name).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def gzrows(p):
 with gzip.open(p,'rt')as f:
  for s in f:yield json.loads(s)
def lf_run_before(tokens,pos,start=0,nl=16):
 n=0
 for j in range(pos-1,start-1,-1):
  if tokens[j]!=nl:break
  n+=1
 return n
def run_name(n):return 'after_LF_exact1'if n==1 else'after_LF_exact2'if n==2 else'after_LF_3plus'if n>2 else'no_visible_LF'
def literal_class(raw,offset):
 n=0
 while offset-n>0 and raw[offset-n-1]==10:n+=1
 if n:return run_name(n)
 if offset==0:return 'unit_start'
 if raw[max(0,offset-3):offset]in['。'.encode(),'！'.encode(),'？'.encode()]or raw[offset-1:offset]in[b'!',b'?']:return 'after_sentence_punctuation_no_LF'
 return 'middle_no_LF_or_terminal_punctuation'
def reference_sequences(r,pieces):
 """Never interpret human-readable utterance joins as trained LF tokens."""
 if r['source']!='realpersona':
  yield r
  return
 runs=[];cur=[]
 for t in r['tokens']:
  if t>=6:cur.append(t)
  elif cur:runs.append(cur);cur=[]
 if cur:runs.append(cur)
 assert len(runs)==len(r['utterances'])
 for i,(tokens,u)in enumerate(zip(runs,r['utterances'])):
  assert b''.join(pieces[t]for t in tokens)==u['text'].encode()
  yield dict(id=r['id']+':turn'+str(i),source='realpersona',text=u['text'],tokens=tokens,
             BOS=False,EOS=False,start_kind='utterance_start',document_start=i==0)
class CounterSet:
 def __init__(self,mata,pieces):
  self.mata=mata;self.pieces=pieces;self.units=0;self.bins=collections.defaultdict(collections.Counter)
  self.literal=collections.Counter();self.literal_next=collections.Counter();self.scalar=collections.Counter();self.runs=collections.Counter()
 def add(self,r,refs=None,teacher_all=None):
  tokens=r['tokens'];pieces=self.pieces
  positions=[i for i,t in enumerate(tokens)if t>=6]
  raw=b''.join(pieces[tokens[i]]for i in positions)
  assert raw==r['text'].encode('utf8')
  self.runs.update(len(x)for x in re.findall(rb'\n+',raw))
  starts=[];ends=[];offset=0
  for i in positions:
   starts.append(offset);offset+=len(pieces[tokens[i]]);ends.append(offset)
  learned=set(); visible={}
  if refs is not None:
   for ref in refs:
    start=ref['start'];end=start+ref['length'];seq=tokens[start:end]
    assert len(seq)==ref['length']and 2<=len(seq)<=257 and all(t!=0 for t in seq)
    for j in range(start+1,end):
     assert j not in learned,'Duplicate teacher source position'
     learned.add(j);visible[j]=lf_run_before(tokens,j,start)
     if teacher_all is not None:teacher_all[tokens[j]]+=1
  self.units+=1
  local=collections.Counter(units=1,characters=len(r['text']),UTF8_bytes=len(raw))
  for k,i in enumerate(positions):
   t=tokens[i];cat=literal_class(raw,starts[k])
   self.bins['all_body_tokens'][t]+=1;self.bins[cat][t]+=1
   if t!=16 and cat.startswith('after_LF_'):self.bins[cat+'_body_only'][t]+=1
   if k==0:
    self.bins['declared_BOS_unit_start'if r.get('BOS')else'unit_start_without_BOS'][t]+=1
    if r.get('start_kind')=='utterance_start':self.bins['utterance_start'][t]+=1
    if r.get('document_start'):self.bins['conversation_start'][t]+=1
   local['body_tokens']+=1;local['token_mata']+=t==self.mata
   local['LF2_body_starts']+=cat=='after_LF_exact2'and t!=16
   local['LF2_token_mata']+=cat=='after_LF_exact2'and t==self.mata
   if refs is not None and i in learned:
    self.bins['teacher_all_body_tokens'][t]+=1
    self.bins['teacher_source_'+cat][t]+=1
    vis=run_name(visible[i])
    self.bins['teacher_visible_'+vis][t]+=1
    self.scalar['visibility:'+cat+'->'+vis]+=1
    local['teacher_body_tokens']+=1;local['teacher_token_mata']+=t==self.mata
    local['teacher_LF2_token_mata']+=cat=='after_LF_exact2'and t==self.mata
   elif refs is not None:self.scalar['body_positions_not_taught']+=1
  needle=MATA_TEXT.encode();cursor=0
  while True:
   at=raw.find(needle,cursor)
   if at<0:break
   cursor=at+len(needle);cat=literal_class(raw,at)
   self.literal['all']+=1;self.literal[cat]+=1
   k=bisect.bisect_right(starts,at)-1;last=bisect.bisect_right(starts,at+len(needle)-1)-1
   assert k>=0 and ends[last]>=at+len(needle)
   self.scalar['literal_starts_at_BPE_boundary']+=starts[k]==at
   self.scalar['literal_inside_BPE_piece']+=starts[k]!=at
   self.scalar['literal_spans_multiple_BPE_tokens']+=last!=k
   suffix=raw[at+len(needle):].decode('utf8');self.literal_next[suffix[:1]or'<END>']+=1
   if refs is not None and all(positions[j]in learned for j in range(k,last+1)):
    self.literal['teacher_all_covering_tokens_exposed']+=1
    self.literal['teacher_source_'+cat]+=1
   local['literal_mata']+=1
  self.scalar.update(local)
  return local
 def export(self):
  def row(t,n):
   b=self.pieces[t]
   try:s=b.decode('utf8')
   except UnicodeDecodeError:s=None
   return dict(token=t,piece=s,hex=b.hex(),count=n)
  return dict(units=self.units,scalar=dict(self.scalar),literal_mata=dict(self.literal),raw_newline_run_lengths=dict(self.runs),
   literal_next_character=dict(self.literal_next.most_common(20)),
   distributions={key:dict(total=sum(c.values()),mata_count=c[self.mata],
      mata_fraction=c[self.mata]/sum(c.values())if sum(c.values())else None,
      newline_count=c[16],top20=[row(t,n)for t,n in c.most_common(20)],
      counts_by_token={str(t):n for t,n in c.items()})for key,c in self.bins.items()})
def group_summary(groups,key):
 rows=[dict(group=k,**dict(v))for k,v in groups.items()]
 total=sum(r.get(key,0)for r in rows)
 order=sorted(rows,key=lambda r:(-r.get(key,0),r['group']))
 chosen=order[:5]
 return dict(total_mata=total,HHI=sum((r.get(key,0)/total)**2 for r in rows)if total else None,
  top5_mata_share=sum(r.get(key,0)for r in chosen)/total if total else None,
  same_top5_body_token_share=sum(r.get('body_tokens',0)for r in chosen)/sum(r.get('body_tokens',0)for r in rows),
  rows=order)
def main():
 tok_path=V/'data/tokenizer.json';tok=read(tok_path);pieces=[bytes.fromhex(x)for x in tok['bytes']]
 mata=pieces.index(MATA_TEXT.encode());assert mata==3749 and pieces[16]==b'\n'
 plan=read(P.parent/'PLAN.json')
 for f in [P.parent/'corpus.jsonl.gz',P.parent/'schedule.json.gz',tok_path]:
  assert sha(f)==plan['input_sha256'][str(f.relative_to(ROOT))]
 old=V/'diverse-foundation/corpus.jsonl.gz'
 assert sha(old)=='a09c03dd95d007bc97b0566fdbe6d43cce2b6b19b146426c32a4a7c43a9ea247'
 schedule=json.load(gzip.open(P.parent/'schedule.json.gz','rt'))
 refs={arm:collections.defaultdict(list)for arm in ['A','B']}
 padding={}
 for arm in refs:
  ignored=0
  for bi,batch in enumerate(schedule['arms'][arm]):
   assert sum(r['length']-1 for r in batch)==schedule['target_counts'][bi]
   width=max(r['length']-1 for r in batch)
   ignored+=sum(width-(r['length']-1)for r in batch)
   for r in batch:refs[arm][r['record']].append(r)
  padding[arm]=ignored
 B=CounterSet(mata,pieces);A=CounterSet(mata,pieces);Aused=CounterSet(mata,pieces)
 all_teachers={'A':collections.Counter(),'B':collections.Counter()}
 groups={k:collections.defaultdict(collections.Counter)for k in ['year','document','heading','document_heading']}
 for i,r in enumerate(gzrows(P.parent/'corpus.jsonl.gz')):
  if r['source']=='env_whitepaper':
   assert i in refs['B']and i not in refs['A']
   local=B.add(r,refs['B'][i],all_teachers['B'])
   values=dict(year=str(r['publication_year']),document=r['document_family'],heading=r['heading'],
    document_heading=r['document_family']+'|'+r['heading'])
   for key,value in values.items():groups[key][value].update(local)
  else:
   assert r['source']=='stair_unused_annotation'
   A.add(r)
   if i in refs['A']:Aused.add(r,refs['A'][i],all_teachers['A'])
 assert sum(all_teachers['B'].values())==591997
 assert sum(all_teachers['A'].values())==591997
 assert B.scalar['body_tokens']==592132
 refstats={};excluded=collections.Counter()
 for r in gzrows(old):
  if r.get('split')!='train':excluded[str(r.get('split'))]+=1;continue
  assert r['source']in ['realpersona','jawikibooks','jawikivoyage','jaquad','jma']
  counter=refstats.setdefault(r['source'],CounterSet(mata,pieces))
  for unit in reference_sequences(r,pieces):counter.add(unit)
 out=dict(schema_version=1,statistics_code_sha256=sha(__file__),optimizer_updates=0,model_forward_calls=0,
  methods=dict(raw='Each admitted body source position; no deduplication or cross-unit concatenation added.',
   teacher='Unique (record, source_token_position) in actual579-update schedule; seq[:-1] inputs, seq[1:] teachers; rightPAD input0 / ignore labels-100 excluded.',
   visible='Separate source-context and actual row-visible LF run; row truncation can hide an LF without changing the gold token.',
   exact1='Exactly one immediately preceding LF: includes the second LF teacher of a two-LF separator.',
   exact2='Exactly two immediately preceding LF; no semantic paragraph classifier.',
   middle='Not unit start, immediate LF, or literal sentence punctuation; not a linguistic clause tag.',
   unit_start='Start of extracted unit, not necessarily true whole-document start. BOS-certified source-unit starts and fragments reported separately.',
   literal='Nonoverlapping UTF8 substringまた, includingまたは/たまたま etc.; no conjunction POS claim. Teacher substring counted only if every covering BPE token is an actual target.',
   realpersona='Split original token runs at special roles/EOS and match each original utterance; NEVER use synthetic LF joins from display text.',
   references='Historical TRAIN raw source positions only, not equal exposure in B579. STAIR pool and actualA-used subset shown separately.'),
  vocabulary_mata_id=mata,actual_B=B.export(),reference_STAIR_pool=A.export(),
  actual_A_used_reference=Aused.export(),historical_reference_TRAIN={k:v.export()for k,v in refstats.items()},
  historical_nonTRAIN_rows_excluded=dict(excluded),padding_ignored_positions=padding,
  actual_teacher_totals={k:dict(total=sum(c.values()),EOS=c[2],PAD=c[0],newline=c[16],mata=c[mata])for k,c in all_teachers.items()},
  concentration={group:{'token_mata':group_summary(gs,'token_mata'),'after_LF2_token_mata':group_summary(gs,'LF2_token_mata')}for group,gs in groups.items()},
  source_sha256={str(f.relative_to(ROOT)):sha(f)for f in [P.parent/'corpus.jsonl.gz',P.parent/'schedule.json.gz',old,tok_path]},
  limitations=['One source family for B; source-page and heading counts are not independent-author families.',
   'Literal line/paragraph markers do not certify semantic starts. Whole-whitepaper document starts are not identified.',
   'Historical source positions can include naturally repeated wording; no new independent-data claim.'])
 write('DATA_STATISTICS.json',out)
 def compact(stats):
  return {k:({n:{a:b for a,b in v.items()if a!='counts_by_token'}for n,v in value.items()}if k=='distributions'else value)for k,value in stats.items()}
 small={k:v for k,v in out.items()if k not in ['actual_B','reference_STAIR_pool','actual_A_used_reference','historical_reference_TRAIN','concentration']}
 for key in ['actual_B','reference_STAIR_pool','actual_A_used_reference']:small[key]=compact(out[key])
 small['historical_reference_TRAIN']={k:compact(v)for k,v in out['historical_reference_TRAIN'].items()}
 small['concentration']={group:{metric:{**{k:v for k,v in d.items()if k!='rows'},'rows':d['rows'][:10]}for metric,d in values.items()}for group,values in out['concentration'].items()}
 write('DATA_SUMMARY.json',small)
 print('B admittedbody / actual targets:',B.scalar['body_tokens'],sum(all_teachers['B'].values()))
if __name__=='__main__':main()
