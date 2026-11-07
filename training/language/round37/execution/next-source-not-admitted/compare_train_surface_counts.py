"""Descriptive TRAIN-only literal-surface counts; no semantic grading or data admission."""
import pathlib,json,collections,statistics,hashlib
R=pathlib.Path(__file__).resolve().parent;B=pathlib.Path('/workspace/4k29/training/language/round37');C=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train');read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Explicitly posthoc list of literal reply surfaces observed in current generated failures.
literals={'そうですね。','そうですね！','そうなんですね。','そうなんですね！','そうです。','なるほど。','ありがとうございます！','お願いします！'}
real=[]
for line in (B/'sources/documents.jsonl').read_text().splitlines():
 d=json.loads(line);p=C/pathlib.PurePosixPath(d['sourcePath']).name;assert sha(p)==d['sourceSha256'];original=read(p);assert len(original['utterances'])==d['utteranceCount'];real.extend(x['text']for x in original['utterances'])
jmrd=[x['text']for d in read(R/'upstream-train.json')for x in d['dialog']]
def counts(items):
 c=collections.Counter(items);lengths=[len(s)for s in items];return dict(utterances=len(items),characters=sum(lengths),meanCharacters=statistics.mean(lengths),medianCharacters=statistics.median(lengths),atMost10Characters=sum(n<=10 for n in lengths),atLeast40Characters=sum(n>=40 for n in lengths),exactDistinctStrings=len(c),exactLiteralSurfaceCounts={s:c[s]for s in sorted(literals)},combinedExactLiteralOccurrences=sum(c[s]for s in literals))
out=dict(scope='Current admitted RealPersona TRAIN vs prospective upstream JMRD TRAIN; raw original utterances',posthocLiteralPatterns=True,literalSurfaceList=sorted(literals),results=dict(currentRealPersona=counts(real),candidateJmrd=counts(jmrd)),limitations='Literal list is not a complete acknowledgement classifier. Unique counts and length are not measures of meaning or training benefit. Genres and collection methods differ; no causal claim or frequency matching. No current training input altered.',noHeldoutRead=True,noModelOrTokenizer=True,notAdmitted=True,realPersonaDocumentsSha256=sha(B/'sources/documents.jsonl'),candidateRawSha256=sha(R/'upstream-train.json'),codeSha256=sha(pathlib.Path(__file__)))
(R/'train-surface-comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
