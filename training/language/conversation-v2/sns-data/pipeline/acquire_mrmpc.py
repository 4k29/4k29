"""Bounded official dialogue-only acquisition. No profiles or cross-service identities."""
import concurrent.futures,datetime,gzip,hashlib,json,pathlib,time,urllib.request
HERE=pathlib.Path(__file__).resolve().parents[1]
REPO='nu-dialogue/multi-relational-multi-party-chat-corpus'
REV='e6e39cb896df88781c7a2e0451226a527c5f1e2e'
RAW='https://raw.githubusercontent.com/'+REPO+'/'+REV+'/'
def fetch(url,limit=1000000):
 req=urllib.request.Request(url,headers={'User-Agent':'4k29-research/1.0 source-rights-audit'})
 with urllib.request.urlopen(req,timeout=45) as r:
  b=r.read(limit+1)
  if len(b)>limit:raise ValueError('bounded download exceeded')
  return b
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 tmp=pathlib.Path('/dev/shm/sns-mrmpc');tmp.mkdir(exist_ok=True)
 evidence={}
 for name in ['README.md','LICENSE']:
  b=fetch(RAW+name);evidence[name]={'sha256':sha(b),'url':RAW+name}
  (HERE/'raw'/('MRMPC-'+name)).write_bytes(b)
 readme=(HERE/'raw/MRMPC-README.md').read_text()
 assert '本コーパスは [CC BY-SA 4.0]' in readme
 tree=json.loads(fetch('https://api.github.com/repos/'+REPO+'/git/trees/'+REV+'?recursive=1',3000000))
 paths=[x['path'] for x in tree['tree'] if x['type']=='blob' and x['path'].startswith('multi_relational_multi_party_chat_corpus/dialogues/') and x['path'].endswith('.json')]
 assert len(paths)==960
 paths.sort()
 ledger=[]
 def one(path):
  dest=tmp/pathlib.Path(path).name
  if dest.exists():b=dest.read_bytes()
  else:
   b=fetch(RAW+path);dest.write_bytes(b)
  d=json.loads(b);assert d['dialogue_id']==dest.stem and len(d['utterances'])>=2
  assert all(set(u)<= {'utterance_id','interlocutor_id','text','mention_to'} for u in d['utterances'])
  return {'path':path,'url':RAW+path,'bytes':len(b),'sha256':sha(b),'data':d}
 # Pilot is validated before bounded expansion; only dialogue paths are requested.
 for path in paths[:8]:ledger.append(one(path));time.sleep(.5)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  pending=[]
  for path in paths[8:]:
   for prior in pending:
    if prior.done() and prior.exception() is not None:
     for queued in pending:queued.cancel()
     raise prior.exception()
   pending.append(pool.submit(one,path));time.sleep(.5)
  for f in pending:ledger.append(f.result())
 out=HERE/'raw/mrmpc-dialogues.jsonl.gz'
 with out.open('wb') as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as z:
   for row in ledger:z.write((json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 receipt={'source':'mrmpc','repository':REPO,'revision':REV,'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'license':'CC-BY-SA-4.0','rightsEvidence':evidence,'acquisition':'official raw dialogue JSON only; no interlocutor profiles','pilotValidated':8,'maxRequestStartsPerSecond':2,'maxConcurrent':2,'requestsPlanned':len(paths)+3,'dialogues':len(ledger),'rawBytes':sum(x['bytes']for x in ledger),'archiveSha256':sha(out.read_bytes()),'archiveBytes':out.stat().st_size,'rows':[ {k:v for k,v in r.items()if k!='data'}for r in ledger]}
 (HERE/'raw/acquisition.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in receipt.items()if k not in ['rows','rightsEvidence']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
