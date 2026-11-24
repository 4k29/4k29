"""Exact full fixed-prefix overlap on appended TRAIN only; no model or TEST."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();inputs={'daily12':E/'daily-probes.json','native8':E/'content-native-dev/probes.json','mrmp5':R/'fixed-source-mrmp-dev/probes.json','original17':R.parent/'round37/execution/new-validation.json'};groups={k:read(p)['rows'if k=='original17'else'probes']for k,p in inputs.items()};docs=[json.loads(x)for x in(R/'added-human-source/documents.jsonl').read_text().splitlines()];hits=[]
for name,rows in groups.items():
 for row in rows:
  matches=[d['originalDocument']for d in docs if row['prefix']in d['text']]
  if matches:hits.append(dict(group=name,id=row['id'],matchingTrainDocuments=matches))
report=dict(scope='Supplementary exact complete fixed-probe prefix overlap audit on appended JMRD only, no generation or new TEST; after launch, no data changed',groups={k:len(v)for k,v in groups.items()},fixedInputSha256={k:sha(p)for k,p in inputs.items()},addedTrainDocuments=len(docs),exactFullPrefixMatches=hits,addedDocumentsSha256=sha(R/'added-human-source/documents.jsonl'),noShortSubstringOrSemanticOverlapGuarantee=True,notNewSourceParticipantDisjointnessProof=True,additionalOptimizerUpdates=0,codeSha256=sha(pathlib.Path(__file__)))
(E/'appended-source-fixed-prefix-overlap.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(fixedPrefixes=sum(len(v)for v in groups.values()),exactFullPrefixMatches=len(hits),additionalOptimizerUpdates=0)))
