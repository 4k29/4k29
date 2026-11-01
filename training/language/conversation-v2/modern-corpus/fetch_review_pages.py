"""Fetch only the pre-fixed twelve public article pages for attribution and quality review."""
import pathlib,json,gzip,urllib.request,datetime,hashlib,time
D=pathlib.Path(__file__).resolve().parent;P=D/'private';ids=json.loads((D/'PILOT_SUMMARY.json').read_text())['sample_ids'];by={r['id']:r for r in map(json.loads,gzip.open(P/'pilot-candidates.jsonl.gz','rt'))};records=[]
for ident in ids:
 r=by[ident];path=P/f'review-{ident}.html';receipt=P/f'review-{ident}.receipt.json'
 if not path.exists():
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with urllib.request.urlopen(r['url'],timeout=45)as response:b=response.read();headers=dict(response.headers)
  path.write_bytes(b);receipt.write_text(json.dumps(dict(id=ident,url=r['url'],request_start_utc=start,response_end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(b).hexdigest(),headers=headers),indent=2)+'\n');time.sleep(10)
 records.append(json.loads(receipt.read_text()))
 (D/'REVIEW_PAGE_RECEIPTS.json').write_text(json.dumps(records,indent=2)+'\n')
 print('review page cached',ident,flush=True)
