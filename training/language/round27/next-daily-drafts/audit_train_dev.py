"""Hash-only duplicate audit of TRAIN + already exposed DEV. Reserved TEST untouched.
No model/tokenizer, no normalization/rewrite, no output selection or training.
"""
import collections,hashlib,json,pathlib,datetime
B=pathlib.Path('/workspace/daily-conversation-source-audit');O=B/'future-train-audit'
manifest=json.loads((B/'human-source-acquisition.json').read_text());folds=json.loads((B/'prospective-speaker-folds.json').read_text())['speakerFolds'];sha=lambda x:hashlib.sha256(x).hexdigest()
D=collections.defaultdict(list);U=collections.defaultdict(lambda:collections.defaultdict(list));rows=[]
for r in sorted(manifest['records'],key=lambda x:(x['dialogueId'],x['sourcePath'])):
 if r['fold'] not in ['train','development']:continue
 f=r['fold'];raw=(B/'human-only-raw'/f/pathlib.PurePosixPath(r['sourcePath']).name).read_bytes();assert sha(raw)==r['sha256'];d=json.loads(raw);assert all(folds[s]==f for s in d['interlocutors'])
 text='\n'.join(u['text'] for u in d['utterances']);seq=[[d['interlocutors'].index(u['interlocutor_id']),u['text']] for u in d['utterances']];digest=sha(json.dumps(seq,ensure_ascii=False,separators=(',',':')).encode());D[digest].append((f,r['sourcePath']))
 for i,u in enumerate(d['utterances']):
  if len(u['text'])>=32:U[sha(u['text'].encode())][f].append((r['sourcePath'],i,len(u['text'])))
 rows.append(dict(sourcePath=r['sourcePath'],dialogueId=r['dialogueId'],fold=f,sourceSha256=r['sha256'],serializedSha256=sha(text.encode()),canonicalDialogueHash=digest,serializedBytes=len(text.encode()),utterances=len(d['utterances'])))
duplicate=[dict(canonicalDialogueHash=h,occurrences=x) for h,x in D.items() if len(x)>1]
cross=[dict(utteranceHash=h,occurrences=dict(x)) for h,x in U.items() if 'train' in x and 'development' in x]
excluded=set()
for h,items in D.items():
 t=[i for f,i in items if f=='train'];v=[i for f,i in items if f=='development']
 if v:excluded.update(t)
 elif len(t)>1:excluded.update(sorted(t)[1:])
report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='TRAIN + exposed DEV only; reserved TEST NOT read',scriptSha256=sha(pathlib.Path(__file__).read_bytes()),sourceManifestSha256=sha((B/'human-source-acquisition.json').read_bytes()),foldPolicySha256=manifest['foldPolicySha256'],exactDialogueDuplicates=duplicate,trainDevExactUtteranceOverlapAtLeast32Characters=cross,proposedTrainDuplicateExclusions=sorted(excluded),retainedTrainCandidateCount=sum(r['fold']=='train' and r['sourcePath'] not in excluded for r in rows),modelOrTokenizerExecuted=False,modelTrainingUpdates=0,sourceTextRewritten=False,trainingDataCreatedOrAdopted=False,reservedTestAuditStillRequiredBeforeTraining=True,shortCommonGreetingsNotTreatedAsLeakage=True,nearDuplicateAuditPending=True,rows=rows)
(O/'train-dev-duplicate-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','exactDialogueDuplicates','trainDevExactUtteranceOverlapAtLeast32Characters']}));print('duplicate groups',len(duplicate),'cross-fold long exact utterances',len(cross))
