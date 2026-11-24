"""Fixed late-position diagnostic; token fourgram repeats never imply meaning."""
import pathlib,json,hashlib,sys
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pre='--before-training' in sys.argv
paths={'daily-control':R.parent/'round29/execution/daily-old-python.json'} if pre else {n:E/f'daily-{n}-python.json' for n in ['old','new']}
models={}
for name,path in paths.items():
 rows=[];totals=[[0,0] for _ in range(3)]
 for row in read(path)['rows']:
  t=row['tokens'];counts=[[0,0] for _ in range(3)]
  for i in range(3,len(t)):
   g=t[i-3:i+1]
   if min(g)<6:continue
   b=min(i//64,2);counts[b][0]+=1
   counts[b][1]+=any(t[j-3:j+1]==g for j in range(max(3,i-64),i))
  for a,b in zip(totals,counts):a[0]+=b[0];a[1]+=b[1]
  rows.append(dict(id=row['id'],buckets=counts))
 models[name]=dict(generationSha256=sha(path),rows=rows,buckets=[dict(generatedPositions=f'{i*64+1}-{(i+1)*64}',eligible=a,repeated=b,fraction=b/a if a else None) for i,(a,b) in enumerate(totals)])
out=dict(models=models,definition='Full raw generated token stream only; exclude gram containing special IDs<6, count identical prior fourgram ending within64 positions. Three generated-position ranges, no compression or prefix inclusion. Teacher-forced TRAIN negative construction separately verified.',exposedDevelopmentOnly=True,semanticScore=False,gateChanged=False,usedForSelection=False)
(E/('pretraining-late-repeat.json' if pre else 'late-repeat-comparison.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v['buckets'] for k,v in models.items()}))
