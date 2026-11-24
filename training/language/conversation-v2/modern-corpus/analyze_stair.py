"""Analyze original human caption TRAIN only with own BPE. No images/external tokenizer.
Candidate accounting and fixed review set are produced before training admission.
"""
import pathlib,json,tarfile,gzip,hashlib,sys,re,collections,statistics,os,time
D=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent));from new_tokenizer import Encoder

def rank(s):return hashlib.sha256(('stair-analysis-v1|'+s).encode()).hexdigest()
def main():
 start=time.time();protocol=dict(member='stair_captions_v1.2_train.json',ignore=['images content/URLs','tokenized_caption','provided tokenized files','original validation captions'],DEV_image_families=64,DEV_selection='64 lowest SHA256 stair-analysis-v1 image IDs from originalTRAIN; all captions of each held-out image excluded from TRAIN',canonical='Whitespace removed + casefold for duplicate detection only; retained source text is never normalized',quality_sample='32 lowest hash distinct-image captions, plus16 longest distinct-image captions, frozen before model outputs',max_caption_utf8_bytes=4096,scope='Original caption annotations only, not conversations, not image-conditioned model training; candidate only',optimizer_updates=0,admitted_tokens=0)
 pf=D/'STAIR_ANALYSIS_PROTOCOL.json'
 if pf.exists():assert json.loads(pf.read_text())==protocol
 else:pf.write_text(json.dumps(protocol,indent=2)+'\n')
 path=D/'private/stair/stair_captions_v1.2.tar.gz';receipt=json.loads((D/'STAIR_ARCHIVE_RECEIPT.json').read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==receipt['sha256']
 with tarfile.open(path,'r:gz')as tar:dataset=json.load(tar.extractfile(protocol['member']))
 annotations=dataset['annotations'];del dataset['images'];images={r['image_id']for r in annotations};dev_images=set(sorted(images,key=lambda n:rank(str(n)))[:64]);ids=set();canonical={};counts=collections.Counter();lengths=[];suffix=collections.Counter();sample=[];longest=[];enc=Encoder(json.loads((D.parent/'data/tokenizer.json').read_text()));pieces=[bytes.fromhex(s)for s in enc.tok['bytes']]
 # Reserve every canonical string occurring in a DEV family before TRAIN deduplication.
 dev_canonical={re.sub(r'\s+','',r['caption']).casefold()for r in annotations if r['image_id']in dev_images}
 out=D/'private/stair-caption-candidates.pending';unique_images=set();review_pool=[]
 with gzip.open(out,'wt')as f:
  for r in annotations:
   assert r['id']not in ids;ids.add(r['id']);text=r['caption'];assert isinstance(text,str);raw=text.encode('utf-8');holds=[]
   if not text.strip():holds.append('empty')
   if len(raw)>4096:holds.append('oversize_no_truncation')
   if '\ufffd'in text:holds.append('replacement_character')
   if not re.search(r'[ぁ-ゖァ-ヺ]',text):holds.append('no_kana_language_review')
   if re.search(r'https?://|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)0\d{1,3}[-ー]\d{2,4}[-ー]\d{3,4}(?!\d)',text):holds.append('contact_or_link')
   key=re.sub(r'\s+','',text).casefold();split='dev'if r['image_id']in dev_images else'train'
   if split=='train'and key in dev_canonical:holds.append('canonical_overlap_with_reserved_DEV')
   if key in canonical:holds.append('canonical_duplicate')
   else:canonical[key]=r['id']
   tokens=enc(text);assert b''.join(pieces[t]for t in tokens)==raw;assert all(t>=6 for t in tokens);counts['raw_body_tokens']+=len(tokens);counts['raw_characters']+=len(text);lengths.append(len(tokens))
   if len(tokens)>255:holds.append('over_context256_hold_no_fake_EOS')
   counts['base_byte_tokens']+=sum(t<262 for t in tokens);suffix[text.rstrip('。．.!！?？ ')[-4:]]+=1
   row=dict(id='stair:'+str(r['id']),image_family='stair-image:'+str(r['image_id']),original_annotation_id=r['id'],original_image_id=r['image_id'],split=split,text=text,body_tokens=tokens,text_sha256=hashlib.sha256(raw).hexdigest(),hold_reasons=holds,source='STAIR captions1.2 originalTRAIN',source_archive_sha256=receipt['sha256'],EOS_approved=False,admission='quarantined candidate')
   f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
   for hold in holds:counts['hold_'+hold]+=1
   if not holds:
    counts[split+'_mechanical_candidate_records']+=1;counts[split+'_mechanical_candidate_body_tokens']+=len(tokens);unique_images.add(r['image_id'])
   review_pool.append((rank(str(r['id'])),len(text),r['image_id'],r['id'],text,row['text_sha256'],split))
   if len(ids)%50000==0:print('STAIR processed',len(ids),'tokens',counts['raw_body_tokens'],flush=True)
 os.replace(out,D/'private/stair-caption-candidates.jsonl.gz')
 chosen=[];seen_images=set()
 for pool,n in [(sorted(review_pool),32),(sorted(review_pool,key=lambda x:(-x[1],x[0])),16)]:
  added=0
  for r in pool:
   if r[2]in seen_images:continue
   chosen.append(dict(annotation_id=r[3],image_id=r[2],text=r[4],sha256=r[5],split=r[6],characters=r[1]));seen_images.add(r[2]);added+=1
   if added==n:break
 with gzip.open(D/'private/stair-quality-sample.jsonl.gz','wt')as f:
  for r in chosen:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 (D/'STAIR_QUALITY_SAMPLE.json').write_text(json.dumps(dict(selection=protocol['quality_sample'],records=[{k:v for k,v in r.items()if k!='text'}for r in chosen],sample_size=len(chosen),status='not yet read; source body private'),indent=2)+'\n')
 result=dict(original_TRAIN_captions=len(annotations),original_TRAIN_image_families=len(images),reserved_DEV_image_families=len(dev_images),canonical_unique_strings=len(canonical),mechanical_candidate_image_families=len(unique_images),counts=dict(counts),token_length=dict(min=min(lengths),median=statistics.median(lengths),p95=sorted(lengths)[int(len(lengths)*.95)],max=max(lengths)),top_suffixes=suffix.most_common(15),all_caption_byte_roundtrip=True,source_info=dataset['info'],seconds=time.time()-start,admitted_tokens=0,optimizer_updates=0,limitations='Image families are not author IDs. About2100 workers is the paper report for full dataset, not independently counted TRAIN authors. Multiple captions per image are correlated, not independent scenes. Caption Japanese differs from conversation/paragraph explanations. No images, tokenized files, original validation or TEST body used.')
 (D/'STAIR_TOKEN_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result,flush=True)
if __name__=='__main__':main()
