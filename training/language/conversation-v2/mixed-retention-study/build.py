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
 assert not(P/'PLAN.json').exists(),'Do not rebuild frozen experiment'
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
 quotas=dict(env_whitepaper=236058,jaquad=88522,jawikibooks=44261,jawikivoyage=35409,jma=8851,stair=118029,realpersona=59014);pools={s:[] for s in quotas};eligible=collections.Counter()
 for r in env:pools['env_whitepaper'].append(r)
 for r in old:
  if r['source'] in pools:pools[r['source']].append(r)
 units=[];refs=[];maps=[];stats={};selected_images=set();changedruns=collections.Counter()
 for source,budget in quotas.items():
  remaining=budget;used=0;unit_ids=[];speaker_ids=set();components=set();counts=collections.Counter();full_body=0;exposed_body=0;target_original=set()
  for raw in sorted(pools[source],key=lambda r:rank(r['id'])):
   if not remaining:break
   if raw.get('split','train')!='train':raise AssertionError('Only already-admitted TRAIN allowed')
   family=raw.get('family',raw.get('document_family'));sp=set(raw.get('speaker_ids',[]))
   if family in families or sp&devspeakers:rejections.append(dict(id=raw['id'],reason='DEV family or known speaker'));continue
   if source=='stair':
    image=raw['original_image_id']
    if image in devimages or image in selected_images:rejections.append(dict(id=raw['id'],reason='DEV image or repeated selected image family'));continue
   if not insert(raw):continue
   t,keep=collapse(raw['tokens']);assert [v for v in t if v!=16]==[v for v in raw['tokens'] if v!=16];r=dict(raw);r['tokens']=t;r['original_text_sha256']=hashlib.sha256(raw['text'].encode()).hexdigest();r['body_token_count']=sum(v>5 for v in t);r['reuse']='Already admitted prior TRAIN; acquisition=0, previous model exposure exists';r['research_transform']='maximal original LF run>=2 to LF1; no other byte changes'
   original=raw['tokens'];offset=0;deleted_bytes=[];keepset=set(keep)
   for j,v in enumerate(original):
    if j not in keepset:deleted_bytes.append(offset)
    if v>5:offset+=len(pieces[v])
   if source=='realpersona':
    cur=1;newutterances=[]
    for u in raw['utterances']:
     assert t[cur]==u['localRoleToken'];cur+=1;body=[]
     while t[cur]!=2:body.append(t[cur]);cur+=1
     text=re.sub(r'\n{2,}','\n',u['text']);assert b''.join(pieces[v] for v in body)==text.encode();newutterances.append({**u,'text':text});cur+=1
    assert cur==len(t);r['utterances']=newutterances;r['text']='\n'.join(u['text'] for u in newutterances)
   else:
    r['text']=re.sub(r'\n{2,}','\n',raw['text']);assert b''.join(pieces[v] for v in t if v>5)==r['text'].encode();assert enc(r['text'])==[v for v in t if v>5]
   if source=='jaquad':assert 2 not in t
   i=len(units);units.append(r);limit=min(len(t)-1,remaining);unit_ids.append(r['id']);full_body+=r['body_token_count'];exposed_body+=sum(v>5 for v in t[:limit+1]);speaker_ids|=sp;components.add(family)
   for start in range(0,limit,256):refs.append(dict(record=i,start=start,length=min(256,limit-start)+1))
   for j,v in enumerate(t[1:limit+1],1):counts['targets']+=1;counts['body_nonLF']+=v>5 and v!=16;counts['LF']+=v==16;counts['EOS']+=v==2;counts['role']+=v in [3,4];counts['BOS']+=v==1;target_original.add((r['id'],keep[j]))
   maps.append(dict(record=i,source=source,id=r['id'],new_to_original_token_position=keep,deleted_original_token_positions=sorted(set(range(len(original)))-set(keep)),deleted_body_byte_offsets=deleted_bytes,teacher_limit_new_position=limit,unit_fully_exposed=limit==len(t)-1))
   changedruns[source]+=len(original)-len(t);remaining-=limit;used+=limit
   if source=='stair':selected_images.add(raw['original_image_id'])
  assert remaining==0,(source,remaining)
  stats[source]=dict(targets=used,share=used/590144,units=len(unit_ids),families=len(components),known_speakers=len(speaker_ids),stored_body_tokens=full_body,exposed_unique_body_positions=exposed_body,counts=dict(counts),distinct_original_teacher_positions=len(target_original),IDs=unit_ids)
 # Preserve the control's per-update active-target budget; length-bucket rows, no document join.
 control_s=json.load(gzip.open(V/'lf-boundary-study/schedule-LF1.json.gz','rt'));budgets=[sum(r['length']-1 for r in b) for b in control_s];assert len(budgets)==579 and sum(budgets)==590144
 ordered=sorted(refs,key=lambda r:(r['length'],rank(units[r['record']]['id']+':'+str(r['start']))));batches=[];q=0;used_in_ref=0
 for budget in sorted(budgets,reverse=True):
  b=[];remaining=budget
  while remaining:
   ref=ordered[q];n=min(remaining,ref['length']-1-used_in_ref);b.append(dict(record=ref['record'],start=ref['start']+used_in_ref,length=n+1));remaining-=n;used_in_ref+=n
   if used_in_ref==ref['length']-1:q+=1;used_in_ref=0
  assert len(b)<=128 and max(r['length']-1 for r in b)*len(b)<=2048,('resource batch',len(b),budget)
  batches.append(b)
 assert q==len(ordered) and used_in_ref==0
 buckets=collections.defaultdict(list)
 for b in batches:buckets[sum(r['length']-1 for r in b)].append(b)
 for k in buckets:buckets[k].sort(key=lambda b:rank('|'.join(units[r['record']]['id']+':'+str(r['start']) for r in b)))
 schedule=[buckets[n].pop() for n in budgets];seen=set();hist=collections.Counter();sb=[];maxpad=0
 for b in schedule:
  count=collections.Counter();maxpad=max(maxpad,len(b)*max(r['length']-1 for r in b))
  for r in b:
   hist[str(r['length']-1)]+=1
   for j in range(r['start']+1,r['start']+r['length']):
    key=(r['record'],j);assert key not in seen;seen.add(key);count[units[r['record']]['source']]+=1
  sb.append(dict(count))
 assert len(seen)==590144
 gzwrite(P/'corpus.json.gz',units);gzwrite(P/'schedule.json.gz',schedule);gzwrite(P/'POSITION_MAP.json.gz',maps);write(P/'SOURCE_AUDIT.json',dict(source_stats=stats,total_targets=len(seen),total_units=len(units),new_acquisition_tokens=0,new_independent_original_tokens=0,LF_tokens_removed=dict(changedruns),teacher_duplicates=0,source_boundary_concatenations=0,padding_max_positions=maxpad,input_length_histogram=dict(hist),protected_DEV_records=len(protected),protected_families=len(families),known_DEV_speaker_intersection=0,STAIR_DEV_image_intersection=0,schedule_per_batch_source_targets=sb,rejection_count=len(rejections),near_duplicate_scope='64 lowest crc32 of13-char shingles, >=4 hits then verified >=85% shorter-set containment; canonical exact; not exhaustive semantic/author independence'))
 write(P/'REJECTIONS.json',rejections)
 write(P/'SAMPLING_PROTOCOL.json',dict(seed='mixed-retention-108-v1 SHA256 order',target_quotas=quotas,other_prose_total=177043,selected_only_from='PR105 admitted TRAIN and PR107 LF1 environment corpus',whole_units_except='At most final selected unit per source prefix-limited to exact target quota, no fake EOS',budget_sequence_equal_to_control=True,batching='Length sorted source windows, split teacher positions once to fill active budgets, hash-shuffle only within identical budget then map to old per-step counts',original_unit_text_order_preserved=True))
 print('selected',len(units),'units; targets',len(seen),'source totals',quotas,'rejections',len(rejections),'maxpad',maxpad,flush=True)
if __name__=='__main__':main()
