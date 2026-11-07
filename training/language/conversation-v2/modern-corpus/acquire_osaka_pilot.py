"""Small fixed pilot of city-authored everyday guidance; no PDFs, images or external FAQ."""
import pathlib,json,urllib.request,datetime,time,hashlib,gzip,os
D=pathlib.Path(__file__).resolve().parent;P=D/'private/osaka';P.mkdir(exist_ok=True)
ids=['0000369352','0000369358','0000009139','0000009337','0000538162','0000523872','0000384167','0000384524']
protocol=dict(source='Osaka city original HTML text; individual third-party exceptions still reviewed',ids=ids,max_pages=8,max_response_bytes=2*1024**2,delay_seconds=5,license_url='https://www.city.osaka.lg.jp/main/site_policy/0000000124.html',admitted_tokens=0)
f=D/'OSAKA_PILOT_PROTOCOL.json'
if f.exists():assert json.loads(f.read_text())==protocol
else:f.write_text(json.dumps(protocol,indent=2)+'\n')
receipts=[]
for ident in ids:
 path=P/f'{ident}.html.gz';rp=P/f'{ident}.receipt.json';url=f'https://www.city.osaka.lg.jp/kankyo/page/{ident}.html'
 if path.exists():
  b=gzip.decompress(path.read_bytes());r=json.loads(rp.read_text());assert hashlib.sha256(b).hexdigest()==r['sha256']
 else:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with urllib.request.urlopen(url,timeout=45)as response:b=response.read(protocol['max_response_bytes']+1);headers=dict(response.headers)
  assert len(b)<=protocol['max_response_bytes'];r=dict(id=ident,url=url,request_start_utc=start,response_end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),headers=headers)
  tmp=path.with_suffix('.pending');tmp.write_bytes(gzip.compress(b,mtime=0));os.replace(tmp,path);rp.write_text(json.dumps(r,indent=2)+'\n');time.sleep(5)
 receipts.append(r);print('Osaka acquired',ident,flush=True)
(D/'OSAKA_PILOT_ACQUISITION.json').write_text(json.dumps(dict(receipts=receipts,complete=True,admitted_tokens=0),indent=2)+'\n')
