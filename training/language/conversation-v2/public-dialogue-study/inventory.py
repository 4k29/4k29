import pathlib,json,collections,hashlib
P=pathlib.Path(__file__).resolve().parent;S=P/'asdc';counts={};records=[]
for p in list(sorted((S/'data/main/dialog/json').glob('*.json')))+list(sorted((S/'data/vanilla').glob('*.jsonl')))+list(sorted((S/'data/supplemental/utterances').glob('*.jsonl'))):
 rs=[json.loads(p.read_text())]if p.suffix=='.json'else map(json.loads,p.open());c=collections.Counter()
 for r in rs:
  part=r.get('purpose',r.get('meta',{}).get('purpose'));c['records']+=1;c['partition_'+str(part)]+=1
  if part not in ['train','dev']:continue
  us=r['utterances'];names=[('agent'if u['name'].startswith('operator')else'user'if u['name'].startswith('customer')else u['name'])for u in us];c['turns_'+str(len(us))]+=1;c['pattern_'+'-'.join(names[:4])]+=1
  for i,name in enumerate(names):
   if name=='agent'and i>0 and names[i-1]=='user':c['agent_after_user_targets']+=1
  records.append(dict(id=r.get('docid',r.get('meta',{}).get('id')),partition=part,file=str(p.relative_to(S)),meta=r.get('meta',{}),utterances=[dict(role=name,text=u.get('text_fixed',u['text']),original_name=u['name'],publisher_fixed='text_fixed'in u)for name,u in zip(names,us)]))
 counts[str(p.relative_to(S))]=dict(c)
(P/'PRIVATE').mkdir(exist_ok=True);(P/'PRIVATE/RECORDS.json').write_text(json.dumps(records,ensure_ascii=False,separators=(',',':')));(P/'INVENTORY.json').write_text(json.dumps(counts,indent=2)+'\n');print('non-test records',len(records));print(json.dumps({f:{k:v for k,v in c.items()if k in ['records','agent_after_user_targets']or k.startswith('pattern_')}for f,c in counts.items()if not f.startswith('data/main')},ensure_ascii=False))
