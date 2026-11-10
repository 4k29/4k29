"""Frozen prior TRAIN only; LF1 projection, protected DEV and exact target allocation."""
import pathlib,json,gzip,hashlib,re,collections,zlib,sys
P=pathlib.Path(__file__).resolve().parent;V=P.parent;ROOT=V.parents[2]
sys.path.insert(0,str(V));from new_tokenizer import Encoder

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gzwrite(p,x):
 with p.open('wb') as f:
  with gzip.GzipFile(fileobj=f,filename='',mtime=0,mode='wb') as z:z.write(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode())
def collapse(t):
 keep=[i for i,v in enumerate(t) if not(v==16 and i and t[i-1]==16)]
 return [t[i] for i in keep],keep

def canon(t):return ''.join(t.split()).casefold()
def rank(t):return hashlib.sha256(('mixed-retention-108-v1|'+t).encode()).hexdigest()
def signatures(t):return set(sorted({zlib.crc32(t[i:i+13].encode()) for i in range(max(0,len(t)-12))})[:64])

def main():
 assert not(P/'PLAN.json').exists(),'No rebuild after freeze'
 tok=read(V/'data/tokenizer.json');pieces=[bytes.fromhex(x) for x in tok['bytes']];enc=Encoder(tok);assert [i for i,x in enumerate(pieces) if b'\n' in x]==[16]
 prior=V/'modern-corpus/next-foundation';admit=read(prior/'DATASET_AUDIT.json');assert sha(prior/'corpus.jsonl.gz')==admit['corpus_sha256']
 prior_env=json.load(gzip.open(V/'lf-boundary-study/corpus-LF1.json.gz','rt'));env_ids={r['id'] for r in prior_env};env=[json.loads(l) for l in gzip.open(V/'paragraph-foundation/corpus.jsonl.gz','rt') if '"env_whitepaper"' in l];env=[r for r in env if r['id'] in env_ids];assert len(env)==len(prior_env);old=[json.loads(l) for l in gzip.open(prior/'corpus.jsonl.gz','rt')]
 protected=[];families=set();devspeakers=set();unit_source={}
 for path in [V/'pretraining-scale/corpus-clean.jsonl.gz',V/'foundation-stage/data.jsonl.gz']:
  for line in gzip.open(path,'rt'):
   r=json.loads(line);unit_source[r['id']]=r['source']
   if r['split']=='dev':protected.append(dict(id=r['id'],text=r['text']));families.add(r.get('family',r.get('component')))
 for l in (V/'data/dev.docs.jsonl').read_text().splitlines():
  r=json.loads(l);devspeakers.update(r['speakers']);families.add(r['normalizedDocumentFamily']);protected.append(dict(id=r['id'],text='\n'.join(u['text'] for u in r['utterances'])))
 for r in read(V/'diverse-foundation/NEW_DEV_SOURCES.json'):protected.append(dict(id=r['id'],text=r['text']));families.add(r['component'])
 for r in read(V/'paragraph-foundation/PARAGRAPH_DEV_PROTOCOL.json')['cases']:protected.append(dict(id=r['id'],text=r['source_text']));families.add(r['family'])
 ev=read(prior/'EVALUATION.json')
 for r in ev['caption_dev']+ev['maff_dev']:protected.append(dict(id=r['id'],text=b''.join(pieces[v] for v in r['tokens'] if v>5).decode('utf8')))
 devimages=set(read(V/'modern-corpus/STAIR_DEV_FAMILIES.json')['original_TRAIN_image_ids_reserved_for_DEV'])
 index=collections.defaultdict(set);texts=[];exact={};rejections=[]
 def insert(r,protect=False):
  text=canon(r['text']);h=hashlib.sha256(text.encode()).hexdigest();sig=signatures(text);matches=collections.Counter(j for s in sig for j in index[s]);why=None
  if h in exact:why=('canonical',exact[h])
  elif len(text)>=80:
   for j,hits in matches.items():
    if hits<4:continue
    prev,other,is_dev=texts[j]
    if len(other)<80:continue
    a={text[i:i+13] for i in range(len(text)-12)};b={other[i:i+13] for i in range(len(other)-12)}
    if len(a&b)/min(len(a),len(b))>=.85:why=('near_containment_DEV' if is_dev else 'near_containment_TRAIN',prev);break
  if why and not protect:rejections.append(dict(id=r['id'],reason=why[0],matches=why[1]));return False
  j=len(texts);texts.append((r['id'],text,protect));exact[h]=r['id']
  for s in sig:index[s].add(j)
  return True
 for r in protected:insert(r,True)
 previous=V/'mixed-retention-study'
 prior_units=json.load(gzip.open(previous/'corpus.json.gz','rt'));prior_maps=json.load(gzip.open(previous/'POSITION_MAP.json.gz','rt'));prior_s=json.load(gzip.open(previous/'schedule.json.gz','rt'))
 used=set()
 for b in prior_s:
  for ref in b:
   i=ref['record'];mp=prior_maps[i];r=prior_units[i]
   for j in range(ref['start']+1,ref['start']+ref['length']):
    key=(r['source'],r['id'],mp['new_to_original_token_position'][j]);assert key not in used;used.add(key)
 assert len(used)==590144
 old_by={r['id']:i for i,r in enumerate(prior_units)};units=prior_units[:];maps=prior_maps[:];refs=[];newseen=set();counts=collections.Counter();source_stats={};selected_images={r['original_image_id'] for r in prior_units if r['source']=='stair'}
 for r in prior_units:insert(r,True)
 cumulative=dict(env_whitepaper=400000,jaquad=150000,jawikibooks=75000,jawikivoyage=60000,jma=15000,stair=200000,realpersona=100000)
 old_counts=read(previous/'SOURCE_AUDIT.json')['source_stats'];quotas={s:n-old_counts[s]['targets'] for s,n in cumulative.items()}
 pools={s:[] for s in quotas}
 for r in env:pools['env_whitepaper'].append(r)
 for r in old:
  if r['source'] in pools:pools[r['source']].append(r)
 availability={}
 # JMA's complete admitted TRAIN, before sampling/quality filters. Exact residual upper bound.
 for s in pools:
  rawall=sum(len(collapse(r['tokens'])[0])-1 for r in pools[s]);availability[s]=dict(raw_admitted_targets=rawall,previous_used=old_counts[s]['targets'],raw_unused_upper_bound=rawall-old_counts[s]['targets'])
 for source,budget in quotas.items():
  remaining=budget;sc=collections.Counter();chosen=[]
  for raw in sorted(pools[source],key=lambda r:rank(r['id'])):
   if not remaining:break
   assert raw.get('split','train')=='train';sp=set(raw.get('speaker_ids',[]));family=raw.get('family',raw.get('document_family'))
   if family in families or sp&devspeakers:rejections.append(dict(id=raw['id'],reason='DEV family or known speaker'));continue
   t,keep=collapse(raw['tokens'])
   if raw['id'] in old_by:
    i=old_by[raw['id']];start=prior_maps[i]['teacher_limit_new_position'];assert units[i]['tokens']==t and prior_maps[i]['new_to_original_token_position']==keep
    if start==len(t)-1:continue
   else:
    if source=='stair' and (raw['original_image_id'] in devimages or raw['original_image_id'] in selected_images):continue
    if not insert(raw):continue
    r=dict(raw);r['tokens']=t;r['reuse']='Previously admitted TRAIN, no new acquisition';r['research_transform']='maximal LF run>=2 to LF1; original wording unchanged';r['original_text_sha256']=hashlib.sha256(raw['text'].encode()).hexdigest()
    if source=='realpersona':
     cur=1;ut=[]
     for u in raw['utterances']:
      assert t[cur]==u['localRoleToken'];cur+=1;body=[]
      while t[cur]!=2:body.append(t[cur]);cur+=1
      text=re.sub(r'\n{2,}','\n',u['text']);assert b''.join(pieces[v] for v in body)==text.encode();ut.append({**u,'text':text});cur+=1
     assert cur==len(t);r['utterances']=ut;r['text']='\n'.join(u['text'] for u in ut)
    else:
     r['text']=re.sub(r'\n{2,}','\n',raw['text']);assert b''.join(pieces[v] for v in t if v>5)==r['text'].encode();assert enc(r['text'])==[v for v in t if v>5]
    if source=='jaquad':assert 2 not in t
    i=len(units);units.append(r);maps.append(dict(record=i,source=source,id=r['id'],new_to_original_token_position=keep));start=0
    if source=='stair':selected_images.add(raw['original_image_id'])
   n=min(remaining,len(t)-1-start);end=start+n
   for a in range(start,end,256):refs.append(dict(record=i,start=a,length=min(256,end-a)+1))
   for j in range(start+1,end+1):
    key=(source,raw['id'],keep[j]);assert key not in used and key not in newseen;newseen.add(key);v=t[j];sc['targets']+=1;sc['body_nonLF']+=v>5 and v!=16;sc['LF']+=v==16;sc['EOS']+=v==2;sc['role']+=v in [3,4]
   chosen.append(dict(record=i,id=raw['id'],start_exclusive=start,end_inclusive=end,new_positions=n,continued_previous_partial=raw['id'] in old_by));remaining-=n
  source_stats[source]=dict(requested=budget,actual=budget-remaining,available_raw=availability[source],teacher_counts=dict(sc),selected=chosen)
  if remaining:
   write(P/'INSUFFICIENT.json',dict(source=source,shortfall=remaining,source_stats=source_stats));raise RuntimeError(('Insufficient fixed-ratio source',source,remaining))
 assert len(newseen)==409856 and not(newseen&used)
 # Source positions exposed once. Length-bucketed batches at <=1024 valid targets.
 ordered=sorted(refs,key=lambda r:(r['length'],rank(units[r['record']]['id']+':'+str(r['start']))));budgets=[1024]*(209856//1024)+[209856%1024]+[1024]*(200000//1024)+[200000%1024];budgets=[n for n in budgets if n];mid=(209856+1023)//1024;schedule=[];q=offset=0
 for budget in budgets:
  b=[];left=budget
  while left:
   ref=ordered[q];n=min(left,ref['length']-1-offset);b.append(dict(record=ref['record'],start=ref['start']+offset,length=n+1));offset+=n;left-=n
   if offset==ref['length']-1:q+=1;offset=0
  assert len(b)*max(r['length']-1 for r in b)<=2048
  schedule.append(b)
 assert q==len(ordered) and offset==0
 # Hash shuffle across the full available corpus within equal-budget buckets,
 # then use the predeclared 800k/1M budget sequence; no length-sorted phase drift.
 buckets=collections.defaultdict(list)
 for b in schedule:buckets[sum(r['length']-1 for r in b)].append(b)
 for n in buckets:buckets[n].sort(key=lambda b:rank('volume-global|'+'|'.join(str(r) for r in b)))
 schedule=[buckets[n].pop() for n in budgets]
 gzwrite(P/'corpus.json.gz',units);gzwrite(P/'schedule.json.gz',schedule);gzwrite(P/'POSITION_MAP.json.gz',maps)
 write(P/'SOURCE_AUDIT.json',dict(previous_unique_teacher_positions=len(used),additional_unique_teacher_positions=len(newseen),cumulative_unique_teacher_positions=len(used|newseen),overlap=0,new_acquisition_tokens=0,source_stats=source_stats,cumulative_targets=cumulative,availability=availability,updates=len(schedule),midpoint_update=mid,midpoint_additional_targets=209856,terminal_additional_targets=409856,prior_corpus_sha256=sha(previous/'corpus.json.gz'),prior_schedule_sha256=sha(previous/'schedule.json.gz'),prior_mapping_sha256=sha(previous/'POSITION_MAP.json.gz'),protected_DEV_records=len(protected),source_policy='Same previous admitted TRAIN and DEV exclusions; no new corpus; human-only and semantic-family independence limitations inherited'))
 write(P/'REJECTIONS.json',rejections);print('NEW targets',len(newseen),'updates',len(schedule),'mid',mid,'JMA',availability['jma'],flush=True)
if __name__=='__main__':main()
