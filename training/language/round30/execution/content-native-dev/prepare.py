"""Freeze8 distinct mid-dialogue human DEV contexts before model outputs."""
import pathlib,json,gzip,hashlib,sys,datetime
D=pathlib.Path(__file__).resolve().parent;R=D.parents[1];B=R.parent/'round28/prospective-daily-source';sys.path.insert(0,str(R.parent/'round10'));import evaluate as ev
sha=lambda b:hashlib.sha256(b).hexdigest();meta=json.loads(gzip.decompress((B/'human-source-acquisition.json.gz').read_bytes()));folds=json.loads((B/'prospective-speaker-folds.json').read_text())['speakerFolds'];tok=json.loads((R/'multiview/tokenizer.json').read_text());candidates=[];seen=set()
for row in sorted((x for x in meta['records'] if x['fold']=='development'),key=lambda x:sha(('r30-content-native-dev|'+x['sourcePath']).encode())):
 assert all(folds[s]=='development' for s in row['speakers']);p=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/development')/pathlib.PurePosixPath(row['sourcePath']).name;raw=p.read_bytes();assert sha(raw)==row['sha256'];u=json.loads(raw)['utterances']
 for index in range(4,len(u)-1):
  text=u[index]['text']
  if not 30<=len(text)<=100:continue
  prefix=text+'\n';start=index
  if 1+len(ev.encode_stream(prefix,tok))>64:continue
  previous=u[index-1]['text']+'\n'+prefix
  if 1+len(ev.encode_stream(previous,tok))<=64:prefix=previous;start=index-1
  h=sha(prefix.encode())
  if h in seen:continue
  seen.add(h);candidates.append(dict(id=f'content-native-{len(candidates):02}',group='human-development-mid-dialogue',prefix=prefix,prefixSha256=h,prefixTokens=1+len(ev.encode_stream(prefix,tok)),sourcePath=row['sourcePath'],sourceSha256=row['sha256'],utteranceStart=start,utteranceEndInclusive=index,rankKey=sha(('r30-content-native-dev|'+row['sourcePath']).encode())));break
 if len(candidates)==8:break
assert len(candidates)==8
out=dict(createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),probes=candidates,exposedDevelopmentOnly=True,newTest=False,selection='SourcePath ordered by SHA256(r30-content-native-dev|sourcePath); first eligible utterance index>=4 with30–100Unicodechars, ownBOS+canonicaltokens<=64, and future utterance exists. Include immediately preceding original utterance only if total<=64 tokens. Unique prefixSHA, one context per source. No generated outputs consulted.',usedForWeightSelection=False,strictGatesChanged=False,maxNewTokens=192,modelOutputsSeenAtFreeze=False,sourceCommit='28d0b6b3865b29cabc26c230a2db37cdf315e937',sourceLicense='CC BY-SA4.0',tokenizerSha256=sha((R/'multiview/tokenizer.json').read_bytes()))
assert not (D/'probes.json').exists();(D/'probes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(D/'real-persona-chat-LICENSE').write_bytes((B/'real-persona-chat-LICENSE').read_bytes());print(json.dumps({'probeSha256':sha((D/'probes.json').read_bytes()),'contexts':[x['prefix'] for x in candidates]},ensure_ascii=False))
