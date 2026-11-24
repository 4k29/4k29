"""Acquire licensed original caption annotations only; never images or models.
Archive remains quarantined. Dataset official TRAIN/validation/test partitions preserved.
"""
import pathlib,json,urllib.request,datetime,hashlib,os,shutil
D=pathlib.Path(__file__).resolve().parent;P=D/'private/stair';P.mkdir(exist_ok=True)
commit=json.loads((D/'private/stair-commit.txt').read_text())['sha'];entry=next(r for r in json.loads((D/'STAIR_REPO_FILES.json').read_text())['entries']if r['name']=='stair_captions_v1.2.tar.gz')
protocol=dict(repository='STAIR-Lab-CIT/STAIR-captions',commit=commit,archive_name=entry['name'],expected_bytes=entry['size'],expected_git_blob_sha1=entry['sha'],max_bytes=75*1024**2,min_free_before_download=1150*1024**2,license='CC BY4.0, publisher README; images not included in training permission',scope='Quarantined annotation archive only. Only original TRAIN records eligible for analysis; no TEST body opened. No dataset/machine-generated answers assumed human until source method verified.',optimizer_updates=0,admitted_tokens=0)
f=D/'STAIR_ACQUISITION_PROTOCOL.json'
if f.exists():assert json.loads(f.read_text())==protocol
else:f.write_text(json.dumps(protocol,indent=2)+'\n')
url=f'https://raw.githubusercontent.com/STAIR-Lab-CIT/STAIR-captions/{commit}/{entry["name"]}';path=P/entry['name'];rp=D/'STAIR_ARCHIVE_RECEIPT.json'
assert not path.exists(),'Existing archive must be verified and reused, never overwritten';assert shutil.disk_usage(D).free>=protocol['min_free_before_download'];start=datetime.datetime.now(datetime.timezone.utc).isoformat();tmp=path.with_suffix('.pending');size=0;h=hashlib.sha256();blob=hashlib.sha1(('blob '+str(entry['size'])+'\0').encode())
with urllib.request.urlopen(url,timeout=90)as r,tmp.open('wb')as out:
 headers={k:v for k,v in r.headers.items()if k.lower()not in {'set-cookie','cookie','authorization','proxy-authorization'}}
 while True:
  chunk=r.read(1024**2)
  if not chunk:break
  size+=len(chunk);assert size<=protocol['max_bytes'];out.write(chunk);h.update(chunk);blob.update(chunk)
 out.flush();os.fsync(out.fileno())
assert size==entry['size']and blob.hexdigest()==entry['sha'];os.replace(tmp,path);rp.write_text(json.dumps(dict(url=url,request_start_utc=start,response_end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bytes=size,sha256=h.hexdigest(),git_blob_sha1=blob.hexdigest(),commit=commit,headers=headers,admission='quarantined; rights/method/quality/split/token audit not complete'),indent=2)+'\n');print('STAIR downloaded verified bytes',size,flush=True)
