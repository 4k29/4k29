"""Descriptive TRAIN-only source audit; never modify data, generate answers or train."""
from pathlib import Path
import json,hashlib,collections
repo=Path('/workspace/4k29');R=repo/'training/language/round47';source=R/'sources/documents.jsonl';base=Path('/workspace/daily-conversation-source-audit/human-only-raw/train');counts=collections.Counter();docs=0;utterances=0;short=0;adjacent_repeat=0;transitions=0;chars=0
for line in source.open():
 d=json.loads(line)
 if not d['id'].startswith('realpersona:'):continue
 assert d['partition']=='train';raw=(base/Path(d['sourcePath']).name).read_bytes();assert hashlib.sha256(raw).hexdigest()==d['sourceSha256'];rows=json.loads(raw)['utterances'];texts=[x['text']for x in rows];assert '\n'.join(texts)==d['text'];docs+=1
 for s in texts:
  norm=' '.join(s.split());counts[norm]+=1;utterances+=1;chars+=len(s);short+=len(norm)<=8
 transitions+=max(0,len(texts)-1);adjacent_repeat+=sum(a==b for a,b in zip(texts,texts[1:]))
info=dict(scope='Existing RealPersona TRAIN only; JMRD not audited by this script; no heldout opened',sourceDocumentsSha256=hashlib.sha256(source.read_bytes()).hexdigest(),verifiedDocuments=docs,originalUtterances=utterances,distinctWhitespaceNormalizedUtterances=len(counts),meanOriginalCharacters=chars/utterances,atMost8CharacterUtterances=short,atMost8CharacterFraction=short/utterances,top20ExactNormalizedUtteranceCount=sum(n for _,n in counts.most_common(20)),top20ExactNormalizedUtteranceFraction=sum(n for _,n in counts.most_common(20))/utterances,adjacentExactRepeatPairs=adjacent_repeat,adjacentPairs=transitions,whitespaceNormalizationForStatisticsOnly=True,noSourceOrGenerationTextModified=True,notASemanticOrGenericAcknowledgmentClassifier=True,noClaimThatShortRepliesAreBad=True,additionalOptimizerUpdates=0,codeSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(R/'execution/train-conversation-descriptive-audit.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info))
