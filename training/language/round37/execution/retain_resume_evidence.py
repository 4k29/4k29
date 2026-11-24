"""Save matching immutable log prefixes for existing checkpoints; never resume/step."""
import pathlib,json,hashlib,time,sys,datetime,torch
E=pathlib.Path(__file__).resolve().parent;R=E.parent;sys.path.insert(0,str(E));from execute import retained_log
torch.set_num_threads(1)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def retain(n):
 d=E/f'retained-paired-{n}';receipt=d/'resume-evidence.json'
 if receipt.exists():return True
 if not (d/'snapshot.json').exists():return False
 c=torch.load(d/'checkpoint.pt',weights_only=False,map_location='cpu');assert c['step']==n
 text=retained_log((E/'train.log').read_text(),n);events=[json.loads(s)for s in text.splitlines()];validation=[x for x in events if 'validation'in x];assert validation==c['history']
 trace=d/'training-rollouts.jsonl';assert len(trace.read_text().splitlines())==c['rolloutCalls']==n//10
 config=json.loads((R/'continue-10000/config.json').read_text());assert config['config']==c['config']and config['settings']==c['settings']
 configpath=d/'config.json';configpath.write_text(json.dumps(config,indent=2)+'\n');log=d/'train-through-snapshot.log';log.write_text(text)
 out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualUpdates=n,checkpointSha256=sha(d/'checkpoint.pt'),checkpointChunksManifestSha256=sha(d/'checkpoint.pt.chunks.json'),trainLogPrefixSha256=sha(log),trainLogEvents=len(events),trainLossEvents=sum('trainingLoss'in x for x in events),validationHistoryExactlyMatchesCheckpoint=True,trainingRolloutsSha256=sha(trace),rolloutCalls=c['rolloutCalls'],configSha256=sha(configpath),sourceManifestSha256=sha(R/'source-manifest.json'),optimizerCounters=sorted({int(x['step'])for x in c['optimizer']['state'].values()}),codeSha256=sha(pathlib.Path(__file__)),liveFilesNotModified=True,additionalOptimizerUpdates=0)
 assert out['optimizerCounters']==[20000+n]
 receipt.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True);return True
while True:
 done=[retain(n)for n in [200,1000,5000]]
 if all(done)or '--watch'not in sys.argv:break
 time.sleep(30)
