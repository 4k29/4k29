"""Freeze additional language diagnostics before new model generation.
Caption evaluation asks plausible textual continuation, never unseen-image accuracy.
"""
import pathlib,json,gzip,hashlib,collections
N=pathlib.Path(__file__).resolve().parent;D=N/'next-foundation'
def rank(s):return hashlib.sha256(('caption-eval-v1|'+s).encode()).hexdigest()
def main():
 path=N/'private/unreviewed-evaluation-v1.json';assert not path.exists(),'Do not overwrite frozen/observed DEV';old=json.loads((N.parent/'diverse-foundation/EVALUATION.json').read_text());cases=[dict(r,reuse='PR104 exposed diagnostic unchanged')for r in old['cases']];pool=collections.defaultdict(list);pieces=[bytes.fromhex(s)for s in json.loads((N.parent/'data/tokenizer.json').read_text())['bytes']]
 for line in gzip.open(N/'private/stair-prose-candidates.jsonl.gz','rt'):
  r=json.loads(line)
  if r['split']=='dev'and len(r['body_tokens'])>=12:pool[r['original_image_id']].append(r)
 for image in sorted(pool,key=lambda n:rank(str(n)))[:32]:
  r=min(pool[image],key=lambda r:rank(r['id']));body=r['body_tokens'];cut=8
  while True:
   try:b''.join(pieces[t]for t in body[:cut]).decode('utf-8');break
   except UnicodeDecodeError:cut+=1
  cases.append(dict(id=r['id'],panel='new-caption32',prefix=[1]+body[:cut],text=r['text'],source_text_sha256=r['text_sha256'],image_family=r['image_family'],semantic_scope='Natural coherent continuation of textual prefix; no hidden image information or reference-string exact match required',source='STAIR Captions1.2 originalTRAIN reserved image families, CC BY4.0'))
 for r in json.loads((N/'private/new-prose-dev.json').read_text()):cases.append(dict(id=r['id'],panel='new-MAFF12',prefix=r['prefix'],text=r['text'],source_text_sha256=r['text_sha256'],source_url=r['source_url'],semantic_scope='Natural continuation of original explanatory QA prose; not independently certified factual QA'))
 caption_dev=[]
 for line in gzip.open(N/'private/stair-prose-candidates.jsonl.gz','rt'):
  r=json.loads(line)
  if r['split']=='dev':caption_dev.append(dict(id=r['id'],tokens=[1]+r['body_tokens']+[2],panel='caption_DEV',body_tokens=len(r['body_tokens'])))
 maff=[dict(id=r['id'],tokens=r['tokens'][:257],panel='MAFF_DEV_no_fake_EOS')for r in json.loads((N/'private/new-prose-dev.json').read_text())]
 result=dict(cases=cases,old_dev_windows=old['dev_windows'],caption_dev=caption_dev,maff_dev=maff,decode=dict(kind='full-vocabulary greedy',max_new=128,EOS=2,postprocess='none; retain exact bytes and all token IDs'),semantic_rubric=dict(existing='Retain prior full-continuation and developed-paragraph distinction, strict old gates unchanged',caption='Whole prefix+generation must be natural coherent Japanese; no harmful repetition, no special tokens, no topic break; immediate EOS at incomplete prefix fails',paragraph='Do not infer multi-sentence coherence from one caption-like sentence',content='Old content/provided-context/multiturn panels retained separately; no assent-only success'),formal_TEST=False,independent_human_evaluation=False,selection_use='Exposed DEV for exploratory series choice only',optimizer_updates_at_freeze=0)
 path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('Frozen evaluation',dict(collections.Counter(r['panel']for r in cases)),len(caption_dev),'caption teacher units')
if __name__=='__main__':main()
