"""Offline result and source integrity verification. Never performs updates."""
import argparse,hashlib,json,pathlib,os
H=pathlib.Path(__file__).resolve().parent;V=H.parent

def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main(freeze=False):
 manifest=H/'MANIFEST.json'
 if freeze:
  files=[p for p in sorted(H.rglob('*'))if p.is_file()and'__pycache__'not in p.parts and p.name not in ['MANIFEST.json','verification.log']and p.suffix!='.pt']
  inputs=[V/'data/data.json',V/'data/tokenizer.json',V/'data/train.docs.jsonl',V/'data/dev.docs.jsonl',V/'response-data/final/active-dev.json',V/'epoch1/content-dev.json',V/'allocation-study/schedule.json',V/'core.py',V/'eval_core.py',V/'new_tokenizer.py',V.parent/'model.py',V.parent/'round10/word_bpe.py',V.parents[1]/'dialogue/tokenizer.py',V/'sns-data/pipeline/publication-policy.json']
  manifest.write_text(json.dumps({'artifacts':[{'path':str(p.relative_to(H)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in files],'source_receipts':[{'path':os.path.relpath(p,V),'sha256':sha(p)}for p in inputs]},indent=2)+'\n')
 d=json.loads(manifest.read_text())
 for r in d['artifacts']:
  p=H/r['path'];assert p.resolve().is_relative_to(H.resolve());assert p.stat().st_size==r['bytes'];assert sha(p)==r['sha256'],r['path']
 for r in d['source_receipts']:assert sha(V/r['path'])==r['sha256'],r['path']
 s=json.loads((H/'SUMMARY.json').read_text());assert s['actual_optimizer_updates_total']==84 and s['valid_retained_updates_total']==28 and s['actual_updates_discarded_total']==56 and not s['language_improvement_demonstrated']
 print(json.dumps({'passed':True,'artifact_count':len(d['artifacts']),'source_receipts':len(d['source_receipts']),'actual_optimizer_calls':84,'valid_retained_new_updates':28,'this_verifier_optimizer_updates':0}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');main(p.parse_args().freeze)
