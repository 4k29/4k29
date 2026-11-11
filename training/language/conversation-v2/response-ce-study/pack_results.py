"""Lossless text transport for new audit artifacts; never include private/held token cards."""
import pathlib,json,gzip,base64,hashlib
P=pathlib.Path(__file__).resolve().parent
NAMES=['CANDIDATE_SPANS.json','REVIEW.json','SELECTION_METADATA.json','SUPPLEMENT_REVIEW.json']
def main():
 rows=[]
 for n in NAMES:
  b=(P/n).read_bytes();json.loads(b);z=gzip.compress(b,mtime=0);name=n+'.gz.b64';(P/name).write_text(base64.b64encode(z).decode()+'\n');rows.append(dict(name=n,packed=name,raw_bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),gzip_sha256=hashlib.sha256(z).hexdigest()))
 (P/'PACKED_INDEX.json').write_text(json.dumps(dict(format='gzip mtime0 + base64, UTF8 raw bytes unchanged',files=rows,held_original_text_or_tokens_included=False),indent=2)+'\n')
if __name__=='__main__':main()
