"""Quarantine a known faulty reference before model output, preserve valid family split."""
import pathlib,json,gzip,hashlib,argparse
N=pathlib.Path(__file__).resolve().parent;D=N/'next-foundation'
def main():
 a=argparse.ArgumentParser();a.add_argument('--output',default=str(D/'EVALUATION.json'));args=a.parse_args();out=pathlib.Path(args.output);assert not out.exists();source=N/'private/unexecuted-EVALUATION.json';v=json.loads(source.read_text());bad='stair:510558';case=next(r for r in v['cases']if r['id']==bad);family=case['image_family'];pool=[]
 for line in gzip.open(N/'private/stair-prose-candidates.jsonl.gz','rt'):
  r=json.loads(line)
  if r['split']=='dev'and r['image_family']==family and r['id']!=bad and len(r['body_tokens'])>=12:pool.append(r)
 r=min(pool,key=lambda r:hashlib.sha256(('caption-eval-v1|'+r['id']).encode()).hexdigest());pieces=[bytes.fromhex(s)for s in json.loads((N.parent/'data/tokenizer.json').read_text())['bytes']];cut=8
 while True:
  try:b''.join(pieces[t]for t in r['body_tokens'][:cut]).decode('utf-8');break
  except UnicodeDecodeError:cut+=1
 replacement={**case,'id':r['id'],'prefix':[1]+r['body_tokens'][:cut],'text':r['text'],'source_text_sha256':r['text_sha256']};v['cases']=[replacement if c['id']==bad else c for c in v['cases']];v['caption_dev']=[c for c in v['caption_dev']if c['id']!=bad];v['source_review_correction']=dict(original_unexecuted_proposal_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),before_any_new_training_or_caption_model_output=True,quarantined_reference_id=bad,replacement_id=r['id'],same_reserved_image_family=family,reason='Known typo reference removed from teacher NLL and generative reference. Replacement original caption fully read and unchanged. Original proposal kept privately; no past result overwritten.')
 out.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print('Final fixed DEV; teacher caption units',len(v['caption_dev']),'caption generation cases',sum(c['panel']=='new-caption32'for c in v['cases']))
if __name__=='__main__':main()
