import os
import pathlib,json,hashlib,time,urllib.parse,sys,re
from metadata import api,get
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'));P=pathlib.Path(__file__).resolve().parents[1]
def snapshot(site,rows,folder):
 out=C/folder;out.mkdir(exist_ok=True);results=[]
 for r in rows:
  f=out/(site+'-'+str(r['pageid'])+'.json')
  if f.exists():results.append(json.loads(f.read_text()));continue
  try:
   d=api(site,action='query',prop='revisions',rvprop='ids|timestamp|user|comment|content',rvslots='main',rvlimit=1,rvstart='2021-12-31T23:59:59Z',rvdir='older',pageids=r['pageid']);page=list(d['query']['pages'].values())[0];rev=page.get('revisions',[])
   obj=dict(site=site,pageid=r['pageid'],title=r['title'],retrieved_UTC=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),fixed_before='2022-01-01',revision=rev[0]if rev else None,request_URL='https://'+site+'/w/api.php?'+urllib.parse.urlencode(dict(action='query',prop='revisions',pageids=r['pageid'],rvstart='2021-12-31T23:59:59Z',rvdir='older',rvlimit=1)),license='CC BY-SA 4.0 per current site policy; attribution/history preserved')
   f.write_text(json.dumps(obj,ensure_ascii=False));results.append(obj);time.sleep(.3)
  except Exception as e:
   (out/'ERRORS.jsonl').open('a').write(json.dumps(dict(site=site,id=r['pageid'],error=str(e)))+'\n');print('fetch stopped',site,r['pageid'],str(e),flush=True);break
 return results
if __name__=='__main__':
 b=json.loads((C/'ja.wikibooks.org.titles.json').read_text());v=json.loads((C/'ja.wikivoyage.org.titles.json').read_text());chosen={}
 chosen['ja.wikibooks.org']=[r for r in b if r['title']in['中学校家庭/肉の調理','中学校家庭/衣服の手入れ','中学校家庭/食品の保存と食中毒の防止','中学校家庭/調理実習での注意事項','中学校家庭/どうして食事をするのだろう','中学校家庭/日常食の調理と地域の食文化']]
 chosen['ja.wikivoyage.org']=[r for r in v if r['title']in['キャンプ','温泉','健康を維持する','鉄道旅行']]
 protocol=dict(selection_before_text_acquisition=True,reserved_family={'jawikibooks':['中学校家庭'],'jawikivoyage':[r['title']for r in chosen['ja.wikivoyage.org']]},pages=chosen,metadata_SHA={s:hashlib.sha256((C/(s+'.titles.json')).read_bytes()).hexdigest()for s in chosen},cutoff='2021-12-31T23:59:59Z',fallback='No replacement after model predictions; missing old revision excluded; all eligible frozen dev paragraphs by predeclared hash order')
 (P/'DEV_RESERVED_FAMILIES.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
 for s,rr in chosen.items():
  out=snapshot(s,rr,'dev-raw');print(s,[(r['title'],r['revision']['revid']if r['revision']else None)for r in out])
