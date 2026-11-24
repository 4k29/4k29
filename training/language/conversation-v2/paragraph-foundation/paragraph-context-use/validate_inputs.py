"""No model: independently bind paired inputs to frozen original TRAIN positions."""
import json,gzip,pathlib,hashlib
from metrics import sha,input_hash
D=pathlib.Path(__file__).resolve().parent;B=D.parent;ROOT=B.parents[3]
def validate():
 pairs=json.loads((D/'INPUT_PAIRS.json').read_text());proto=json.loads((D/'PROTOCOL.json').read_text());review=json.loads((D/'PAIR_REVIEW.json').read_text())
 assert review['input_pairs_sha256']==sha(D/'INPUT_PAIRS.json')and all(r['accepted']for r in review['decisions'])
 for rel,h in proto['source_sha256'].items():assert sha(ROOT/rel)==h
 pieces=[bytes.fromhex(s)for s in json.loads((B.parent/'data/tokenizer.json').read_text())['bytes']]
 need={r[k]['record']for r in pairs for k in ['correct','unrelated']}
 corpus={i:json.loads(line)for i,line in enumerate(gzip.open(B/'corpus.jsonl.gz','rt'))if i in need}
 schedule=json.load(gzip.open(B/'schedule.json.gz','rt'));seen=set()
 for i,r in enumerate(pairs):
  assert r['index']==i and r['positions']==list(range(len(r['correct']['history_tokens'])))
  assert len(r['correct']['history_tokens'])==len(r['unrelated']['history_tokens'])
  assert r['correct']['document_family']!=r['unrelated']['document_family']and r['correct']['year']==r['unrelated']['year']
  for k in ['correct','unrelated']:
   v=r[k];source=corpus[v['record']];ref=schedule['arms']['B'][v['batch_index']][v['row_index']]
   assert ref==v['ref']and source['id']==v['source_id']and source['source_sha256']==v['source_sha256']and source['text_sha256']==v['text_sha256']
   start=ref['start']if k=='correct'else v['retained_source_start'];end=v['source_position'];ids=v['history_tokens']
   assert source['tokens'][start:end]==ids and ref['start']<end<ref['start']+ref['length']and source['tokens'][end]==v['gold']
   assert ids[-2:]==[16,16]and all(t>=6 for t in ids)and 64<=len(ids)<=248
   assert b''.join(pieces[t]for t in ids).decode('utf8')==v['history_text']
   h=input_hash(ids);assert h not in seen;seen.add(h)
   if k=='correct':assert source['tokens'][end:end+8]==r['teacher_tail']and r['gold']==source['tokens'][end]
 assert len(pairs)==32 and sum(r['group']=='mata'for r in pairs)==16
 print('32 frozen-source pairs /64 exact UTF8 inputs validated; no model forward.')
if __name__=='__main__':validate()
