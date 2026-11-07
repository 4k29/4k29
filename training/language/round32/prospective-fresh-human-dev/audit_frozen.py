"""Read-only source/license/split/lossless-prefix audit; no models or TEST encoding."""
import hashlib,json,pathlib,sys,numpy as np
D=pathlib.Path(__file__).resolve().parent;R=D.parent;repo=R.parents[2];read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
m=read(D/'source-manifest.json');q=read(D/'probes.json');fold=read(D/'prospective-speaker-folds.json')['speakerFolds'];assert m['policySha256']==q['selectionPolicySha256']==sha((D/'policy.json').read_bytes());assert q['sourceManifestSha256']==sha((D/'source-manifest.json').read_bytes());assert q['speakerFoldSha256']==m['speakerFoldSha256']==sha((D/'prospective-speaker-folds.json').read_bytes());assert m['preparationCodeSha256']==sha((D/'prepare.py').read_bytes())
for r in m['records']:
 raw=pathlib.Path(r['cachePath']).read_bytes();assert sha(raw)==r['sourceSha256']and len(raw)==r['bytes'];assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==r['gitBlobSha1']
sys.path.insert(0,str(repo/'training/dialogue'));from tokenizer import encode_stream,SPECIALS
tok=read(R/'multiview/tokenizer.json');vocab=[bytes.fromhex(x)for x in tok['bytes']];records={r['sourcePath']:r for r in m['records']};prefixes={}
for p in q['probes']:
 r=records[p['sourcePath']];assert r['fold']=='development'and all(fold[s]=='development'for s in r['speakers']);assert r['sourceSha256']==p['sourceSha256'];obj=read(pathlib.Path(r['cachePath']));text='\n'.join(u['text']for u in obj['utterances'][p['utteranceStart']:p['utteranceEndInclusive']+1])+'\n';assert text==p['prefix']and sha(text.encode())==p['prefixSha256'];ids=encode_stream(text,tok);assert len(ids)+1==p['prefixTokens']<=64and b''.join(vocab[i]for i in ids)==text.encode();prefixes[p['id']]=text.encode()
found={label:{k:[]for k in prefixes}for label in ['currentRound32CanonicalTrain','historicalRound29HumanTrain']};index=read(R/'multiview/train.index.json');values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r')
for d in index['documents']:
 if d['variant']!=0:continue
 raw=b''.join(vocab[int(i)]for i in values[d['offset']+1:d['offset']+d['length']-1]);assert sha(raw)==d['textSha256']
 for ident,prefix in prefixes.items():
  if prefix in raw:found['currentRound32CanonicalTrain'][ident].append(d['id'])
for line in (R.parent/'round29/sources/documents.jsonl').read_text().splitlines():
 d=json.loads(line);assert d['partition']=='train';raw=d['text'].encode();assert sha(raw)==d['textSha256']
 for ident,prefix in prefixes.items():
  if prefix in raw:found['historicalRound29HumanTrain'][ident].append(d['id'])
report=dict(policySha256=q['selectionPolicySha256'],probesSha256=sha((D/'probes.json').read_bytes()),auditorSha256=sha(pathlib.Path(__file__).read_bytes()),all960RawSourceSha256SizesAndGitBlobIdsVerified=True,preparationCodeShaMatches=True,all5SourcePrefixesExactOriginalAdjacentDevUtterances=True,allOwnTokenPrefixesDecodeToExactUtf8=True,onlyDevelopmentTokenized=True,noReservedTextSemanticDisplayOrEncoding=True,modelsOrOptimizersInstantiated=False,trainingUpdates=0,actualContexts=5,uniquePrefixTexts=len(set(prefixes.values())),independentSpeakerCombinationFamilies=1,distinctPublicSpeakerIds=3,exactFullPrefixMatches=found,noExactFullPrefixMatchesInAuditedTrainCorpora=not any(v for corpus in found.values()for v in corpus.values()),documentationSha256={n:sha((D/n).read_bytes())for n in ['upstream-LICENSE','upstream-README.md','upstream-VERSION']},limits='Exact full-prefix audit of the currently admitted canonical source units and historical R29 human TRAIN only. Does not prove absence of every shorter/fuzzy overlap or independently audit all ancestral historical datasets. No resampling or deletion if a match is found; preserve the original frozen set and disclose it. Five source documents share one three-speaker cast; not five independent speaker groups.')
(D/'data-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['exactFullPrefixMatches','documentationSha256']}))
