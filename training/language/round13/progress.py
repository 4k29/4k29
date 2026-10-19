"""Read-only monitor: report logged completed optimizer updates, never budgets."""
import json,pathlib
root=pathlib.Path(__file__).resolve().parent.parent;out={}
for n in [13,14,15,16]:
 p=root/f'round{n}/execution/train.log';rows=[]
 if p.exists():
  for line in p.read_text().splitlines():
   try:rows.append(json.loads(line))
   except json.JSONDecodeError:pass
 if rows:
  last=rows[-1];step=last.get('completedUpdates',last.get('step',0));values=[r for r in rows if 'validation' in r];out[str(n)]={'confirmedUpdates':step,'completedRun':last.get('event')=='finished','developmentNll':values[-1]['validation']['nllPerUtf8Byte'] if values else None}
 else:out[str(n)]={'confirmedUpdates':0,'completedRun':False,'state':'initial_measurement' if (root/f'round{n}/continue-10000/config.json').exists() else 'not_started'}
print(json.dumps(out))
