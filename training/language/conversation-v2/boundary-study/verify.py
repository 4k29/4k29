"""Frozen artifacts/source and complete checkpoint streams, no Torch required."""
import argparse,hashlib,json,pathlib,subprocess
N=pathlib.Path(__file__).resolve().parent;ROOT=N.parents[3];V=N.parent;H=V/'foundation-stage'
def raw(p):return p.read_bytes()if p.exists()else subprocess.check_output(['git','show','HEAD:'+p.relative_to(ROOT).as_posix()],cwd=ROOT)
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def inventory():
 files=[p for p in N.rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.suffix not in ['.pt','.pending','.f32','.pyc']and p.name not in ['MANIFEST.json','worker.lock']]
 deps=[H/s for s in ['runtime.py','mixed_runtime.py','prose_decode.py','prepare.py','TOKEN_BOUNDARY_PROTOCOL.json','data.jsonl.gz','schedule.json.gz','prose-dev.json','evaluation/initial.json','evaluation/initial-token-boundary.json']]+[V/s for s in ['core.py','PLAN.json','new_tokenizer.py','eval_core.py','data/tokenizer.json','data/data.json','data/train.tokens.bin','data/dev.tokens.bin','epoch1/medium/archive/checkpoint.pt.chunks.json','epoch1/content-dev.json','response-data/final/active-dev.json','foundation-data/research/zero_update_preflight.py','foundation-data/corpus/documents.jsonl.gz','foundation-data/catalog.json','foundation-data/DATA-LICENSE.md','foundation-data/evaluation/human-dev.json','grounded-objective/data.json','grounded-objective/PLAN.json','grounded-objective/CONTEXT_PROBE_PLAN.json','grounded-objective/evaluation/initial3470.json','parity.py','parity.mjs']]+[ROOT/s for s in ['GOAL.md','training/language/model.py','training/language/round10/word_bpe.py','training/dialogue/tokenizer.py','training/dialogue/inference.mjs','.github/workflows/boundary-study.yml']]
 files+=deps;result={p.relative_to(ROOT).as_posix():dict(bytes=len(raw(p)),sha256=sha(p))for p in sorted(set(files))}
 for manifest in(N/'run').glob('*/archive/checkpoint.json'):
  for r in json.loads(manifest.read_text())['chunks']:result[(manifest.parent/r['path']).relative_to(ROOT).as_posix()]=dict(bytes=r['bytes'],sha256=r['sha256'])
 return result

def verify():
 m=json.loads((N/'MANIFEST.json').read_text())
 for name,r in m.items():
  b=raw(ROOT/name);assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],name
 count=0
 for p in(N/'run').glob('*/archive/checkpoint.json'):
  r=json.loads(p.read_text());whole=hashlib.sha256();total=0
  for part in r['chunks']:
   b=raw(p.parent/part['path']);assert len(b)==part['bytes']and hashlib.sha256(b).hexdigest()==part['sha256'];whole.update(b);total+=len(b)
  assert whole.hexdigest()==r['sha256']and total==r['bytes'];count+=1
 print('Verified',len(m),'artifact/source SHA records and',count,'complete checkpoint byte streams')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
 if a.write:(N/'MANIFEST.json').write_text(json.dumps(inventory(),indent=2)+'\n')
 verify()
