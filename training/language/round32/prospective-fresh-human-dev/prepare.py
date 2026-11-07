"""Pinned original human corpus: metadata-only speaker split, DEV-only probes.
No model, optimizer, profiles, reserved-text display or TEST tokenization.
"""
import collections,datetime,hashlib,json,pathlib,sys,tarfile
D=pathlib.Path(__file__).resolve().parent;R=D.parent;repo=R.parents[2]
read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
policy=read(D/'policy.json');assert policy['sourceCommit']=='e6e39cb896df88781c7a2e0451226a527c5f1e2e';assert not (D/'probes.json').exists()
cache=pathlib.Path('/workspace/mrmp-fresh-dev-source');cache.mkdir(exist_ok=False)
tree=read(pathlib.Path('/workspace/mrmp-source-tree.json'));assert not tree['truncated'];tree={r['path']:r for r in tree['files']}
speakers={};records=[]
def speaker_fold(s):
 n=int(sha(('r32-mrmp-v1|speaker|'+s).encode()),16)%100
 return 'future-train-not-admitted' if n<50 else 'development' if n<75 else 'reserved-test'
with tarfile.open('/workspace/mrmp-pinned-source.tar.gz','r:gz')as archive:
 for member in archive:
  if not member.isfile():continue
  path=member.name.split('/',1)[1] if '/'in member.name else ''
  dialogue=path.startswith('multi_relational_multi_party_chat_corpus/dialogues/') and path.endswith('.json')
  if not dialogue and path not in ['LICENSE','README.md','VERSION']:continue
  assert path in tree;raw=archive.extractfile(member).read();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert blob==tree[path]['sha'] and len(raw)==tree[path]['size']
  if not dialogue:
   (D/('upstream-'+path)).write_bytes(raw);continue
  obj=json.loads(raw);ids=obj['interlocutors'];assert len(ids)==3 and len(set(ids))==3;folds={speaker_fold(s)for s in ids}
  for s in ids:speakers[s]=speaker_fold(s)
  fold=next(iter(folds)) if len(folds)==1 else 'cross-speaker-fold-excluded'
  dest=cache/fold/pathlib.PurePosixPath(path).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
  records.append(dict(sourcePath=path,sourceSha256=sha(raw),gitBlobSha1=blob,bytes=len(raw),dialogueId=obj['dialogue_id'],dialogueType=obj['dialogue_type'],speakers=ids,fold=fold,cachePath=str(dest)))
