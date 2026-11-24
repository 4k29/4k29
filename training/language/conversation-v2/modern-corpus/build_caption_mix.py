"""Build byte-preserved finite corpus and source-balanced one-pass batch schedule.
All output compression is deterministic; no model output is used for selection.
"""
import pathlib,json,gzip,hashlib,collections,math,os
N=pathlib.Path(__file__).resolve().parent;D=N/'next-foundation';D.mkdir(exist_ok=True);OLD=N.parent/'diverse-foundation'
def rank(s):return hashlib.sha256(('caption-mix-v1|'+s).encode()).hexdigest()
def dump_gz(path,rows,lines=False):
 with path.open('wb')as raw:
  with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='')as z:
   if lines:
    for row in rows:z.write((json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n').encode())
   else:z.write((json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n').encode())
def main():
 policy=dict(caption_body_cap=3000000,realpersona_body_cap=1000000,reused_prose='All previously admitted PR104 TRAIN prose, preserve original EOS/noEOS and UTF8',caption_selection='One caption per eligible image family before second/third views; hash-ranked image and caption order; whole units only, no repetition or truncation',caption_use='Human original scene sentences, not conversation, image understanding or assistant answers',max_valid_targets_per_update=1024,max_rows=128,max_padded_positions=2048,batching='Within each source group sort by length for efficient independent-row padding, then hash-shuffle batches. Interleave groups by smallest consumed fraction of their fixed one-pass target total.',comparison_minimum_targets=2000000,midpoint_minimum_targets=4000000,unit_window_stride=256,EOS='Only original source-approved unit/turn ends; no arbitrary window EOS',optimizer_updates=0)
 pf=D/'MIX_POLICY.json'
 if pf.exists():assert json.loads(pf.read_text())==policy
 else:pf.write_text(json.dumps(policy,ensure_ascii=False,indent=2)+'\n')
 assert json.loads((N/'STAIR_PROSE_AUDIT_REVIEW.json').read_text())['research_component_quality_gate_pass'];audit=json.loads((N/'STAIR_SPLIT_AUDIT.json').read_text());held={r['id']for r in audit['held']};groups=collections.defaultdict(list)
 for line in gzip.open(N/'private/stair-prose-candidates.jsonl.gz','rt'):
  row=json.loads(line)
  if row['split']!='train'or row['id']in held:continue
  groups[row['original_image_id']].append(dict(id=row['id'],source='stair',family=row['image_family'],text=row['text'],tokens=[1]+row['body_tokens']+[2],body_token_count=len(row['body_tokens']),kind='human_caption_sentence',source_text_sha256=row['text_sha256'],original_annotation_id=row['original_annotation_id'],original_image_id=row['original_image_id'],provenance_ref='STAIR_LICENSE_RECEIPT.json + STAIR_ARCHIVE_RECEIPT.json',license='CC-BY-4.0',boundary_contract='Whole original finite-clause caption annotation; no punctuation/word repair; caption end is not proof of a complete paragraph',EOS=True,speaker_ids=[]))
 image_order=sorted(groups,key=lambda n:rank(str(n)))
 for rows in groups.values():rows.sort(key=lambda r:rank(r['id']))
 selected=[];body=0
 for view in range(max(map(len,groups.values()))):
  for image in image_order:
   rows=groups[image]
   if view>=len(rows):continue
   row=rows[view]
   if body+row['body_token_count']>policy['caption_body_cap']:continue
   selected.append(row);body+=row['body_token_count']
 del groups
 prior=[json.loads(line)for line in gzip.open(OLD/'corpus.jsonl.gz','rt')if json.loads(line)['split']=='train'];rp=[]
 for r in prior:
  if r['source']=='realpersona':rp.append(r);continue
  selected.append({**r,'body_token_count':len(r['body_tokens']),'reuse':'PR104 previously admitted prose; not new acquisition'})
 total=0
 for r in sorted(rp,key=lambda r:rank(r['id'])):
  size=len(r['body_tokens'])
  if total+size>policy['realpersona_body_cap']:continue
  selected.append({**r,'body_token_count':size,'reuse':'Original RP TRAIN from PR104; human A/B roles unchanged, not assistant identity'});total+=size
 # Strip duplicated raw token list for storage; tokens remain exact original full contract.
 for r in selected:r.pop('body_tokens',None)
 selected.sort(key=lambda r:r['id']);assert len({r['id']for r in selected})==len(selected)
 pools=collections.defaultdict(list);counts=collections.Counter();source_units=collections.Counter();speaker_ids=set();families=collections.defaultdict(set)
 for idx,row in enumerate(selected):
  t=row['tokens'];assert (t[0]==1)==bool(row.get('BOS',True)) and 1 not in t[1:]and 0 not in t and 5 not in t;counts['context_only_first_body_positions']+=t[0]>=6;assert row['body_token_count']==sum(v>=6 for v in t);source=row['source'];group='stair'if source=='stair'else'realpersona'if source=='realpersona'else'prose';source_units[source]+=1;families[source].add(row['family']);speaker_ids.update(row.get('speaker_ids',[]));counts[source+'_body_tokens']+=row['body_token_count']
  if source=='jaquad':assert 2 not in t,'No document EOS for excerpts'
  for start in range(0,len(t)-1,256):
   w=t[start:start+257];ref=dict(record=idx,start=start,length=len(w));pools[group].append(ref);counts[source+'_targets']+=len(w)-1;counts['all_targets']+=len(w)-1;counts['EOS_targets']+=w[1:].count(2);counts['role_targets']+=w[1:].count(3)+w[1:].count(4)
 batches_by_group={};group_totals={}
 for group,refs in pools.items():
  refs.sort(key=lambda r:(r['length'],rank(selected[r['record']]['id']+':'+str(r['start']))));batches=[];current=[];valid=0;width=0
  for ref in refs:
   v=ref['length']-1;new_width=max(width,v)
   if current and(valid+v>1024 or len(current)+1>128 or new_width*(len(current)+1)>2048):batches.append(current);current=[];valid=0;width=0
   current.append(ref);valid+=v;width=max(width,v)
  if current:batches.append(current)
  batches.sort(key=lambda b:rank(group+'|'+str(b[0]['record'])+'|'+str(b[0]['start'])));batches_by_group[group]=batches;group_totals[group]=sum(r['length']-1 for b in batches for r in b)
 cursors={g:0 for g in pools};consumed={g:0 for g in pools};batches=[];running=0;boundaries={}
 while any(cursors[g]<len(batches_by_group[g])for g in pools):
  group=min((g for g in pools if cursors[g]<len(batches_by_group[g])),key=lambda g:(consumed[g]/group_totals[g],g));batch=batches_by_group[group][cursors[group]];cursors[group]+=1;n=sum(r['length']-1 for r in batch);consumed[group]+=n;running+=n;batches.append(batch)
  for key,minimum in [('comparison',2000000),('midpoint',4000000)]:
   if running>=minimum and key not in boundaries:boundaries[key]=dict(updates=len(batches),targets=running)
 assert running==counts['all_targets'];dump_gz(D/'corpus.jsonl.gz',selected,True);dump_gz(D/'schedule.json.gz',dict(batches=batches,group_totals=group_totals,boundaries=boundaries,targets=running))
 result=dict(selected_units=len(selected),source_units=dict(source_units),source_families={s:len(v)for s,v in families.items()},RP_anonymous_speaker_ids=len(speaker_ids),counts=dict(counts),new_caption_selected_body_tokens=body,reused_RP_selected_body_tokens=total,full_pass_updates=len(batches),full_pass_targets=running,boundaries=boundaries,corpus_sha256=hashlib.sha256((D/'corpus.jsonl.gz').read_bytes()).hexdigest(),schedule_sha256=hashlib.sha256((D/'schedule.json.gz').read_bytes()).hexdigest(),duplicated_teacher_positions=0,caption_pool_not_all_processed=audit['counts']['remaining_TRAIN_body_tokens'],body_tokens_not_processed_targets=True,optimizer_updates=0)
 (D/'DATASET_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result,flush=True)
if __name__=='__main__':main()
