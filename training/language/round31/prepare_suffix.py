"""One TRAIN-only transformation. Never loads DEV/TEST texts or policy references."""
import array,collections,hashlib,json,pathlib,random,sys
import numpy as np
R=pathlib.Path(__file__).resolve().parent;C=R.parent/'round25';E=R/'execution';sys.path.insert(0,str(R.parent/'round10'));from word_bpe import apply_rules
sys.path.insert(0,str(R.parents[1]/'dialogue'));from tokenizer import encode_stream
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=lambda b:hashlib.sha256(b).hexdigest();write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (E/'suffix-transformation.json').exists(),'Do not transform twice'
policy=read(R/'dedup-policy.json');old=read(C/'multiview/train.index.json');values=np.memmap(C/'multiview/train.tokens.bin',dtype='<u4',mode='r');tok=read(C/'multiview/tokenizer.json');vocab=[bytes.fromhex(x) for x in tok['bytes']];canonical={};last={};sources=collections.defaultdict(set)
for d in old['documents']:
 if d['variant']!=0:continue
 raw=b''.join(vocab[int(t)] for t in values[d['offset']:d['offset']+d['length']]);assert digest(raw)==d['textSha256'];text=raw.decode();canonical[d['id']]=(d,text)
 sid=d['sourceDocument']
 if sid not in last or d['endLine']>last[sid]['endLine']:last[sid]=d
 for line in text.splitlines():
  if len(line)>=policy['minimumUnicodeCharacters']:sources[line].add(sid)
keepers={line:min(ids,key=lambda x:digest(x.encode())) for line,ids in sources.items() if len(ids)>=policy['minimumDistinctSourceDocuments']};changes={};removed=[]
for sid,d in last.items():
 text=canonical[d['id']][1];lines=text.splitlines(keepends=True);end=len(lines)
 while end:
  key=lines[end-1].rstrip('\r\n')
  if not key.strip():end-=1;continue
  if key in keepers and keepers[key]!=sid:end-=1
  else:break
 new=''.join(lines[:end])
 # Keep original whitespace if no substantive line removed.
 if not any(x.rstrip('\r\n').strip() for x in lines[end:]):continue
 assert text.startswith(new)
 changes[d['id']]=new;removed.append(dict(id=d['id'],sourceDocument=sid,site=d['site'],beforeSha256=digest(text.encode()),afterSha256=digest(new.encode()),removedUtf8Bytes=len(text[len(new):].encode()),removedLines=lines[end:],emptyUnitDropped=not new.strip()))
glyph=read(R.parent/'round10/unicode-bpe-4681/tokenizer.json');rules=tok['merges'][len(glyph['merges']):];charids={x['character']:x['token'] for x in read(R.parent/'round10/character-frequencies.json')};cache={}
def glyph_encode(text):
 out=[]
 for ch in text:
  if ch in charids:out.append(charids[ch])
  else:
   if ch not in cache:cache[ch]=encode_stream(ch,glyph)
   out.extend(cache[ch])
 return out
newvalues=array.array('I');rows=[];docs=[];unchanged=0;changed=0;dropped=0
byunit=collections.defaultdict(list)
for row in old['rows']:byunit[row['unit']].append(row)
for d0 in old['documents']:
 d=dict(d0);key=d['id'].rsplit(':view:',1)[0]+':view:0';offset=len(newvalues)
 if key not in changes:
  full=list(map(int,values[d['offset']:d['offset']+d['length']]));newvalues.extend(full)
  for orig in byunit[d['id']]:row=dict(orig);row['offset']=offset+row['start'];rows.append(row)
  d['offset']=offset;docs.append(d);unchanged+=1;continue
 text=changes[key]
 if not text.strip():dropped+=1;continue
 g=glyph_encode(text);variant=d['variant'];cuts=[]
 if variant==0:encoded=apply_rules(g,rules)
 elif variant==1:encoded=g
 else:
  rng=random.Random(int(digest(('2049|'+d['sourceDocument']+'|'+str(d['startLine'])).encode()),16));encoded=[];start=0
  while start<len(text):
   end=min(len(text),start+rng.randint(8,24));encoded.extend(apply_rules(glyph_encode(text[start:end]),rules));cuts.append(end);start=end
 assert b''.join(vocab[t] for t in encoded)==text.encode()
 full=[1]+encoded+[2];newvalues.extend(full);start=0;covered=[]
 while start<len(full)-1:
  end=min(start+257,len(full));prefix=1 if start==0 else 32
  rows.append(dict(document=d['sourceDocument'],unit=d['id'],site=d['site'],variant=variant,offset=offset+start,length=end-start,prefixLength=prefix,start=start,end=end));covered.extend(full[start+prefix:end])
  if end==len(full):break
  start=end-32
 assert covered==full[1:]
 d.update(offset=offset,length=len(full),characters=len(text),utf8Bytes=len(text.encode()),textSha256=digest(text.encode()),characterCuts=cuts);docs.append(d);changed+=1
if sys.byteorder!='little':newvalues.byteswap()
f=R/'multiview/train.tokens.bin';f.write_bytes(newvalues.tobytes());write(R/'multiview/train.index.json',dict(rows=rows,documents=docs,tokensSha256=sha(f)))
meta=read(C/'multiview/data.json');meta['stats']['train']={str(v):dict(units=sum(d['variant']==v for d in docs),windows=sum(x['variant']==v for x in rows),targetTokens=sum(d['length']-1 for d in docs if d['variant']==v),utf8Bytes=sum(d['utf8Bytes'] for d in docs if d['variant']==v)) for v in range(3)};meta['trainingTransformationPolicySha256']=sha(R/'dedup-policy.json');meta['originalPreparedDataSha256']=sha(C/'multiview/data.json');write(R/'multiview/data.json',meta)
write(E/'suffix-transformation.json',dict(actualOptimizerUpdates=0,trainOnly=True,canonicalUnitsAudited=len(canonical),candidateCommonLines=len(keepers),changedCanonicalUnits=len(changes),changedViewUnits=changed,droppedViewUnits=dropped,unchangedViewUnitsCopiedExactly=unchanged,removedUtf8Bytes=sum(x['removedUtf8Bytes'] for x in removed),originalTrainBytes=read(C/'multiview/data.json')['stats']['train']['0']['utf8Bytes'],newTrainBytes=meta['stats']['train']['0']['utf8Bytes'],changes=removed,originalTrainIndexSha256=sha(C/'multiview/train.index.json'),newTrainIndexSha256=sha(R/'multiview/train.index.json'),dedupPolicySha256=sha(R/'dedup-policy.json'),noInternalLineStitching=True,noPositiveGeneratedTargets=True))
print(json.dumps({k:v for k,v in read(E/'suffix-transformation.json').items() if k!='changes'}))
