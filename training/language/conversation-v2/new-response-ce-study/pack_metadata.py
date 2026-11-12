"""Pack metadata only. Raw questions, responses, token sequences and checkpoints are forbidden."""
import pathlib,json,gzip,base64,hashlib
P=pathlib.Path(__file__).resolve().parent;index=[]
for name in ['CANDIDATE_METADATA.json','CORPUS_AUDIT.json']:
 raw=(P/name).read_bytes();obj=json.loads(raw)
 if name=='CANDIDATE_METADATA.json':
  for r in obj:assert not({'tokens','question','answer','text','output','history','utterances'}&set(r))
 z=gzip.compress(raw,mtime=0);encoded=base64.b64encode(z).decode();parts=[]
 for i,start in enumerate(range(0,len(encoded),120000)):
  packed=name+'.gz.b64.part-'+str(i).zfill(3);(P/packed).write_text(encoded[start:start+120000]+'\n');parts.append(packed)
 index.append(dict(name=name,parts=parts,sha256=hashlib.sha256(raw).hexdigest(),gzip_sha256=hashlib.sha256(z).hexdigest(),bytes=len(raw)))
(P/'METADATA_PACK.json').write_text(json.dumps(dict(contents='IDs, hashes, counts, flags, provenance only; no source body or BPE token sequence',files=index),indent=2)+'\n')
