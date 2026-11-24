import pathlib,json,gzip,base64,hashlib
P=pathlib.Path(__file__).resolve().parent
for r in json.loads((P/'METADATA_PACK.json').read_text())['files']:
 z=base64.b64decode(''.join((P/part).read_text().strip()for part in r['parts']),validate=True);assert hashlib.sha256(z).hexdigest()==r['gzip_sha256'];b=gzip.decompress(z);assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'];(P/r['name']).write_bytes(b)
