"""Unabridged, unedited model text; token arrays/raw bytes remain in linked JSON."""
import json,pathlib
H=pathlib.Path(__file__).resolve().parent;V=H.parent

def main():
 out=['# 生成全文（無修正）\n','モデルの本文は空白・改行・反復を含めて保存。入力・token列・raw bytes・checkpoint対応は各JSONが正本。これは人間による独立評価ではない。\n']
 ids={c['id']:c.get('prompt',c.get('inputText',c.get('prefixText','')))for p in [V/'epoch1/content-dev.json',V/'response-data/final/active-dev.json']for c in json.loads(p.read_text())['cases']}
 def emit(label,row):
  out.append('\n### '+label+'\n');inp=row.get('prompt',row.get('input',row.get('prefix_text',ids.get(row.get('id'),''))))
  if inp:out.append('\n入力：\n\n'+inp+'\n')
  if 'reference'in row:out.append('\n原注釈：'+row['reference']+'\n')
  text=row.get('text');out.append('\nEOS='+str(row.get('eos'))+' / stop='+str(row.get('stopReason'))+'\n')
  if text is None:out.append('\n厳密UTF8として復号不能。rawBytesHexを参照。\n');return
  fence='`'*max(3,max((len(s)for s in __import__('re').findall(r'`+',text)),default=0)+1)
  out.append('\n'+fence+'text\n'+text+'\n'+fence+'\n')
 for name in ['initial','control','boundary','clip5']:
  out.append('\n## '+name+'\n');base=H/'evaluation'/(name+'.json');d=json.loads(base.read_text());out.append('\n[正本JSON](evaluation/'+base.name+')\n')
  for k in ['prose_dev','grounded36','legacy','context12']:
   for i,row in enumerate(d[k]):emit(k+'/'+str(i)+'/'+str(row.get('id')),row)
  for i,ep in enumerate(d['self_history']):
   for j,row in enumerate(ep['turns']):
    if 'text'in row:emit('self_history/'+str(i)+'/turn'+str(j+1),row)
  for suffix in ['human32','paragraphs']:
   p=H/'evaluation'/(name+'-'+suffix+'.json')
   if p.exists():
    for i,row in enumerate(json.loads(p.read_text())['cases']):emit(suffix+'/'+str(i)+'/'+str(row.get('id')),row)
 (H/'GENERATIONS.md').write_text(''.join(out))
if __name__=='__main__':main()
