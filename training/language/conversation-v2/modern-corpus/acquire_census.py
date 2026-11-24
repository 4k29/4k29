"""Bounded pre2022 API census, private storage only; no TRAIN admission."""
import pathlib,json,gzip,hashlib,urllib.request,datetime,time,os,shutil
D=pathlib.Path(__file__).resolve().parent;P=D/'private/census';P.mkdir(exist_ok=True)
protocol=dict(max_pages=27,per_page=100,max_posts=2700,max_response_bytes=8*1024**2,max_total_raw_bytes=100*1024**2,delay_seconds=10,before='2022-01-01T00:00:00',source='official public WordPress posts API',rights='CC-BY3 for GV-created material, individual exceptions quarantined',admission='none until independent quality/rights/split checks',no_restricted_users_endpoint=True)
proto=D/'CENSUS_PROTOCOL.json'
if proto.exists():assert json.loads(proto.read_text())==protocol
else:proto.write_text(json.dumps(protocol,indent=2)+'\n')
receipts=[];seen=set();rawtotal=0;posts=0
for page in range(1,protocol['max_pages']+1):
 assert shutil.disk_usage(D).free>1024**3,'Protect storage reserve before further acquisition'
 path=P/f'{page:03d}.json.gz';rp=P/f'{page:03d}.receipt.json';url=f"https://jp.globalvoices.org/wp-json/wp/v2/posts?per_page=100&page={page}&before=2022-01-01T00:00:00&_fields=id,date_gmt,modified_gmt,link,title,content,categories,tags,author"
 if path.exists():
  b=gzip.decompress(path.read_bytes());r=json.loads(rp.read_text());assert hashlib.sha256(b).hexdigest()==r['sha256']
 else:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with urllib.request.urlopen(url,timeout=45)as response:b=response.read(protocol['max_response_bytes']+1);headers=dict(response.headers)
  assert len(b)<=protocol['max_response_bytes'];assert rawtotal+len(b)<=protocol['max_total_raw_bytes'];r=dict(page=page,url=url,request_start_utc=start,response_end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(b).hexdigest(),raw_bytes=len(b),headers=headers)
  tmp=path.with_suffix('.pending');tmp.write_bytes(gzip.compress(b,mtime=0));os.replace(tmp,path);rp.write_text(json.dumps(r,indent=2)+'\n');time.sleep(protocol['delay_seconds'])
 rows=json.loads(b);assert isinstance(rows,list)and len(rows)<=100
 for post in rows:assert post['id']not in seen,'Duplicate across census pages; stop rather than assume complete stable pagination';seen.add(post['id'])
 rawtotal+=len(b);posts+=len(rows);receipts.append(r);status=dict(pages=len(receipts),posts=posts,raw_bytes=rawtotal,admitted_tokens=0,optimizer_updates=0,receipts=receipts,complete=False)
 (D/'CENSUS_STATUS.json').write_text(json.dumps(status,indent=2)+'\n');print('census',page,posts,rawtotal,flush=True)
 if len(rows)<100:break
status['complete']=True;(D/'CENSUS_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
