"""Register4 early-exposed TRAIN probes, never count them as unknown-family success."""
import pathlib,json,gzip,hashlib
N=pathlib.Path(__file__).resolve().parent;D=N/'next-foundation'
def main():
 assert not(D/'evaluation').exists(),'Register before any new series generation';path=D/'EVALUATION.json';v=json.loads(path.read_text());assert not any(c['panel']=='train-caption4'for c in v['cases']);corpus=[json.loads(s)for s in gzip.open(D/'corpus.jsonl.gz','rt')];schedule=json.load(gzip.open(D/'schedule.json.gz','rt'))['batches'];seen=set();cases=[];pieces=[bytes.fromhex(s)for s in json.loads((N.parent/'data/tokenizer.json').read_text())['bytes']]
 for step,batch in enumerate(schedule[:128],1):
  for ref in batch:
   r=corpus[ref['record']]
   if r['source']!='stair'or r['family']in seen or len(r['tokens'])<14:continue
   cut=9
   while True:
    try:b''.join(pieces[t]for t in r['tokens'][1:cut]).decode('utf-8');break
    except UnicodeDecodeError:cut+=1
   seen.add(r['family']);cases.append(dict(id=r['id'],panel='train-caption4',prefix=r['tokens'][:cut],text=r['text'],image_family=r['family'],first_teacher_batch=step,source_text_sha256=r['source_text_sha256'],semantic_scope='TRAIN memorization/learning diagnostic, not generalization. At step0 unseen; at comparison1997 all4 source records have actually been processed.'))
   if len(cases)==4:break
  if len(cases)==4:break
 assert len(cases)==4;v['cases']+=cases;v['TRAIN_probe_registration']=dict(case_count=4,selection='First4 distinct-image caption units with>=12 body tokens in first128 frozen batches, before any new generation',counted_as_DEV_or_TEST=False);path.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print('Registered4 TRAIN probes at batches',[c['first_teacher_batch']for c in cases])
if __name__=='__main__':main()
