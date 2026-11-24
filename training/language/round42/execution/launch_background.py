"""Launch one lock-protected long training pipeline after frozen zero-update audits."""
import pathlib,subprocess,json,datetime,sys,os
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';repo=R.parents[2]
assert not (E/'launch.json').exists(), 'Inspect existing run; do not duplicate'
for n in ['data-preflight.json','eos-full-training-mask-preflight.json','prefix-policy-preflight.json','context-preflight.json','initial-development-preflight.json','preflight-runtime.json']:
 assert (E/n).exists(),n
assert not (R/'continue-10000/checkpoint.pt').exists()
with (E/'controller.log').open('ab',buffering=0) as f:
 child=subprocess.Popen(['bash',str(E/'persistent.sh')],cwd=repo,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
(E/'launch.json').write_text(json.dumps(dict(pid=child.pid,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),requestedOptimizerUpdates=10000,actualCompletedAtLaunch=0,detachedFromChatTransport=True,command='bash training/language/round42/execution/persistent.sh',resumeOnlyWithExactIdentity=True),indent=2)+'\n')
print('Launched persistent R42 controller',child.pid,'actual updates at launch0',flush=True)
