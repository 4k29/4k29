"""TRAIN-only prospective end-target coverage; no model, optimizer, or heldout."""
import pathlib,json,collections,bisect,hashlib,numpy as np
R=pathlib.Path('/workspace/4k29/training/language/round34');E=pathlib.Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
info=load(R/'multiview/train.index.json');feature=load(R/'human-turn-token-boundaries.json');tok=load(R/'multiview/tokenizer.json');values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r')
docs={d['id']:d for d in info['documents']};counts=collections.defaultdict(collections.Counter);eligible=collections.defaultdict(set);targeted=collections.defaultdict(set)
assert bytes.fromhex(tok['bytes'][16])==b'\n'
for row in info['rows']:
 if row['site']!='human-chat':continue
 d=docs[row['unit']];assert row['offset']==d['offset']+row['start']
 ends=feature['boundariesByUnit'][row['unit']];c=counts[str(row['variant'])];c['rows']+=1;c['originalNonmaskedTargets']+=row['length']-row['prefixLength']
 # Separator token is at absolute unit index end-1. It is predicted at
 # row-local logit position end-start-2, before seeing that separator.
 lower=row['start']+row['prefixLength']+1;upper=row['start']+row['length']
 n=0
 for end in ends[bisect.bisect_left(ends,lower):bisect.bisect_right(ends,upper)]:
  local=end-row['start']-2
  assert row['prefixLength']-1<=local<row['length']-1
  absolute=d['offset']+end-1
  assert absolute==row['offset']+local+1
  targeted[row['unit']].add(end)
  if int(values[absolute])!=16:continue
  n+=1;eligible[row['unit']].add(end)
 c['eligibleAuxiliaryEosTargets']+=n;c['rowsWithEligibleBoundary']+=bool(n)
for variant,c in counts.items():
 expected={u:{end for end in ends if int(values[docs[u]['offset']+end-1])==16}for u,ends in feature['boundariesByUnit'].items()if str(docs[u]['variant'])==variant}
 assert all(eligible[u]==ends for u,ends in expected.items())
 c['allOriginalStandaloneNewlineBoundaryPositionsCovered']=True
 c['eligiblePerOriginalHumanTarget']=c['eligibleAuxiliaryEosTargets']/c['originalNonmaskedTargets']
 c['eligibleRowsFraction']=c['rowsWithEligibleBoundary']/c['rows']
 c['duplicateEligibleTargetsFromOverlap']=c['eligibleAuxiliaryEosTargets']-sum(map(len,expected.values()))
 assert c['duplicateEligibleTargetsFromOverlap']==0
out=dict(counts={k:dict(v)for k,v in counts.items()},trainIndexSha256=sha(R/'multiview/train.index.json'),featureSha256=sha(R/'human-turn-token-boundaries.json'),codeSha256=sha(pathlib.Path(__file__)),noHeldoutTextOrModelOpened=True,noRngOrOptimizerUsed=True,noRound34FilesModified=True,actualNewRoundUpdates=0,notSamplingFrequencyOrLanguageEvidence=True)
(E/'eligible-end-row-counts.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
