import pathlib,json,base64,gzip,hashlib
p=pathlib.Path(__file__).resolve().parent;r=json.loads((p/'READING_PACK.json').read_text());z=base64.b64decode((p/r['packed']).read_text().strip(),validate=True);assert hashlib.sha256(z).hexdigest()==r['gzip_sha256'];b=gzip.decompress(z);assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'];(p/r['name']).write_bytes(b)
