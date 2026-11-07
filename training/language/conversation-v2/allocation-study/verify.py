"""Offline immutable artifact/input checks, no optimizer/network/model construction."""
import hashlib,json,pathlib,argparse
H=pathlib.Path(__file__).resolve().parent;V=H.parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(freeze=False):
 manifest=H/'MANIFEST.json'
 if freeze:
  files=[p for p in sorted(H.rglob('*'))if p.is_file()and'__pycache__'not in p.parts and p.name not in ['MANIFEST.json','verification.log']]
  sources=[V/'data/data.json',V/'data/train.docs.jsonl',V/'data/tokenizer.json',V/'core.py',V/'response-data/final/active-dev.json',V/'response-data/research/matched_schedule.py']
  manifest.write_text(json.dumps({'artifacts':[{'path':str(p.relative_to(H)),'sha256':sha(p),'bytes':p.stat().st_size}for p in files],'inputs':[{'path':str(p.relative_to(V)),'sha256':sha(p)}for p in sources]},indent=2)+'\n')
 data=json.loads(manifest.read_text())
 for r in data['artifacts']:
  p=H/r['path'];assert p.resolve().is_relative_to(H.resolve());assert sha(p)==r['sha256'];assert p.stat().st_size==r['bytes']
 for r in data['inputs']:assert sha(V/r['path'])==r['sha256']
 s=json.loads((H/'SUMMARY.json').read_text());assert s['optimizer_updates']==0 and not s['training_go'];assert s['RP_fixed_whole_dialogues_read']==20 and s['jmultiwoz_fixed_conversations_read']==40
 print(json.dumps({'passed':True,'artifact_count':len(data['artifacts']),'input_count':len(data['inputs']),'optimizer_updates':0}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');run(p.parse_args().freeze)
