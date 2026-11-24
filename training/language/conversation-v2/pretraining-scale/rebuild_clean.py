"""Reconstruct qualified corpus/schedule from frozen v2 inputs, without replaying historical learning or overwriting files."""
import gzip,json,pathlib,hashlib,io
P=pathlib.Path(__file__).resolve().parent

def rows(path):return list(map(json.loads,gzip.open(path,'rt')))
def resolve(rows0,source_id):
 by={r['id']:r for r in rows0};assert source_id in by;return by[source_id]['component']
def encode(rows0):
 f=io.BytesIO()
 with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0)as z:
  for r in rows0:z.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 return f.getvalue()
def main():
 old=rows(P/'corpus.jsonl.gz');component=resolve(old,'jawikivoyage:5078:2');held={r['id']for r in old if r['component']==component};data=encode([r for r in old if r['id']not in held]);assert data==(P/'corpus-clean.jsonl.gz').read_bytes();old_schedule=json.load(gzip.open(P/'schedule.json.gz','rt'))['batches'];clean=[[w for w in b if w['unit_id']not in held]for b in old_schedule];assert clean==json.load(gzip.open(P/'schedule-clean.json.gz','rt'))['batches'];print(dict(corpus_byte_exact=True,schedule_exact=True,source_ID_resolved_component=component,held_units=len(held)))
if __name__=='__main__':main()
