"""Seven preselected PD-flagged essay candidates; no automatic training adoption."""
import pathlib,json,urllib.request,datetime,hashlib,gzip,time
D=pathlib.Path(__file__).resolve().parent;P=D/'private/aozora';P.mkdir(exist_ok=True)
def fetch(name,url):
 path=P/(name+'.gz');receipt=P/(name+'.receipt.json')
 if path.exists():
  r=json.loads(receipt.read_text());raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==r['sha256'];return r
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with urllib.request.urlopen(url,timeout=45)as response:raw=response.read(2*1024**2+1);headers=dict(response.headers)
 assert len(raw)<=2*1024**2
 path.write_bytes(gzip.compress(raw,mtime=0));r=dict(name=name,url=url,request_start_utc=start,response_end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw),headers=headers,local_snapshot=str(path.relative_to(D)))
 receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');time.sleep(3);return r
receipts=[]
for name,url in [('robots','https://www.aozora.gr.jp/robots.txt'),('terms','https://www.aozora.gr.jp/guide/kijyunn.html')]:receipts.append(fetch(name,url))
for row in json.loads((D/'AOZORA_PILOT_SELECTION.json').read_text())['selected']:
 for kind,field in [('card','図書カードURL'),('work','XHTML/HTMLファイルURL')]:
  receipts.append(fetch(row['作品ID']+'-'+kind,row[field]));(D/'AOZORA_ACQUISITION.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n');print('cached',row['作品ID'],kind,flush=True)
