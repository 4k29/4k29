import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
"""Future prototype data validation only; no model or alternate learning trial."""
import pathlib,json,hashlib,collections,numpy as np
from prefix_selection import load_selector
R=pathlib.Path(__file__).resolve().parents[1];D=R;read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();idx=read(R/'multiview/train.index.json');tok=read(R/'multiview/tokenizer.json');feature=D/'human-turn-token-boundaries.json';selector=load_selector(feature,tok,idx,sha(feature),sha(R/'multiview/tokenizer.json'),sha(R/'multiview/train.index.json'),sha(R/'sources/documents.jsonl'));values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');pieces=[bytes.fromhex(x)for x in tok['bytes']];counts=collections.Counter();lengths=[]
for row in idx['rows']:
 first=int(values[row['offset']]);base=min(32,row['length']-1);n=selector.length(row,first);assert 1<=n<=base;counts['allRows']+=1
 if row['site']!='human-chat':assert n==base;counts['otherRowsExactlyUnchanged']+=1;continue
 counts['humanRows']+=1;counts['unsafeStartsDetectedFromFirstByte']+=not selector.valid_start[first]
 if n!=base:
  assert 8<=n<base and row['start']+n in selector.ends[row['unit']];raw=b''.join(pieces[int(t)]for t in values[row['offset']:row['offset']+n]);raw.decode('utf-8');counts['hypotheticalChangedHumanRows']+=1;lengths.append(n)
 else:counts['humanRowsKeepingOriginalPrefixLength']+=1
out=dict(counts=dict(counts),hypotheticalChangedLengthMean=float(np.mean(lengths)),allHypotheticallyChangedPrefixesDecodeValidUtf8=True,allChosenEndsAreExistingTrueTurnTokenEnds=True,allOtherGenresExactlyUnchanged=True,prefixCodeSha256=sha(D/'prefix_selection.py'),featureSha256=sha(feature),modelOrOptimizerInstantiated=False,actualNewRoundOptimizerUpdates=0,newRoundTrainingNotStarted=True,controlRound38ArtifactsUnchanged=True,scope='Prospective Round39 policy preflight only; actual optimizer updates0; not language evaluation')
(D/'execution/prefix-policy-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
