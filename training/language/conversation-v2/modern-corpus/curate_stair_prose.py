"""A separate sentence-form candidate contract. Never rewrite source captions.
Development48 examples inform these fixed rules; disjoint64 audit is not yet scored.
"""
import pathlib,json,gzip,re,hashlib,collections,os
D=pathlib.Path(__file__).resolve().parent
FINITE=r'(?:いる|ある|れる|する|なる|見える|できる|寝る|食べる|走る|座る|立つ|泳ぐ|咥える|乗る|飛ぶ|入る|飲む|歩く|置く|だ|です|ます|ました|した|った|いた|かった|ない|大きい|小さい|多い|少ない|美しい|狭い|広い|高い|低い|青い|赤い|白い|黒い)$'
KNOWN_BAD={795057:'source typo ディスクトップ',316031:'ambiguous source grammar 黒人のスーツ',777156:'source typo オーブンニ and nominal fragment',177578:'multiple severe transcription errors',786503:'anomalous 枕元 noun selection'}
def reasons(row):
 text=row['text'];out=[h for h in row['hold_reasons']if h not in {'canonical_duplicate','canonical_overlap_with_reserved_DEV'}]
 if not re.search(FINITE,text.rstrip('。．.!！?？ \t\r\n')):out.append('not_finite_sentence_proxy')
 if row['original_annotation_id']in KNOWN_BAD:out.append('known_development_sample_quality_issue')
 if re.search(r'ディスクトップ|オーブンニ',text):out.append('known_transcription_pattern')
 if re.search(r'この(?:写真|画像)|(?:写真|画像)(?:の|が|には|という)',text):out.append('unprovided_image_deixis')
 if re.search(r'「[^」]{40,}」|“[^”]{40,}”',text):out.append('long_transcription_quote_rights_hold')
 if re.search(r'(.{2,12})\1{3,}',text):out.append('source_text_repetition')
 if re.match(r'^(?:私は|僕は|俺は|わたしは)',text):out.append('author_self_attribute_not_scene_prose')
 return out

def main():
 protocol=dict(source='Original STAIR TRAIN caption strings only, byte-preserved',finite_sentence_proxy=FINITE,known_development_exclusions=KNOWN_BAD,nominal_caption_policy='Keep source in raw candidate pool but exclude from this prose-sentence component; no predicate or punctuation added',EOS_contract='Only full original finite-clause annotation units, never arbitrary windows. A caption-unit end does not prove complete document/paragraph ability.',DEV='64 pre-fixed image families, no original validation or TEST body read',review_gate=dict(disjoint_distinct_image_TRAIN_sample=64,min_natural_complete_sentences=60,max_severe_rights_privacy_or_corruption=0,reviewer='main assistant; not independent human; no source-image correctness certification',failure='No research training of this component if gate fails; report issue, do not tune rules to this audit sample'),admitted_tokens=0,optimizer_updates=0)
 pf=D/'STAIR_PROSE_CURATION_PROTOCOL.json'
 if pf.exists():assert json.loads(pf.read_text())==json.loads(json.dumps(protocol))
 else:pf.write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
 source=D/'private/stair-caption-candidates.jsonl.gz';dev_keys=set()
 for line in gzip.open(source,'rt'):
  row=json.loads(line)
  if row['split']=='dev'and not reasons(row):dev_keys.add(re.sub(r'\s+','',row['text']).casefold())
 seen={'train':set(),'dev':set()};counts=collections.Counter();pool=[];used_images={'train':set(),'dev':set()};out=D/'private/stair-prose-candidates.pending'
 with gzip.open(out,'wt')as dest:
  for line in gzip.open(source,'rt'):
   row=json.loads(line);holds=reasons(row);split=row['split'];key=re.sub(r'\s+','',row['text']).casefold()
   if split=='train'and key in dev_keys:holds.append('canonical_overlap_with_reserved_DEV')
   if key in seen[split]:holds.append('canonical_duplicate_within_split')
   for hold in holds:counts['hold_'+hold]+=1
   if holds:continue
   seen[split].add(key);used_images[split].add(row['original_image_id']);counts[split+'_records']+=1;counts[split+'_body_tokens']+=len(row['body_tokens']);counts[split+'_EOS_positions']+=1
   row.update(hold_reasons=[],admission='sentence-form candidate pending disjoint audit',EOS_approved=False,proposed_tokens=[1]+row['body_tokens']+[2]);dest.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
   if split=='train':pool.append((hashlib.sha256(('stair-prose-audit64-v1|'+row['id']).encode()).hexdigest(),row))
 os.replace(out,D/'private/stair-prose-candidates.jsonl.gz');development_images={r['image_id']for r in json.loads((D/'STAIR_QUALITY_SAMPLE.json').read_text())['records']};sample=[];seen_images=set(development_images)
 for _,row in sorted(pool,key=lambda x:x[0]):
  if row['original_image_id']in seen_images:continue
  seen_images.add(row['original_image_id']);sample.append(row)
  if len(sample)==64:break
 with gzip.open(D/'private/stair-prose-audit64.jsonl.gz','wt')as f:
  for row in sample:f.write(json.dumps(row,ensure_ascii=False)+'\n')
 (D/'STAIR_PROSE_AUDIT_SAMPLE.json').write_text(json.dumps(dict(rows=[{k:row[k]for k in ['id','original_image_id','text_sha256']}for row in sample],count=len(sample),status='frozen before reading; no model outputs',rules_sha256=hashlib.sha256(pf.read_bytes()).hexdigest()),indent=2)+'\n')
 result=dict(counts=dict(counts),unique_image_families={k:len(v)for k,v in used_images.items()},admitted_tokens=0,optimizer_updates=0,caption_style_warning='Single-sentence present-progressive visual descriptions dominate; not conversation, reasoning or paragraph corpus. Multiple descriptions per image remain correlated.',canonical_policy='Independent dedup within each split, qualified DEV strings take precedence over TRAIN')
 (D/'STAIR_PROSE_CANDIDATE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
if __name__=='__main__':main()
