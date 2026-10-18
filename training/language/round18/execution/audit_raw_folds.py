"""Broader raw-fold overlap audit; no TEST scoring, generation or optimization."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parts={x['document']:x['partition'] for x in read(R.parent/'round10/split.json')['assignments']};old=[json.loads(l) for l in (R.parent/'round10/documents.jsonl').read_text().splitlines()];new=[json.loads(l) for l in (R/'sources/documents.jsonl').read_text().splitlines()];train=[x for x in new if x['partition']=='train'];held=[dict(x,partition=parts[x['id']]) for x in old if parts[x['id']]!='train']+[x for x in new if x['partition']=='reserved'];wanted={d['text'][i:i+64] for d in train for i in range(len(d['text'])-63)};matches=[]
for d in held:
 found={d['text'][i:i+64] for i in range(max(0,len(d['text'])-63)) if d['text'][i:i+64] in wanted}
 for t in found:
  matches.append({'heldDocument':d['id'],'heldPartition':d['partition'],'trainDocuments':[x['id'] for x in train if t in x['text']],'spanCharacters':64,'spanSha256':hashlib.sha256(t.encode()).hexdigest()})
record={'scope':'All existing raw non-TRAIN folds including development/quarantine, plus new reserved documents; not only encoded units.','spanCharacters':64,'heldDocuments':len(held),'newTrainDocuments':len(train),'matches':matches,'testTextReadForDuplicateAudit':True,'testScoredOrGenerated':False,'additionalOptimizerUpdates':0,'sourceDocumentsSha256':sha(R/'sources/documents.jsonl'),'oldDocumentsSha256':sha(R.parent/'round10/documents.jsonl'),'oldSplitSha256':sha(R.parent/'round10/split.json'),'existingShortOverlapNotRemoved':True};(R/'execution/raw-fold-overlap-audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'heldDocuments':len(held),'matches':len(matches),'matchedPartitions':sorted({x['heldPartition'] for x in matches})}));assert not matches,'Review actual overlap before claiming clean added corpus'
