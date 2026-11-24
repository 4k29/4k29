"""Check same prefix/observed first sentence has unchanged component judgments."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];read=lambda p:json.loads(p.read_text());seen={};matches=[];keys=['grammar','meaning','connection','repetition','breaks','sentenceClosed']
for round_name in ['round39','round40','round41','round42','round43']:
 E=R.parent/round_name/'execution'
 for state,gp,mp in [('selected','new-validation.json','new-manual.json'),('terminal','terminal-state-diagnostic/original17-python.json','terminal-state-diagnostic/original17-manual.json')]:
  g,m=read(E/gp),read(E/mp)
  for x,y in zip(g['rows'],m['rows'],strict=True):
   assert x['id']==y['id'];stop=x['text'].find('。')
   if stop<0:continue
   first=x['prefix']+x['text'][:stop+1];scores=[y[k]for k in keys];h=hashlib.sha256(first.encode()).hexdigest();loc=round_name+'/'+state+'/'+x['id']
   if h in seen:assert seen[h][0]==scores,(loc,seen[h]);matches.append(dict(location=loc,sameAs=seen[h][1],firstSentenceSha256=h))
   else:seen[h]=(scores,loc)
(R/'execution/first-sentence-consistency.json').write_text(json.dumps(dict(sameObservedFirstSentenceComponentsAlwaysMatch=True,matches=matches,uniqueObservedFullFirstSentences=len(seen),noNewJudgmentsAssigned=True),indent=2)+'\n');print('Matching first-sentence component scores verified',len(matches))
