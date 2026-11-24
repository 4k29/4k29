"""SHA and complete lossless checkpoint stream verification, standard library only."""
import argparse,hashlib,json,pathlib,subprocess
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[3];V=H.parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  while b:=f.read(1024**2):h.update(b)
 return h.hexdigest()
def raw(p):
 return p.read_bytes()if p.exists()else subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT)
def inventory():
 files=[p for p in H.rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.name not in ['MANIFEST.json','PROCESS.json','worker.lock']and p.suffix not in ['.pt','.pending','.pyc','.f32']]
 files +=[V/p for p in ['core.py','new_tokenizer.py','eval_core.py','PLAN.json','data/tokenizer.json','data/data.json','data/train.tokens.bin','data/dev.tokens.bin','epoch1/content-dev.json','response-data/final/active-dev.json','foundation-data/evaluation/human-dev.json','foundation-data/DATA-LICENSE.md','foundation-data/catalog.json','foundation-data/research/zero_update_preflight.py','grounded-objective/PLAN.json','grounded-objective/data.json','grounded-objective/CONTEXT_PROBE_PLAN.json','grounded-objective/evaluation/initial3470.json','parity.py','parity.mjs']]
 files +=[ROOT/p for p in ['GOAL.md','training/language/model.py','training/language/round10/word_bpe.py','training/dialogue/tokenizer.py','training/dialogue/inference.mjs','.github/workflows/foundation-stage.yml']]
 result={p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p))for p in sorted(set(files))}
 for manifest in(H/'run').glob('*/archive/checkpoint.json'):
  for r in json.loads(manifest.read_text())['chunks']:
   p=manifest.parent/r['path'];result[p.relative_to(ROOT).as_posix()]=dict(bytes=r['bytes'],sha256=r['sha256'])
 return result
def verify():
 data=json.loads((H/'MANIFEST.json').read_text())
 for name,r in data.items():
  p=ROOT/name;b=raw(p);assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],name
 count=0
 for p in(H/'run').glob('*/archive/checkpoint.json'):
  m=json.loads(p.read_text());whole=hashlib.sha256();total=0
  for row in m['chunks']:
   b=raw(p.parent/row['path']);assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256'];whole.update(b);total+=len(b)
  assert total==m['bytes']and whole.hexdigest()==m['sha256'];count+=1
 print('Verified',len(data),'artifact/source SHAs and',count,'complete checkpoint byte streams')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
 if a.write:(H/'MANIFEST.json').write_text(json.dumps(inventory(),indent=2)+'\n')
 verify()
