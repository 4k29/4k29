"""Describe paired saved TRAIN negative rollouts; no model forward, positive target or semantic grade."""
import pathlib,json,hashlib,collections
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round36'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pieces=read(R/'multiview/tokenizer.json')['bytes']
def decode(tokens):return b''.join(bytes.fromhex(pieces[i])for i in tokens if i>=6).decode('utf-8',errors='strict')
paths=[P/'execution/retained-paired-1000/training-rollouts.jsonl',E/'retained-paired-1000/training-rollouts.jsonl']
a,b=([json.loads(s)for s in p.read_text().splitlines()]for p in paths);assert len(a)==len(b)==100
stats={};rows=[];lines=['# Paired actual1000 TRAIN negative rollouts','','Same100 scheduled calls and source prefixes, max64. These are evolving TRAIN states, not frozen final models, fixed192 DEV outputs, semantic grades, heldout evidence or independent100 samples. No generated text is used as a positive target. Full texts decoded directly from saved token IDs; no repair.','']
for label,items in [('retainedNewlineCeRound36',a),('excludedNewlineCeRound37',b)]:
 groups=collections.defaultdict(lambda:dict(calls=0,generatedTokens=0,negativePositions=0,eosCalls=0,max64Calls=0))
 for x in items:
  for key in ['all',x['sourceRow']['site']]:
   z=groups[key];z['calls']+=1;z['generatedTokens']+=x['generatedTokens'];z['negativePositions']+=x['negativePositions'];z['eosCalls']+=int(x['tokens'][-1]==2);z['max64Calls']+=int(x['generatedTokens']==64)
 stats[label]=dict(groups)
for x,y in zip(a,b,strict=True):
 assert x['step']==y['step']and x['sourceRow']==y['sourceRow']and x['prefixLength']==y['prefixLength']
 n=x['prefixLength'];assert x['tokens'][:n]==y['tokens'][:n]
 row=dict(step=x['step'],sourceRow=x['sourceRow'],prefixTokens=x['tokens'][:n],prefix=decode(x['tokens'][:n]),oldGeneratedTokens=x['tokens'][n:],newGeneratedTokens=y['tokens'][n:],oldText=decode(x['tokens'][n:]),newText=decode(y['tokens'][n:]))
 rows.append(row);lines.extend([f"## Actual step {x['step']} / {x['sourceRow']['site']}",'','Prefix:','```text',row['prefix'],'```','R36:','```text',row['oldText'],'```','R37:','```text',row['newText'],'```',''])
out=dict(actualSnapshotUpdates=1000,rolloutCallsEach=100,sourceLogSha256=[sha(p)for p in paths],sameSourceRowsAndPrefixTokenIds=True,statistics=stats,rows=rows,notSemanticOrGeneralizationEvidence=True,generatedTextNeverPositiveTarget=True,noModelForward=True,additionalOptimizerUpdates=0,codeSha256=sha(pathlib.Path(__file__)))
(E/'paired-train-rollouts-1000.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(E/'PAIRED_TRAIN_ROLLOUTS_1000.md').write_text('\n'.join(lines)+'\n');print(json.dumps(stats))
