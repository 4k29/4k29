"""Readable full outputs; raw JSON byte payloads/tokens remain canonical."""
from common import *
lines=['# 無修正の自由生成全文','', '全語彙greedy。保存JSONがtoken列/raw bytes/停止理由の正本。assistantによる読解は正式な母語話者評価ではない。','']
for f in sorted((P/'evaluation').glob('*.json')):
 if f.name.endswith(('-summary.json','-reading.json')):continue
 d=read(f);rows=d.get('cases',[])
 if 'prose_dev'in d:rows=[dict(panel='prose24',**r)for r in d['prose_dev']]+[dict(panel='grounded36',**r)for r in d['grounded36']]+d['legacy']+[dict(panel='context12',**r)for r in d['context12']]
 lines+=['## '+f.name,'']
 for r in rows:
  text=r.get('text',r.get('decodedText',r.get('textWithReplacement','')))
  if not text:
   # byte_payload uses utf8 text; inspect raw schema if no ordinary field present.
   for key in ['textUtf8','textUtf8Replacement','decoded']:
    if key in r:text=r[key];break
  lines+=['### '+str(r.get('panel',''))+' '+str(r.get('id','')), '', '入力token: '+json.dumps(r.get('prefix',[])), '', '終了: '+str(r.get('stopReason'))+' / EOS='+str(r.get('eos')), '', '~~~text',text,'~~~','']
 if 'self_history'in d:
  for e in d['self_history']:
   lines+=['### 自己履歴 '+e['id'],'']
   for i,r in enumerate(e['turns']):lines+=['turn '+str(i+1)+' prefix='+json.dumps(r.get('prefix')),'', '~~~text',str(r.get('text',r.get('textUtf8Replacement',r))), '~~~','']
(P/'GENERATIONS.md').write_text('\n'.join(lines)+'\n')