assert len(records)==960
write(D/'prospective-speaker-folds.json',dict(rule=policy['prospectiveSpeakerFold'],speakerFolds=dict(sorted(speakers.items())),profilesExtracted=False))
manifest=dict(sourceRepository=policy['sourceRepository'],sourceCommit=policy['sourceCommit'],sourceLicense=policy['sourceLicense'],attribution=policy['sourceAttribution'],acquisitionUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),policySha256=sha((D/'policy.json').read_bytes()),sourceArchiveSha256=sha(pathlib.Path('/workspace/mrmp-pinned-source.tar.gz').read_bytes()),preparationCodeSha256=sha(pathlib.Path(__file__).read_bytes()),speakerFoldSha256=sha((D/'prospective-speaker-folds.json').read_bytes()),dialogues=len(records),speakers=len(speakers),dialogueCounts=dict(collections.Counter(r['fold']for r in records)),reservedJsonParsedForSpeakerMetadataOnly=True,reservedTextSemanticallyDisplayed=False,reservedTestEncodedOrModelEvaluated=False,profilesOrAttributesUsed=False,prospectiveTrainAdmitted=False,modelInstantiated=False,optimizerUpdates=0,records=records)
write(D/'source-manifest.json',manifest)
sys.path.insert(0,str(repo/'training/dialogue'));from tokenizer import encode_stream,SPECIALS
tok=read(R/'multiview/tokenizer.json');candidates=[]
known_train={d['textSha256'] for d in read(R/'multiview/train.index.json')['documents']if d['variant']==0}
known_train.update(json.loads(l)['textSha256'] for l in (R.parent/'round29/sources/documents.jsonl').read_text().splitlines())
for record in records:
 if record['fold']!='development' or record['dialogueId']in policy['excludePreviouslyDisplayedReadmeExampleDialogueIds']:continue
 raw=pathlib.Path(record['cachePath']).read_bytes();assert sha(raw)==record['sourceSha256'];obj=json.loads(raw);turns=obj['utterances'];text='\n'.join(u['text']for u in turns)
 if sha(text.encode())in known_train:continue
 choices=[]
 for i in range(5,len(turns)-1):
  pair=[turns[i-1]['text'],turns[i]['text']]
  if not 20<=len(pair[-1])<=100 or any(not x.strip() or '＊＊'in x or '@'in x or any(ord(c)<32 and c not in '\n\t\r' for c in x)for x in pair):continue
  prefix='\n'.join(pair)+'\n';tokens=[SPECIALS['bos']]+encode_stream(prefix,tok)
  if len(tokens)>64:continue
  rank=sha(('r32-mrmp-prefix-v1|'+record['sourcePath']+'|'+str(i)).encode());choices.append(dict(rankKey=rank,prefix=prefix,prefixSha256=sha(prefix.encode()),prefixTokens=len(tokens),utteranceStart=i-1,utteranceEndInclusive=i,sourcePath=record['sourcePath'],sourceSha256=record['sourceSha256'],dialogueId=record['dialogueId'],dialogueType=record['dialogueType'],family=record['dialogueId'][:4],speakers=record['speakers'],sourceTextSha256=sha(text.encode())))
 if choices:
  row=min(choices,key=lambda r:r['rankKey']);row['documentRank']=sha(('r32-mrmp-document-v1|'+record['sourcePath']).encode());candidates.append(row)
groups=collections.defaultdict(list)
for row in candidates:groups[row['family']].append(row)
for rows in groups.values():rows.sort(key=lambda r:r['documentRank'])
family_order=sorted(groups,key=lambda x:sha(('r32-mrmp-family-v1|'+x).encode()));selected=[];depth=0
while len(selected)<8:
 batch=[groups[f][depth] for f in family_order if depth<len(groups[f])]
 if not batch:break
 selected.extend(batch[:8-len(selected)]);depth+=1
assert selected,'No eligible DEV context; do not resample or change frozen policy'
known_prefixes=set()
for p in [R/'execution/daily-probes.json',R/'execution/content-native-dev/probes.json',R.parent/'round31/execution/old-validation.json']:
 obj=read(p)
 for row in obj.get('probes',obj.get('rows',[])):known_prefixes.add(row['prefix'])
assert all(row['prefix']not in known_prefixes for row in selected)
for i,row in enumerate(selected):row['id']=f'fresh-mrmp-{i:02}'
probes=dict(createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceRepository=policy['sourceRepository'],sourceCommit=policy['sourceCommit'],sourceManifestSha256=sha((D/'source-manifest.json').read_bytes()),selectionPolicySha256=sha((D/'policy.json').read_bytes()),speakerFoldSha256=sha((D/'prospective-speaker-folds.json').read_bytes()),tokenizerSha256=sha((R/'multiview/tokenizer.json').read_bytes()),actualContexts=len(selected),independentSpeakerCombinationFamilies=len({r['family']for r in selected}),distinctPublicSpeakerIds=len({s for r in selected for s in r['speakers']}),sameFamilyMayRepeat=True,noModelOutputsSeenAtFreeze=True,notTest=True,neverUsedForCurrentTrainingOrCheckpointSelection=True,requestedMaxNewTokens=192,onlyDevelopmentTokenized=True,prospectiveTrainNotAdmitted=True,eligibleDevelopmentDocuments=len(candidates),probes=selected)
write(D/'probes.json',probes);print(json.dumps(dict(dialogueFoldCounts=manifest['dialogueCounts'],freshDevContexts=len(selected),families=probes['independentSpeakerCombinationFamilies'],speakers=probes['distinctPublicSpeakerIds'],noModelInstantiated=True,noReservedTextEncodedOrDisplayed=True,probesSha256=sha((D/'probes.json').read_bytes()))))
