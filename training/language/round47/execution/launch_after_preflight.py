"""Explicit one-shot launch after successful exact-parent CI and frozen zero-update commit."""
import pathlib,json,hashlib,subprocess,datetime,sys,os
repo=pathlib.Path('/workspace/4k29');R=repo/'training/language/round47';E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(pathlib.Path('/workspace/ROUND46_FINAL_CI.json'))['headSha']=='d0dbffbdd28932ac45e09a854b53cee24248f72b'
assert read(pathlib.Path('/workspace/ROUND46_FINAL_CI.json'))['conclusion']=='success'
assert not (R/'continue-10000').exists() and not (E/'launch.json').exists()
p=read(R/'policy.json');assert p['learningRate']==4.4999999999999996e-5 and p['contextPreference']['coefficient']==.1 and p['sequenceUnlikelihood']['coefficient']==.2
for row in read(R/'source-manifest.json')['files']:assert (R/row['path']).stat().st_size==row['bytes'] and sha(R/row['path'])==row['sha256'],row['path']
for n in ['data-preflight.json','sampling-probability-preflight.json','prefix-policy-preflight.json','eos-full-training-mask-preflight.json','context-preflight.json','initial-development-preflight.json','preflight-runtime.json','new-source-gradient-preflight.json','single-condition-and-executable-preflight.json']:assert (E/n).exists(),n
assert read(E/'initial-development-preflight.json')['fullMixedViewDevelopmentExactlyMatchesParent']
assert read(E/'preflight-runtime.json')['allParametersFiniteNonzeroGradients']
assert read(E/'new-source-gradient-preflight.json')['allParametersFiniteNonzeroGradients']
assert 'Ran 43 tests' in (E/'tests-preflight.log').read_text() and (E/'tests-preflight.log').read_text().strip().endswith('OK')
assert 'ℹ pass 962' in (E/'repository-tests.log').read_text() and 'ℹ fail 0' in (E/'repository-tests.log').read_text()
assert read(E/'public-evaluation.log')['passed']==2580
subprocess.run(['git','diff','--exit-code'],cwd=repo,check=True,stdout=subprocess.DEVNULL)
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',str(R.relative_to(repo))],cwd=repo,text=True).strip()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
pr=json.loads(subprocess.check_output(['gh','pr','view','--json','number,isDraft'],cwd=repo,text=True));assert pr['isDraft']
handles=[];children=[]
for script,log in [('supervise.py','controller.log'),('wait_interim.py','interim-waiter.log'),('wait_final_context.py','context-final-waiter.log'),('wait_terminal_diagnostic.py','terminal-waiter.log'),('wait_human_train_gap.py','train-gap-waiter.log'),('../fixed-source-mrmp-dev/after_final.py','source-waiter.log')]:
 f=(E/log).open('ab',buffering=0);handles.append(f);proc=subprocess.Popen([sys.executable,str(E/script)],cwd=repo,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);children.append(dict(script=script,pid=proc.pid))
launch=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=children[0]['pid'],children=children,frozenZeroUpdateCommit=head,pr=pr['number'],actualRetainedUpdatesAtLaunch=0,scientificControl='round46',oneFactor='Sequence UL coefficient0.1 to0.2; LR4.5e-5 and context CE0.1 retained',exactParentFinalCiRun=40158137169)
(E/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
for f in handles:f.close()
print(json.dumps(launch))
