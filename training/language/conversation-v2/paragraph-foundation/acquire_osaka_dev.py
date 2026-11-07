"""Bounded supplementary source-held-out DEV candidates. Never TRAIN."""
import time,json
from discover import fetch,D
IDS=['0000520539','0000678958','0000644680','0000471631','0000541069','0000052392']
rows=[]
for ident in IDS:
 body,r=fetch('osaka-dev-'+ident,'https://www.city.osaka.lg.jp/kankyo/page/'+ident+'.html');rows.append(r)
 if r['status']!=200:break
 time.sleep(5)
(D/'OSAKA_DEV_ACQUISITION.json').write_text(json.dumps(dict(scope='DEV candidate only; no TRAIN; no approval by acquisition',pages=rows),indent=2)+'\n')
