"""Stdlib whole-artifact integrity, raw-byte reconstruction and actual-call accounting."""
import argparse,pathlib,json,hashlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def checkpoint(p):
 d=read(p);whole=hashlib.sha256();size=0
 for part in d['chunks']:
  f=p.parent/part['path'];b=f.read_bytes();assert len(b)==part['bytes']and hashlib.sha256(b).hexdigest()==part['sha256'];whole.update(b);size+=len(b)
 assert size==d['bytes']and whole.hexdigest()==d['sha256'];return d

def main():
 a=argparse.ArgumentParser();a.add_argument('--write',action='store_true');args=a.parse_args();tok=read(P.parent/'data/tokenizer.json');pieces=[bytes.fromhex(v)for v in tok['bytes']];evaluations=0
 for f in(P/'evaluation').glob('*.json'):
  d=read(f)
  if'cases'in d and isinstance(d['cases'],list)and d['cases']and'tokensIncludingEos'in d['cases'][0]:rows=d['cases']
  elif'prose_dev'in d:rows=d['prose_dev']+d['grounded36']+d['legacy']+d['context12']+[r for e in d['self_history']for r in e['turns']if'tokensIncludingEos'in r]
  else:continue
  for r in rows:
   ids=r['nonEosTokens'];assert r['tokensIncludingEos']==ids+([2]if r['eos']else[]);raw=b''.join(pieces[i]for i in ids);assert raw.hex()==r['rawBytesHex']
   if r['strictUtf8']:assert raw.decode()==r['text']
   else:
    try:raw.decode();raise AssertionError('invalid UTF8 not confirmed')
    except UnicodeDecodeError:assert r['text']is None
   evaluations+=1
 checkpoints=[checkpoint(p)for p in P.rglob('archive*/checkpoint.json')]
 if args.write:
  paths=[]
  for f in sorted(P.rglob('*')):
   if not f.is_file()or f.suffix in ['.pt','.pending']or'__pycache__'in f.parts or f.name.endswith('.lock')or f.name in ['MANIFEST.json','VERIFY.json','verify.log']or f.name in ['candidates.jsonl.gz','QUALITY_SAMPLE.json','NEW_DEV_SOURCES.json']:continue
   paths.append(dict(path=str(f.relative_to(P)),bytes=f.stat().st_size,sha256=sha(f)))
  (P/'MANIFEST.json').write_text(json.dumps(dict(files=paths),indent=2)+'\n')
 else:
  for r in read(P/'MANIFEST.json')['files']:
   p=P/r['path'];assert p.stat().st_size==r['bytes']and sha(p)==r['sha256'],str(p)
 result=dict(artifact_records=len(read(P/'MANIFEST.json')['files']),full_checkpoint_streams=len(checkpoints),raw_generated_cases_verified=evaluations,pass_all=True)
 (P/'VERIFY.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
