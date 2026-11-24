import pathlib,json,hashlib,tarfile,io,gzip,base64
P=pathlib.Path(__file__).resolve().parent;OUT=pathlib.Path('/workspace/scratch/absorption/publish');OUT.mkdir(exist_ok=True);files={p.name:p.read_bytes()for p in P.iterdir()if p.is_file()and p.name not in ['PACKAGE.json']};buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w')as t:
 for n,b in sorted(files.items()):
  x=tarfile.TarInfo(n);x.size=len(b);x.mtime=0;t.addfile(x,io.BytesIO(b))
b=gzip.compress(buf.getvalue(),mtime=0);parts=[]
for i in range(0,len(b),192*1024):
 v=b[i:i+192*1024];n=f'part-{i//(192*1024):03d}.bin';(OUT/(n+'.b64')).write_text(base64.b64encode(v).decode());parts.append(dict(path=n,bytes=len(v),sha256=hashlib.sha256(v).hexdigest()))
m=dict(purpose='Only bounded-admitted licensed research prose and public metadata; no raw held/private text; source acquisition0',sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),parts=parts,files={n:hashlib.sha256(v).hexdigest()for n,v in files.items()});(OUT/'SOURCE_BUNDLE_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n');print('parts',len(parts),'bytes',len(b),'files',len(files),'SHA',m['sha256'])
