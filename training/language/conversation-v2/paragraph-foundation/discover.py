"""Bounded official-source discovery. No source is admitted by fetching it."""
import pathlib, urllib.request, urllib.error, datetime, hashlib, json, gzip, time
from html.parser import HTMLParser
D=pathlib.Path(__file__).resolve().parent
P=D/'private/discovery';P.mkdir(parents=True,exist_ok=True)
URLS={
 'env-robots':'https://www.env.go.jp/robots.txt',
 'env-whitepapers':'https://www.env.go.jp/policy/hakusyo/index.html',
 'wikinews-license':'https://ja.wikinews.org/wiki/Wikinews:%E8%91%97%E4%BD%9C%E6%A8%A9',
}
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   a=dict(attrs)
   if a.get('href'):self.links.append(a['href'])
def fetch(name,url):
 path=P/(name+'.gz');receipt=P/(name+'.json')
 if path.exists():
  body=gzip.decompress(path.read_bytes());r=json.loads(receipt.read_text());assert hashlib.sha256(body).hexdigest()==r['sha256'];return body,r
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  request=urllib.request.Request(url,headers={'User-Agent':'4k29-paragraph-research/1.0'})
  with urllib.request.urlopen(request,timeout=40)as response:
   body=response.read(3*1024**2+1);assert len(body)<=3*1024**2
   r=dict(url=url,status=response.status,final_url=response.url,started_utc=start,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),headers={k:v for k,v in response.headers.items()if k.lower()in ['content-type','last-modified','etag','date']})
  path.write_bytes(gzip.compress(body,mtime=0));receipt.write_text(json.dumps(r,indent=2)+'\n');return body,r
 except urllib.error.HTTPError as error:
  r=dict(url=url,status=error.code,started_utc=start,error=str(error),admitted_tokens=0);receipt.write_text(json.dumps(r,indent=2)+'\n');return b'',r
def main():
 rows=[]
 for name,url in URLS.items():
  b,r=fetch(name,url);p=Links();p.feed(b.decode('utf8',errors='replace'));r['links']=p.links;r['admitted_tokens']=0;rows.append(r);print(name,r.get('status'),len(b),flush=True);time.sleep(3)
 (D/'DISCOVERY.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
