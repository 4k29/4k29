"""Compact progress from actual optimizer logs, with no test inspection."""
import argparse,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--run',default='raw-million');args=parser.parse_args()
rows=[]
for line in (ROOT/(args.run+'-log.jsonl')).read_text().splitlines():
 try:
  row=json.loads(line)
  if 'step' in row:rows.append(row)
 except json.JSONDecodeError:pass
last=rows[-1];evaluated=[r for r in rows if 'validation' in r];best=min(evaluated,key=lambda r:r['validation']['nllPerUtf8Byte'])
speeds=[(b['elapsedSeconds']-a['elapsedSeconds'])/(b['step']-a['step']) for a,b in zip(rows[-6:-1],rows[-5:]) if b['step']>a['step']]
print(json.dumps(dict(run=args.run,lastCompletedLoggedUpdate=last['step'],elapsedSeconds=last['elapsedSeconds'],lastValidationStep=evaluated[-1]['step'],lastValidationNllPerUtf8Byte=evaluated[-1]['validation']['nllPerUtf8Byte'],bestValidationStep=best['step'],bestValidationNllPerUtf8Byte=best['validation']['nllPerUtf8Byte'],recentSecondsPerUpdate=sum(speeds)/len(speeds) if speeds else None,updatesRemaining=10000-last['step'],counter='Last flushed log count; atomic optimizer checkpoint may be earlier. Final report uses exact completedRun count.')))
