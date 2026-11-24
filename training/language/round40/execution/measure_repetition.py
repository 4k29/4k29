"""Post-hoc raw-generation diagnostics; never replace fixed language gates."""
import pathlib,json,hashlib
E=pathlib.Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
models={};raw={}
for name in ['old','new']:
 p=E/f'{name}-validation.json';raw[name]=read(p)['rows'];rows=[]
 for x in raw[name]:
  tokens=[t for t in x['tokens'] if t>=6];seen=set();repeated=0
  for i in range(3,len(tokens)):
   gram=tuple(tokens[i-3:i+1]);repeated+=gram in seen;seen.add(gram)
  rows.append(dict(id=x['id'],nonSpecialGeneratedTokens=len(tokens),eligibleFourgrams=max(0,len(tokens)-3),repeatedFourgrams=repeated,eos=x['eos']))
 count=sum(x['eligibleFourgrams'] for x in rows);reps=sum(x['repeatedFourgrams'] for x in rows)
 models[name]=dict(generationSha256=sha(p),rows=rows,repeatedFourgrams=reps,eligibleFourgrams=count,repeatedFourgramFraction=reps/count,eosOutputs=sum(x['eos'] for x in rows))
same=[a['id'] for a,b in zip(raw['old'],raw['new'],strict=True) if a['tokens']==b['tokens'] and a['text']==b['text']]
out=dict(models=models,identicalCompleteOutputs=same,postHocDevelopmentOnly=True,gateDefinitionUnchanged=True,definition='Generated non-special token stream only, excludes opening. For each overlapping4gram after the first3tokens count if identical tuple occurred earlier, including overlaps. No semantic or unseen-generalization claim.')
(E/'repetition-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(models={k:{q:v[q] for q in ['repeatedFourgramFraction','eosOutputs']} for k,v in models.items()},identicalCompleteOutputs=same)))
