"""Retain unedited full own-TRAIN rollouts; invalid UTF8 stays raw bytes, never repaired."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tok=read(R/'multiview/tokenizer.json');trace=R/'continue-10000/training-rollouts.jsonl';rows=[]
def decode(ids):
 raw=b''.join(bytes.fromhex(tok['bytes'][i]) for i in ids)
 try:text=raw.decode('utf8');valid=True
 except UnicodeDecodeError:text=None;valid=False
 return dict(tokens=ids,rawUtf8Hex=raw.hex(),text=text,validUtf8=valid,nonSpecialOrBoundaryOnly=all(i>=6 or i in [1,2] for i in ids))
for line in trace.read_text().splitlines():
 row=json.loads(line);n=row['prefixLength'];rows.append(dict(step=row['step'],sourceRow=row['sourceRow'],prefix=decode(row['tokens'][:n]),generated=decode(row['tokens'][n:]),loss=row['loss'],negativePositions=row['negativePositions'],generatedTokens=row['generatedTokens']))
assert len(rows)==1000 and [r['step'] for r in rows]==list(range(10,10001,10))
record=dict(trainingTraceSha256=sha(trace),tokenizerSha256=sha(R/'multiview/tokenizer.json'),trainingOnly=True,evaluation=False,additionalOptimizerUpdates=0,generatedUsedAsPositiveTeacher=False,noOutputRepair=True,rows=rows)
(E/'training-rollouts-full.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(trainingRollouts=len(rows),validUtf8Generated=sum(r['generated']['validUtf8'] for r in rows),negativePositions=sum(r['negativePositions'] for r in rows))))
