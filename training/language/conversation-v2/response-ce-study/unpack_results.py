"""SHA-verified local decoding only; never overwrite different existing evidence."""
import pathlib,json,gzip,base64,hashlib,os
P=pathlib.Path(__file__).resolve().parent
os.umask(0o077)
def main():
 index=json.loads((P/'PACKED_INDEX.json').read_text())
 for r in index['files']:
  dest=P/r['name'];assert dest.parent==P and (P/r['packed']).parent==P
  z=base64.b64decode((P/r['packed']).read_text().strip(),validate=True);assert hashlib.sha256(z).hexdigest()==r['gzip_sha256'];b=gzip.decompress(z);assert len(b)==r['raw_bytes']and hashlib.sha256(b).hexdigest()==r['sha256'];json.loads(b)
  if dest.exists():assert dest.read_bytes()==b,'Never overwrite differing existing raw evidence'
  else:
   with dest.open('xb')as f:f.write(b)
 print('Four lossless audit files verified; optimizer0, model forward0.')
if __name__=='__main__':main()
