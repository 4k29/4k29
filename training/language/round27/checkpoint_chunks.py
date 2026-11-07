"""Lossless own-checkpoint chunks for future capacity checkpoints over GitHub100MiB."""
import pathlib,hashlib,json,argparse
BLOCK=1024*1024

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(BLOCK),b''):h.update(block)
 return h.hexdigest()
def pack(path,chunk_size=40*1024*1024):
 path=pathlib.Path(path);assert path.is_file() and chunk_size>0
 size=path.stat().st_size;original=digest(path);directory=path.parent/(path.name+'.chunks.'+original[:12]);directory.mkdir(exist_ok=True);records=[];combined=hashlib.sha256()
 with path.open('rb') as src:
  i=0
  while True:
   data=src.read(chunk_size)
   if not data:break
   target=directory/f'part-{i:03d}.bin';wanted=hashlib.sha256(data).hexdigest()
   if target.exists():assert target.stat().st_size==len(data) and digest(target)==wanted
   else:
    temp=target.with_suffix('.tmp');temp.write_bytes(data);temp.replace(target)
   records.append(dict(path=str(target.relative_to(path.parent)),bytes=len(data),sha256=wanted));combined.update(data);i+=1
 assert sum(r['bytes'] for r in records)==size and combined.hexdigest()==original and path.stat().st_size==size and digest(path)==original
 manifest=dict(schemaVersion=1,filename=path.name,bytes=size,sha256=original,chunks=records,losslessByteConcatenation=True)
 dest=path.with_name(path.name+'.chunks.json');temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(manifest,indent=2)+'\n');temp.replace(dest);return dest

def restore(manifest):
 manifest=pathlib.Path(manifest);record=json.loads(manifest.read_text());assert pathlib.Path(record['filename']).name==record['filename'];dest=manifest.parent/record['filename']
 if dest.exists():
  if dest.stat().st_size==record['bytes'] and digest(dest)==record['sha256']:return dest
  raise ValueError('Existing checkpoint differs; refuse to overwrite')
 # Validate every chunk before creating a reconstructed file.
 paths=[]
 for part in record['chunks']:
  p=manifest.parent/part['path'];assert p.resolve().is_relative_to(manifest.parent.resolve())
  if p.stat().st_size!=part['bytes'] or digest(p)!=part['sha256']:raise ValueError('Corrupt checkpoint chunk')
  paths.append(p)
 temp=dest.with_name(dest.name+'.restore.tmp');total=0;sha=hashlib.sha256()
 try:
  with temp.open('wb') as out:
   for p in paths:
    with p.open('rb') as src:
     for data in iter(lambda:src.read(BLOCK),b''):out.write(data);sha.update(data);total+=len(data)
  if total!=record['bytes'] or sha.hexdigest()!=record['sha256']:raise ValueError('Reconstructed checkpoint does not match original')
  temp.replace(dest);return dest
 except BaseException:
  temp.unlink(missing_ok=True);raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('operation',choices=['pack','restore']);p.add_argument('path',type=pathlib.Path);a=p.parse_args();print(pack(a.path) if a.operation=='pack' else restore(a.path))
