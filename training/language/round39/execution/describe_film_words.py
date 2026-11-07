"""Posthoc literal word count, not a topic classifier or a new gate."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];read=lambda p:json.loads(p.read_text());out=[]
for round_name in ['round38','round39']:
 E=R.parent/round_name/'execution'
 for state in ['selected','terminal']:
  files=[E/p for p in ['daily-new-python.json','content-native-dev/new-python.json','fixed-source-mrmp-dev/new-python.json']]if state=='selected'else[E/'terminal-state-diagnostic'/f'{g}-python.json'for g in ['daily12','native8','mrmp5']];rows=[x for p in files for x in read(p)['rows']];assert len(rows)==25;out.append(dict(round=round_name,state=state,generatedTextsContainingLiteralEiga=sum('映画'in x['text']for x in rows),ids=[x['id']for x in rows if '映画'in x['text']],scope=25,generationSha256=[hashlib.sha256(p.read_bytes()).hexdigest()for p in files]))
(R/'execution/film-word-description.json').write_text(json.dumps(dict(posthoc=True,literalWord='映画',notTopicClassifier=True,notNewGate=True,notSemanticSuccess=True,states=out,additionalOptimizerUpdates=0),ensure_ascii=False,indent=2)+'\n');print([(r['round'],r['state'],r['generatedTextsContainingLiteralEiga'])for r in out])
