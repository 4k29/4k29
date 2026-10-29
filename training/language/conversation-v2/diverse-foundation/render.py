"""Full raw generation artifact, no sentence repair, sampling selection or omissions."""
import re
from common import *
tok=read(V/'data/tokenizer.json');pieces=[bytes.fromhex(x)for x in tok['bytes']]
lines=['# 無修正の全語彙greedy生成全文','原文参照と生成文は別。token列・raw bytes・EOS等の厳密な原本は対応JSON。invalid UTF8は補修しない。全件露出済みDEV/診断であり独立TESTではない。']
def emit(c,label):
 lines.extend(['',f"## {label} / {c.get('panel','')} / {c.get('id','')}"])
 prefix=c.get('prefix',[]);raw=b''.join(pieces[t]for t in prefix if t>=6)
 try:text=raw.decode('utf8','strict')
 except UnicodeError:text='PREFIX raw bytes hex: '+raw.hex()
 lines.extend(['入力（特殊tokenはJSON参照）：','````text',text,'````','生成全文：','````text',c.get('text')if c.get('text')is not None else'INVALID UTF8; rawBytesHex='+c.get('rawBytesHex',''),'````',f"EOS={c.get('eos')}, stop={c.get('stopReason')}, token_count={len(c.get('tokensIncludingEos',[]))}"])
for p in sorted((D/'evaluation').glob('*.json')):
 if p.name.endswith('-summary.json'):continue
 for c in read(p)['cases']:emit(c,p.stem)
for p in sorted((D/'panels').glob('*.json'))if(D/'panels').exists()else[]:
 if p.name.endswith('-summary.json'):continue
 r=read(p)
 for key in ['legacy','grounded36','context12']:
  for c in r[key]:emit(c,p.stem+'/'+key)
 for e in r['self_history']:
  for i,c in enumerate(e['turns']):emit(dict(id=e['id']+':turn'+str(i),**c),p.stem+'/self_history')
for folder in ['sampling','daily-prose']:
 for p in sorted((D/folder).glob('*.json'))if(D/folder).exists()else[]:
  for c in read(p)['cases']:emit(c,p.stem+'/'+folder)
(D/'GENERATIONS.md').write_text('\n'.join(lines)+'\n')
