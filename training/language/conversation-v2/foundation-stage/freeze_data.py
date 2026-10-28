"""Freeze actual one-pass windows, provenance and evaluation before any update."""
import collections,gzip,hashlib,importlib.util,json,pathlib,re
H=pathlib.Path(__file__).resolve().parent;V=H.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rank(s):return hashlib.sha256(('final-foundation-v1|'+s).encode()).hexdigest()
def main():
 validation=json.loads((H/'quality-validation.json').read_text());held={validation[i]['id']for i in [1,9,11]}
 (H/'QUALITY_VALIDATION_REVIEW.json').write_text(json.dumps(dict(reviewer='main assistant, not independent native-human',all12_source_units_read=True,held_indices=[1,9,11],reasons={'1':'脱字: 構成されるも','9':'リトルロックの位置の疑義と不自然な語','11':'京都/幡生の東西を逆に記述'},remaining='9/12 conditional modern prose, not complete fact verification. School physics omits pressure conditions; low-density food introduction remains a limitation.'),ensure_ascii=False,indent=2)+'\n')
 rows=[];removed=collections.Counter()
 for l in gzip.open(H/'admitted.jsonl.gz','rt'):
  r=json.loads(l)
  if r['id']in held:removed['postfilter_sample_issue']+=1;continue
  if r['family']=='jawikibooks|中学校社会 歴史':removed['historical_editorial_scope']+=1;continue
  rows.append(r)
 with (H/'data.jsonl.gz').open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for r in rows:z.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 train=[];dev=[]
 for r in rows:
  seq=r['tokens'];assert set(seq)<=set(range(3997))and not(set(seq)&{0,3,4,5})
  assert (1 in seq)==r['true_processed_page_start']and(2 in seq)==r['true_processed_page_end']
  for start in range(0,len(seq)-1,256):
   ids=seq[start:start+257]
   if len(ids)<2:continue
   w=dict(id=r['id']+':'+str(start),unit_id=r['id'],offset=start,tokens=ids)
   (train if r['split']=='train'else dev).append(w)
 assert len({r['id']for r in train})==len(train)
 batches=[train[i:i+4]for i in range(0,len(train),4)]
 schedule=dict(batches=batches,dev=dev,targets=sum(len(r['tokens'])-1 for r in train),updates=len(batches),epochs=1,repeated_target_positions=0)
 with (H/'schedule.json.gz').open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:z.write(json.dumps(schedule,separators=(',',':')).encode())
 # One source component per article, two within-article prompts. Not 24 independent documents.
 chosen={}
 for r in sorted([r for r in rows if r['split']=='dev'],key=lambda r:rank(r['id'])):
  if len(r['text'])>=90:chosen.setdefault(r['component'],r)
 spec=importlib.util.spec_from_file_location('bpe',V/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);tok=json.loads((V/'data/tokenizer.json').read_text());enc=m.Encoder(tok);pieces=[bytes.fromhex(b)for b in tok['bytes']];cases=[]
 for r in list(chosen.values())[:12]:
  for chars in [30,60]:
   prefix=([1]if r['true_processed_page_start']else[])+enc(r['text'][:chars]);assert len(prefix)+128<=256
   cases.append(dict(id=r['id']+':prefix'+str(chars),unit_id=r['id'],component=r['component'],source=r['source'],title=r['title'],prefix_text=r['text'][:chars],prefix=prefix,source_remainder=r['text'][chars:],generation=dict(mode='greedy-full-vocabulary',max_new_tokens=128,no_repair=True)))
 (H/'prose-dev.json').write_text(json.dumps(dict(scope='exposed exploratory DEV, source components disjoint from TRAIN; two correlated prompts/article, no author/full-semantic independence proof',cases=cases),ensure_ascii=False,indent=2)+'\n')
 tr=[r for r in rows if r['split']=='train'];de=[r for r in rows if r['split']=='dev'];unknown=collections.Counter();glyphs=tok['glyphTokenIds']
 for r in tr:
  for c in r['text']:
   if ord(c)>127 and c not in glyphs:unknown[c]+=1
  body=r['tokens'][int(r['true_processed_page_start']):len(r['tokens'])-int(r['true_processed_page_end'])]
  assert b''.join(pieces[i]for i in body).decode()==r['text']
 audit=dict(train_units=len(tr),train_documents=len({r['provenance']['id']for r in tr}),train_families=len({r['component']for r in tr}),train_independent_body_tokens=sum(r['body_tokens']for r in tr),train_characters=sum(len(r['text'])for r in tr),actual_scheduled_targets=schedule['targets'],actual_scheduled_updates=schedule['updates'],source_body_tokens={s:sum(r['body_tokens']for r in tr if r['source']==s)for s in ['jaquad','jawikibooks','jawikivoyage']},dev_body_tokens=sum(r['body_tokens']for r in de),dev_units=len(de),prose_prompt_count=len(cases),prose_independent_source_components=len({r['component']for r in cases}),unknown_nonASCII_glyph_occurrences=sum(unknown.values()),unknown_nonASCII_glyph_types=len(unknown),byte_roundtrip_all_train_units=True,units_over_context256=sum(len(r['tokens'])>257 for r in tr),units_over512=sum(len(r['tokens'])>513 for r in tr),units_over1024=sum(len(r['tokens'])>1025 for r in tr),true_page_BOS=sum(r['true_processed_page_start']for r in tr),true_page_EOS=sum(r['true_processed_page_end']for r in tr),no_fake_boundary_at_window_edges=True,JA_excerpt_BOS_EOS_insertions=0,full_contributor_independence_unproven=True,known_last_editor_overlap=0,old_split_preserved=True,final_removals=dict(removed),data_sha256=sha(H/'data.jsonl.gz'),schedule_sha256=sha(H/'schedule.json.gz'),prose_dev_sha256=sha(H/'prose-dev.json'))
 assert not {r['component']for r in tr}&{r['component']for r in de}
 (H/'DATA_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps(audit,ensure_ascii=False))
if __name__=='__main__':main()
