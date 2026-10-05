"""Independent deterministic continuations from the already held-out pages.

Frozen after training began, before seeing any new model output; these do not
fit vocabulary/weights or select checkpoints. Raw fluency is not chat ability.
"""
import collections,hashlib,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent
c=json.loads((HERE/'switch-corpus.json').read_text());groups=collections.defaultdict(list)
for r in c['pretrainingTest']:groups[r['document']].extend(r['tokens'][r['prefixLength']:])
metadata={d['id']:d for d in c['provenance']['documents']};rows=[]
for identity,tokens in groups.items():
    text=bytes.fromhex(''.join(c['tokenizer']['bytes'][t] for t in tokens[:-1])).decode('utf-8');assert hashlib.sha256(text.encode()).hexdigest()==metadata[identity]['textSha256']
    paragraph=next(line for line in text.splitlines() if len(line)>=50 and 'http' not in line and '電話' not in line)
    prefix=paragraph[:36]
    rows.append(dict(id='switch-raw:'+identity,document=identity,sourceUrl=metadata[identity]['url'],textSha256=metadata[identity]['textSha256'],prefix=prefix,sourceContinuation=paragraph[36:156],license='CC BY-SA 4.0' if identity.startswith('mdn:') else 'Public Data License1.0'))
result=dict(schemaVersion=1,rows=rows,provenance=dict(corpusSha256=c['sourceSha256'],frozenAfterTrainingStart=True,frozenBeforeCandidateEvaluation=True,selection='First held-page paragraph with >=50 characters, excluding URL/phone notices; prefix36 Unicode characters. Never used for fitting or checkpoint selection.',scope='Eight separate source pages, raw next-token fluency diagnostic. Source continuations are illustrative references, not exact golds or factual validation. Not general language or dialogue quality.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();(HERE/'switch-raw-probes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['sourceSha256'])
