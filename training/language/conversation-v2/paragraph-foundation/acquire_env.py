"""Finite, resumable official whitepaper acquisition; every body starts quarantined."""
import pathlib,sys,json,gzip,time,urllib.parse,urllib.robotparser,hashlib,datetime
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from discover import fetch,Links
D=pathlib.Path(__file__).resolve().parent;P=D/'private/discovery'
EDITIONS=['r03','r02','r01','h30','h28','h26','h24','h22']
def write(path,obj):
 path=pathlib.Path(path);tmp=path.with_suffix('.pending');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
def main():
 protocol=dict(editions=EDITIONS,max_pages=650,delay_seconds=5,parts=['01','02'],exclude='next-year measures part03, PDFs/images, CGI, external hosts',license='PDL1.0 for ministry-owned text only; third-party material excluded at curation',robots='Disallow /cgi-bin/',acquired_is_not_admitted=True)
 f=D/'ACQUISITION_PROTOCOL.json'
 if f.exists():assert json.loads(f.read_text())==protocol
 else:write(f,protocol)
 robots=urllib.robotparser.RobotFileParser();robots.parse(gzip.decompress((P/'env-robots.gz').read_bytes()).decode().splitlines());urls=[];indices=[]
 for edition in EDITIONS:
  index=f'https://www.env.go.jp/policy/hakusyo/{edition}/index.html';body,r=fetch('env-'+edition+'-index',index);assert r.get('status')==200,r
  links=Links();links.feed(body.decode('utf8'));paths=sorted({urllib.parse.urljoin(index,h.split('#')[0])for h in links.links if __import__('re').fullmatch(r'html/hj\d{2}0[12]\d{4}(?:_\d+)?\.html',h.split('#')[0])});indices.append(dict(edition=edition,receipt=r,pages=len(paths)));urls.extend(dict(edition=edition,url=u)for u in paths);time.sleep(5)
 # Interleave editions so a finite cap does not admit only the first year's style.
 ordered=[];groups={e:[r for r in urls if r['edition']==e]for e in EDITIONS}
 for i in range(max(map(len,groups.values()))):
  for e in EDITIONS:
   if i<len(groups[e]):ordered.append(groups[e][i])
 ordered=ordered[:protocol['max_pages']];write(D/'ENV_PAGE_SELECTION.json',dict(indices=indices,selected=ordered,admitted_tokens=0));receipts=[]
 for i,row in enumerate(ordered):
  url=row['url'];assert robots.can_fetch('4k29-paragraph-research/1.0',url);name='env-'+row['edition']+'-'+url.rsplit('/',1)[1].removesuffix('.html');body,r=fetch(name,url)
  receipts.append(dict(**row,cache_name=name,**{k:v for k,v in r.items()if k!='url'}));write(D/'ACQUISITION_STATUS.json',dict(processed=i+1,selected=len(ordered),successful=sum(r.get('status')==200 for r in receipts),complete=False,admitted_tokens=0,last_url=url))
  if r.get('status')in [403,429]:write(D/'ACQUISITION_STOP.json',r);break
  if r.get('status')!=200:write(D/'ACQUISITION_ERRORS.json',receipts[-1]);break
  assert urllib.parse.urlparse(r['final_url']).hostname=='www.env.go.jp'
  if(i+1)%20==0:print('acquired',i+1,'/',len(ordered),flush=True)
  time.sleep(protocol['delay_seconds'])
 write(D/'ACQUISITION_RECEIPTS.json',receipts);write(D/'ACQUISITION_STATUS.json',dict(processed=len(receipts),selected=len(ordered),successful=sum(r.get('status')==200 for r in receipts),complete=len(receipts)==len(ordered),admitted_tokens=0))
if __name__=='__main__':main()
