import json,pathlib
r=pathlib.Path(__file__).resolve().parents[1];logs=r/'execution/train.log'
rows=[]
if logs.exists():
 for line in logs.read_text().splitlines():
  try:rows.append(json.loads(line))
  except json.JSONDecodeError:pass
v=[x for x in rows if 'validation' in x];last=rows[-1] if rows else {}
print(json.dumps(dict(lastLoggedStep=last.get('step',last.get('completedUpdates',0)),lastEvent=last.get('event','validation' if v else 'initializing'),lastValidatedStep=v[-1]['step'] if v else None,nll=v[-1]['validation']['nllPerUtf8Byte'] if v else None,completedRun=last.get('event')=='finished')))
