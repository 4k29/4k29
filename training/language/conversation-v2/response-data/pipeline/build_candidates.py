"""Prepare real-source reply candidates, not semantic acceptance or training."""
import collections,gzip,hashlib,importlib.util,json,pathlib,re
HERE=pathlib.Path(__file__).resolve().parents[1];V2=HERE.parent

def sha(b):return hashlib.sha256(b).hexdigest()
def write_gz(path,rows):
 with path.open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for row in rows:z.write((json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode())
def encoder():
 spec=importlib.util.spec_from_file_location('response_own_bpe',V2/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 tok=json.loads((V2/'data/tokenizer.json').read_text());return m.Encoder(tok),tok

def serialize(turns,encode):
 stream=[1];bounds=[]
 for i,u in enumerate(turns):
  if u['source_role']not in ('prompter','assistant'):raise ValueError('Unknown source semantic role')
  if (i==0 and u['source_role']!='prompter')or(i and u['parent_id']!=turns[i-1]['id']):raise ValueError('Missing complete source ancestry')
  if i and u['source_role']==turns[i-1]['source_role']:raise ValueError('Not a source role-alternating chain')
  ids=list(encode(u['text']))
  if not ids or any(x<6 for x in ids):raise ValueError('Invalid body token')
  stream +=[3 if u['source_role']=='prompter'else 4]+ids+[2]
  bounds.append({'source_id':u['id'],'eos_offset':len(stream)-1})
 return stream,bounds

def extract_oasst(docs,encode,tok):
 found={};vocab=[bytes.fromhex(x)for x in tok['bytes']]
 for d in docs:
  assert d['split']=='TRAIN'
  for i,u in enumerate(d['utterances']):
   if u['source_role']!='assistant':continue
   turns=d['utterances'][:i+1];stream,bounds=serialize(turns,encode)
   for t in turns:assert b''.join(vocab[x]for x in encode(t['text']))==t['text'].encode()
   assert u['parent_id']==turns[-2]['id']
   ids=list(encode(u['text']));prefix=stream[:-len(ids)-1]
   assert prefix[-1]==4
   row={'id':u['id'],'source':'oasst2','family':d['conversation_family'],'component':d['component'],'partition':'TRAIN-candidate','rights_status':'Apache-2.0-source; record-quality-and-privacy-pending','admitted_for_training':False,'source_url':d['source_url'],'source_sha256':d['source_sha256'],'license':d['license'],'history':[{'id':x['id'],'parent_id':x['parent_id'],'speaker_id':x['speaker_id'],'source_role':x['source_role'],'text':x['text']}for x in turns[:-1]],'response':{'id':u['id'],'parent_id':u['parent_id'],'speaker_id':u['speaker_id'],'source_role':u['source_role'],'text':u['text'],'source_quality_labels':u['quality_flags'].get('source_labels_review',{})},'source_authors':sorted({x['speaker_id']for x in turns}),'token_audit':{'generation_prefix_tokens':len(prefix),'response_body_tokens':len(ids),'full_serialized_tokens':len(stream),'full_ancestry_and_response_fit_context256':len(stream)<=257,'generation_prefix_fit_context192':len(prefix)<=192,'eos_only_true_source_turn_boundaries':True,'byte_roundtrip':True},'prefix_ids':prefix,'response_ids':ids,'serialized_ids':stream,'boundaries':bounds}
   if u['id']in found:assert found[u['id']]==row
   found[u['id']]=row
 return sorted(found.values(),key=lambda d:sha(('response-oasst-candidates-v1|'+d['id']).encode()))

def inventory():
 records=[]
 for name,partition in [('train.docs.jsonl','TRAIN'),('dev.docs.jsonl','existing-DEV-not-training')]:
  path=V2/'data'/name;docs=[json.loads(l)for l in path.open()];c=collections.Counter()
  for d in docs:
   us=d['utterances'];c['utterances']+=len(us)
   for a,b in zip(us,us[1:]):
    if a['speakerId']!=b['speakerId']:
     c['adjacent_different_speaker_pairs']+=1
     c['question_mark_then_next_turn_proxy']+=bool(re.search(r'[?？]',a['text']))
  records.append({'source':'RealPersona-existing','partition':partition,'documents':len(docs),'counts':dict(c),'path':str(path.relative_to(V2)),'sha256':sha(path.read_bytes()),'meaning':'chronological different-speaker adjacency; question-mark proxy is not verified semantic answer','source_license':'CC-BY-SA-4.0','newly_acquired':False})
 jp=V2.parent/'round46/added-human-source/documents.jsonl';jdocs=[json.loads(l)for l in jp.open()]
 assert all(d['upstreamPartition']=='train'for d in jdocs)
 records.append({'source':'JMRD-existing-prepared-TRAIN','documents':len(jdocs),'utterances':sum(d['utteranceCount']for d in jdocs),'path':str(jp),'sha256':sha(jp.read_bytes()),'newly_acquired':False,'source_license':'CC-BY-SA-4.0','role_export':'HOLD: joined-text prepared artifact lacks original per-turn speaker metadata; do not invent alternating roles','quality_hold':'movie plots may include third-party excerpts and need fact/rights review; knowledge/reviews/questionnaires not targets','speaker_independence':'not established'})
 mp=V2/'sns-data/derived/metrics.json';m=json.loads(mp.read_text())
 records.append({'source':'MRMPC-existing-public-candidate','documents':m['dialogues'],'utterances':m['utterances'],'body_tokens':m['body_tokens'],'newly_acquired':False,'source_license':'CC-BY-SA-4.0','role_export':'HOLD all three-party; current two-role input contract cannot represent; parent_id unknown, addressee not parent','source_metrics_sha256':sha(mp.read_bytes())})
 return records

def main():
 src=V2/'sns-data/derived/oasst-conversations.jsonl.gz';docs=[json.loads(l)for l in gzip.open(src,'rt')];enc,tok=encoder();rows=extract_oasst(docs,enc,tok)
 out=HERE/'derived/oasst-response-candidate-metadata.jsonl.gz'
 metadata=[{k:v for k,v in r.items()if k not in ('history','response','prefix_ids','response_ids','serialized_ids','boundaries')}|{'history_ids':[u['id']for u in r['history']],'response_text_sha256':sha(r['response']['text'].encode()),'history_text_sha256':sha(json.dumps(r['history'],ensure_ascii=False,sort_keys=True).encode()),'publication':'metadata-only; full census text temporary, only quality accepted ancestry-safe text may be newly published'}for r in rows]
 write_gz(out,metadata)
 metrics={'source':'oasst2-existing-public-safe-PR95','source_sha256':sha(src.read_bytes()),'candidate_archive_sha256':sha(out.read_bytes()),'unique_response_ids':len(rows),'unique_families':len({r['family']for r in rows}),'unique_authors':len({s for r in rows for s in r['source_authors']}),'full_context256_fit':sum(r['token_audit']['full_ancestry_and_response_fit_context256']for r in rows),'generation_prefix192_fit':sum(r['token_audit']['generation_prefix_fit_context192']for r in rows),'unique_response_body_tokens':sum(len(r['response_ids'])for r in rows),'serialized_tokens_including_repeated_ancestry':sum(len(r['serialized_ids'])for r in rows),'tokenizer_sha256':sha((V2/'data/tokenizer.json').read_bytes()),'actual_optimizer_updates':0,'training_admitted':0,'content_semantics':'not determined by regex; quality reviewer must adjudicate complete prefix and response','census_text_persisted_in_repository':False,'no_new_independent_original_acquisition':True,'sealed_test_opened':False}
 (HERE/'derived/oasst-candidate-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
 (HERE/'audit/existing-source-inventory.json').write_text(json.dumps(inventory(),ensure_ascii=False,indent=2)+'\n')
 temp=pathlib.Path('/dev/shm/response-oasst-candidates.jsonl');temp.write_text(''.join(json.dumps({k:v for k,v in r.items()if k not in ('prefix_ids','response_ids','serialized_ids','boundaries')},ensure_ascii=False)+'\n'for r in rows))
 print(json.dumps(metrics,ensure_ascii=False))
if __name__=='__main__':main()
