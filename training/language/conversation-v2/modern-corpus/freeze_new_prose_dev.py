"""Freeze source-held-out food explanation diagnostic before any model output.
All MAFF source text stays out of TRAIN in this study. Not a sealed TEST or human evaluation.
"""
import pathlib,json,gzip,hashlib,sys
D=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent));from new_tokenizer import Encoder

def main():
 public=D/'NEW_PROSE_DEV_PROTOCOL.json';private=D/'private/new-prose-dev.json'
 assert not public.exists()and not private.exists(),'Do not silently replace frozen DEV'
 old=D.parent/'diverse-foundation/future-sources/maff';review=json.loads((D/'MAFF_COMPLETE_REVIEW.json').read_text());allowed={r['id']:r for r in review['decisions']if r['genre']=='mame'and r['decision']=='research_prose_candidate'};tok=json.loads((D.parent/'data/tokenizer.json').read_text());enc=Encoder(tok);pieces=[bytes.fromhex(s)for s in tok['bytes']];cases=[]
 for line in gzip.open(old/'candidates.private.jsonl.gz','rt'):
  r=json.loads(line)
  if r['id']not in allowed:continue
  sha=hashlib.sha256(r['text'].encode()).hexdigest();assert sha==allowed[r['id']]['original_text_sha256'];prov=r['provenance'];raw=gzip.decompress((old/prov['snapshot']).read_bytes());assert hashlib.sha256(raw).hexdigest()==prov['raw_sha256'];body=enc(r['text']);assert b''.join(pieces[i]for i in body)==r['text'].encode()
  count=min(12,len(body)-1)
  while count<len(body):
   try:b''.join(pieces[i]for i in body[:count]).decode('utf-8');break
   except UnicodeDecodeError:count+=1
  cases.append(dict(id=r['id'],source_url=prov['url'],source_sha256=prov['raw_sha256'],text_sha256=sha,text=r['text'],tokens=[1]+body,prefix=[1]+body[:count],prefix_body_tokens=count,body_tokens=len(body),teacher_target_limit=min(256,len(body)),source_boundary='Complete original QA answer section before references, previously fully read; no training EOS inserted',split='new exposed DEV diagnostic; entire MAFF source excluded from TRAIN'))
 cases.sort(key=lambda r:r['id']);private.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
 manifests={}
 for arm in ['A','B']:
  path=D.parent/'diverse-foundation/run'/arm/'archive-06459/checkpoint.json';m=json.loads(path.read_text());manifests[arm]=dict(checkpoint_sha256=m['sha256'],manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),name=arm+'-6459')
 proto=dict(cases=[{k:v for k,v in r.items()if k not in {'text','tokens','prefix'}}for r in cases],case_count=len(cases),private_inputs_sha256=hashlib.sha256(private.read_bytes()).hexdigest(),tokenizer_sha256=hashlib.sha256((D.parent/'data/tokenizer.json').read_bytes()).hexdigest(),checkpoints=manifests,decode=dict(kind='full-vocabulary greedy',max_new_tokens=128,stop='genuine token2 or fixed budget',postprocessing='none; raw bytes and tokens retained'),teacher_NLL='First up to256 body target positions with exact source teacher history; no invented EOS target, no padding loss',purpose='New source/genre baseline prior to future training, not a new training experiment or independent TEST',family_policy='All MAFF source excluded from current/future TRAIN unless this benchmark is explicitly retired to exposed diagnosis. Institutional writer identities unknown; author independence not claimed.',limitations='Main-assistant reviewed source, no independent native-speaker evaluation, food facts not independently certified QA. Previous source samples were read but model outputs not seen at freeze.',optimizer_updates=0)
 public.write_text(json.dumps(proto,ensure_ascii=False,indent=2)+'\n');print('Frozen cases',len(cases),'teacher targets',sum(r['teacher_target_limit']for r in cases))
if __name__=='__main__':main()
