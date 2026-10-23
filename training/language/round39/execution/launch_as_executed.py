import pathlib,json,subprocess,hashlib,datetime,sys
repo=pathlib.Path('/workspace/4k29');R=repo/'training/language/round39';E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(E/'initial-development-preflight.json')['fullMixedViewDevelopmentExactlyMatchesParent']
for name in ['preflight-runtime.json','new-source-gradient-preflight.json']:
 a=read(E/name);assert a['allParametersFiniteNonzeroGradients'];assert a['sourceHashes']['policy.json']==sha(R/'policy.json');assert a['sourceHashes']['source-manifest.json']==sha(R/'source-manifest.json')
assert read(E/'data-preflight.json')['allDataFilesByteIdenticalToRound38']
for f in read(R/'source-manifest.json')['files']:assert sha(R/f['path'])==f['sha256'],f['path']
assert not (R/'continue-10000/checkpoint.pt').exists()and not(E/'launch.json').exists()
with(E/'supervisor.log').open('ab',buffering=0)as log:proc=subprocess.Popen([sys.executable,str(E/'supervise.py')],cwd=repo,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
a=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,requestedUpdates=10000,actualUpdatesAtLaunch=0,policySha256=sha(R/'policy.json'),sourceManifestSha256=sha(R/'source-manifest.json'),allPreflightsPassed=True);(E/'launch.json').write_text(json.dumps(a,indent=2)+'\n')
for script,name in [(E/'wait_terminal_diagnostic.py','terminal-waiter.log'),(E/'wait_human_train_gap.py','human-gap-waiter.log'),(R/'fixed-source-mrmp-dev/after_final.py','source-waiter.log')]:
 with(E/name).open('ab',buffering=0)as f:subprocess.Popen([sys.executable,str(script)],cwd=repo,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps(a),flush=True)
