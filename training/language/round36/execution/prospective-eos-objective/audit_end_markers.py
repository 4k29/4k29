"""Untrained future hypothesis: count existing human TRAIN end markers only."""
import pathlib,json,collections,hashlib,numpy as np
R=pathlib.Path('/workspace/4k29/training/language/round34');D=pathlib.Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();index=read(R/'multiview/train.index.json');tok=read(R/'multiview/tokenizer.json');feature=read(R/'human-turn-token-boundaries.json');values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');newline={i for i,b in enumerate(tok['bytes'])if i>=6 and bytes.fromhex(b)==b'\n'};counts=collections.defaultdict(collections.Counter)
for doc in index['documents']:
 if doc['site']!='human-chat':continue
 c=counts[str(doc['variant'])];c['units']+=1;c['originalTargetsIncludingDialogEos']+=doc['length']-1;assert int(values[doc['offset']+doc['length']-1])==2;c['originalTerminalEosTargets']+=1
 for end in feature['boundariesByUnit'][doc['id']]:
  c['trueInteriorAfterSeparatorTokenEnds']+=1;token=int(values[doc['offset']+end-1]);c['standaloneNewlineTargetsAtTrueEnd']+=token in newline;c['tokenContainsMoreThanOnlyNewline']+=token not in newline
out=dict(sourceRound=34,sourceFeatureSha256=sha(R/'human-turn-token-boundaries.json'),trainIndexSha256=sha(R/'multiview/train.index.json'),tokenizerSha256=sha(R/'multiview/tokenizer.json'),newlineTokenIds=sorted(newline),counts={k:dict(v)for k,v in counts.items()},noHeldoutTextOrModelOpened=True,noTrainingDataOrLabelsChanged=True,noAlternativeLearningConditionExecuted=True,actualNewRoundOptimizerUpdates=0,currentRound34LearningConditionsUnchanged=True,notEvidenceThatEndSupervisionImprovesMeaning=True)
(D/'end-marker-counts.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
