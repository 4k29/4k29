"""Expand only approved candidate token records and judgment metadata, checking both SHAs."""
import pathlib,json,base64,gzip,hashlib
P=pathlib.Path(__file__).resolve().parent
for row in json.loads((P/'DATA_PACK_INDEX.json').read_text())['files']:
 z=base64.b64decode((P/row['packed']).read_text().strip(),validate=True);assert hashlib.sha256(z).hexdigest()==row['gzip_sha256'];b=gzip.decompress(z);assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256'];(P/row['name']).write_bytes(b)
