"""Bind a reviewed pre-training capacity draft; never claim training completion."""
import datetime,hashlib,json,os,pathlib,subprocess,sys
B=pathlib.Path(os.environ.get('CAPACITY_DRAFT_ROOT','/workspace/4k29/training/language'));R=B/'round27';E=R/'execution'
for p in [R/'continue-10000/checkpoint.pt',R/'continue-10000/checkpoint.pt.chunks.json',E/'train.log']:
 assert not p.exists(), 'Do not re-freeze or restart existing training: '+str(p)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=read(R/'policy.json');C=B/read(E/'creation-context.json')['scientificControl'];assert read(C/'execution/adoption.json')['experimentalSettingsAdopted']
p['codeHashes'].update({n:sha(R/n) for n in ['capacity.py','capacity_audit.py','checkpoint_chunks.py','../model.py']})
for n in p['codeHashes']:p['codeHashes'][n]=sha(R/n)
p['supplementaryEverydayDevelopment']=dict(probeSha256=sha(E/'daily-probes.json'),humanSourceMetadataSha256=sha(R/'prospective-daily-source/human-source-acquisition.json.gz'),humanSpeakerFoldsSha256=sha(R/'prospective-daily-source/prospective-speaker-folds.json'),usedForWeightSelection=False,originalStrictGateUnchanged=True,authenticHumanTrainingAdded=False,reservedTestClosed=True)
write(R/'policy.json',p)
manifest=read(R/'source-manifest.json');entries={x['path']:x for x in manifest['files'] if x['path']!='execution/single-factor-audit.json'}
owned=['capacity.py','capacity_audit.py','checkpoint_chunks.py','execution/verify_initial.py','execution/verify_runtime.py','execution/verify_single_factor.py','execution/execute.py','execution/run.sh','execution/pipeline.sh','execution/persistent.sh','execution/publish_mechanical.py','execution/evaluate_daily.py','execution/daily_human_likelihood.py','execution/assemble_daily.py','execution/assemble_human_daily.py','execution/compare_daily.sh','execution/compare_human_daily.sh','execution/daily-probes.json','execution/DAILY_REVIEW_PROTOCOL.md','execution/HUMAN_DAILY_DEV_PROTOCOL.md','prospective-daily-source/human-source-acquisition.json.gz','prospective-daily-source/prospective-speaker-folds.json','prospective-daily-source/real-persona-chat-LICENSE']
owned += [str(f.relative_to(R)) for f in E.iterdir() if f.suffix in ['.py','.sh','.mjs']]
for n in owned:entries[n]={}
for name in entries:
 f=R/name;assert f.is_file(),str(f);entries[name]=dict(path=name,bytes=f.stat().st_size,sha256=sha(f))
manifest['files']=[entries[n] for n in sorted(entries)];write(R/'source-manifest.json',manifest)
subprocess.run([sys.executable,str(E/'verify_single_factor.py')],check=True)
f=E/'single-factor-audit.json';manifest['files'].append(dict(path='execution/single-factor-audit.json',bytes=f.stat().st_size,sha256=sha(f)));manifest['files'].sort(key=lambda x:x['path']);write(R/'source-manifest.json',manifest)
record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scientificControl=C.name,actualExperimentalOptimizerUpdates=0,requestedUpdates=10000,trainingCompleted=False,preparationOnly=True,capacityOnly='FFN768→1536',policySha256=sha(R/'policy.json'),sourceManifestSha256=sha(R/'source-manifest.json'),noExistingTrialCheckpointOrTrainingLog=True,modelMomentGradientPreflightStillRequired=True)
write(E/'frozen-draft.json',record);print(json.dumps(record))
