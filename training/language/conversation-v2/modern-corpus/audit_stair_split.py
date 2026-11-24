"""Protect fixed image-family DEV and prior admitted DEV before research admission.
Containment matches are conservatively held, not asserted to be semantic leakage.
"""
import pathlib,json,gzip,re,zlib,collections,time
D=pathlib.Path(__file__).resolve().parent

def canon(s):return re.sub(r'\s+','',s).casefold()
def grams(s):return {zlib.crc32(s[i:i+13].encode())for i in range(max(0,len(s)-12))}
def build_index(rows):
 index=collections.defaultdict(list);sets=[]
 for i,r in enumerate(rows):
  ss=grams(canon(r['text']));sets.append(ss)
  for h in ss:index[h].append(i)
 return index,sets

def match(ss,index,sets):
 hits=collections.Counter(j for h in ss for j in index.get(h,[]));out=[]
 for j,n in hits.items():
  other=sets[j]
  if not ss or not other or n<min(4,len(ss),len(other)):continue
  if n/min(len(ss),len(other))>=.85:out.append(j)
 return out

def main():
 start=time.time();gate=json.loads((D/'STAIR_PROSE_AUDIT_REVIEW.json').read_text());assert gate['research_component_quality_gate_pass'];known=set(gate['known_held_annotation_ids']);source=D/'private/stair-prose-candidates.jsonl.gz';dev=[];dev_images=set()
 for line in gzip.open(source,'rt'):
  r=json.loads(line)
  if r['split']=='dev':dev.append(r);dev_images.add(r['original_image_id'])
 di,ds=build_index(dev);legacy_dev=[];legacy_exact=set();old=D.parent/'diverse-foundation/corpus.jsonl.gz'
 for line in gzip.open(old,'rt'):
  r=json.loads(line)
  if r['split']not in {'train','dev'}:continue
  legacy_exact.add(canon(r['text']))
  for u in r.get('utterances',[]):legacy_exact.add(canon(u['text']))
  if r['split']=='dev':legacy_dev.append(r)
 new_prose=json.loads((D/'private/new-prose-dev.json').read_text());legacy_dev.extend(dict(id=r['id'],text=r['text'])for r in new_prose)
 li,ls=build_index(legacy_dev);held=[];counts=collections.Counter();images=set();sha=set()
 for line in gzip.open(source,'rt'):
  r=json.loads(line)
  if r['split']!='train':continue
  assert r['original_image_id']not in dev_images;assert r['text_sha256']not in sha;sha.add(r['text_sha256']);why=[]
  if r['id']in known:why.append('known_audit_quality_hold')
  text=canon(r['text']);ss=grams(text)
  if text in legacy_exact:why.append('exact_prior_train_or_dev_string')
  near_dev=match(ss,di,ds);near_old=match(ss,li,ls)
  if near_dev:why.append('near_caption_DEV_containment_screen')
  if near_old:why.append('near_prior_DEV_containment_screen')
  if why:held.append(dict(id=r['id'],reasons=why,near_caption_DEV_ids=[dev[j]['id']for j in near_dev],near_prior_DEV_ids=[legacy_dev[j]['id']for j in near_old]));counts.update(why)
  else:counts['remaining_TRAIN_records']+=1;counts['remaining_TRAIN_body_tokens']+=len(r['body_tokens']);images.add(r['original_image_id'])
 result=dict(fixed_caption_DEV_records=len(dev),fixed_caption_DEV_images=len(dev_images),prior_DEV_sections=len(legacy_dev),held_TRAIN_records=len(held),counts=dict(counts),remaining_TRAIN_images=len(images),known_image_family_intersection=0,seconds=time.time()-start,held=held,admitted_tokens=0,optimizer_updates=0,scope='13-character CRC32 full-shingle >=85% shorter-set containment against fixed DEV, plus exact canonical prior TRAIN/DEV strings. Shared generic caption syntax may be held unnecessarily. Not exhaustive semantic duplicate detection, image similarity, or author independence. Includes12 newly frozen MAFF proseDEV documents. No TEST opened.')
 (D/'STAIR_SPLIT_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items()if k!='held'},flush=True)
if __name__=='__main__':main()
