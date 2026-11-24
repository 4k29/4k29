"""Only run AFTER source/control adoption. Draft requiring preflight before actual updates."""
import pathlib,shutil,json,hashlib,os,sys
B=pathlib.Path(os.environ.get('CAPACITY_DRAFT_ROOT','/workspace/4k29/training/language'));C=B/sys.argv[1];R=B/'round27';assert C.name in ['round24','round25','round26'] and not R.exists();R.mkdir();(R/'execution').mkdir();read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert read(C/'execution/adoption.json')['experimentalSettingsAdopted']
for name in ['train.py','batching.py','initialization.py','objective.py','policy.json','source-manifest.json','.gitattributes']:
 shutil.copyfile(C/name,R/name)
for name in ['sequence_objective.py','rollout_trace.py']:
 if (C/name).exists():shutil.copyfile(C/name,R/name)
shutil.copytree(C/'multiview',R/'multiview')
oldcontrol=read(C/'execution/adoption.json')['scientificControl']
for f in (C/'execution').iterdir():
 if f.suffix not in ['.py','.sh','.mjs'] or f.name=='score_outputs.py':continue
 s=f.read_text().replace(C.name,'round27').replace('Round'+C.name[5:],'Round27')
 s=s.replace(oldcontrol+'/',C.name+'/').replace("'"+oldcontrol+"'","'"+C.name+"'").replace('Round'+oldcontrol[5:],'Round'+C.name[5:])
 (R/'execution'/f.name).write_text(s)
D=B/'round24/next-candidate-drafts'
for f in ['capacity.py','checkpoint_chunks.py']:shutil.copyfile(D/f,R/f)
for f in ['test_capacity.py','test_checkpoint_chunks.py']:shutil.copyfile(D/f,R/'execution'/f)
(R/'.gitignore').write_text('continue-10000/checkpoint.pt\ncontinue-10000/checkpoint-0.pt\ncontinue-10000/*.tmp\n')
p=R/'train.py';s=p.read_text().replace('from initialization import initialize','from initialization import initialize\nfrom capacity import expand_optimizer_moments');s=s.replace('hidden=args.dim*4','hidden=args.dim*8').replace("optimizer.load_state_dict(parent_state['optimizer']);torch.set_rng_state", "optimizer.load_state_dict(parent_state['optimizer']);expand_optimizer_moments(optimizer,model,parent_state);torch.set_rng_state");p.write_text(s)
p=R/'initialization.py';s=p.read_text().replace('ROOT=pathlib.Path','from capacity import expand_ffn_weights\nROOT=pathlib.Path');s=s.replace("assert saved['step']==10000 and saved['config']==model.config","assert saved['step']==10000 and saved['config']['hidden']==768 and model.config['hidden']==1536\n    assert {k:v for k,v in saved['config'].items() if k!='hidden'}=={k:v for k,v in model.config.items() if k!='hidden'}");s=s.replace("model.load_state_dict(saved['model'],strict=True)","expand_ffn_weights(model,saved)");s=s.replace("parentSelectedLineageUpdates=49000,","parentSelectedLineageUpdates=49000,newCoordinatesInitialLineageUpdates=0,newCoordinatesAdamWTensorCounter=10000,capacityChange='Only FFN hidden768→1536; old coordinate weights/moments retained; new incoming own random features and zero outgoing/moments',");p.write_text(s)
p=R/'execution/publish_mechanical.py';s=p.read_text().replace("R=pathlib.Path", "sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))\nfrom checkpoint_chunks import pack\nR=pathlib.Path");s=s.replace("files=[str(p.relative_to(REPO))", "for raw in [R/'continue-10000/checkpoint.pt',R/'continue-10000/checkpoint-0.pt']:\n if raw.exists():pack(raw)\nfiles=[str(p.relative_to(REPO))");s=s.replace("p.name not in ['automatic-publish.log','automatic-publish-complete.json']", "p.name not in ['automatic-publish.log','automatic-publish-complete.json','checkpoint.pt','checkpoint-0.pt'] and not p.name.endswith('.tmp')");p.write_text(s)
p=R/'execution/freeze_results.py';s=p.read_text().replace("p.name!='artifact-manifest.json'", "p.name not in ['artifact-manifest.json','checkpoint.pt','checkpoint-0.pt'] and not p.name.endswith('.tmp')");s=s.replace('manifest=dict(actualCompletedUpdates=',"assembled=[]\nfor name in ['checkpoint.pt','checkpoint-0.pt']:\n p=R/'continue-10000'/name;parts=json.loads(p.with_name(name+'.chunks.json').read_text());assert sha(p)==parts['sha256'];assembled.append(dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size,chunksManifest=str(p.with_name(name+'.chunks.json').relative_to(R))))\nmanifest=dict(assembledCheckpoints=assembled,actualCompletedUpdates=");p.write_text(s)
p=R/'execution/verify_manifest.py';s=p.read_text();s+='''\nfor raw in a['assembledCheckpoints']:\n manifest=R/raw['chunksManifest'];parts=json.loads(manifest.read_text());h=hashlib.sha256();total=0\n for row in parts['chunks']:\n  p=manifest.parent/row['path'];data=p.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'];h.update(data);total+=len(data)\n assert total==raw['bytes']==parts['bytes'] and h.hexdigest()==raw['sha256']==parts['sha256']\n if (R/raw['path']).exists():assert sha_raw(R/raw['path'])==raw['sha256']\n''';s=s.replace("for raw in a['assembledCheckpoints']:","def sha_raw(p):return hashlib.sha256(p.read_bytes()).hexdigest()\nfor raw in a['assembledCheckpoints']:");p.write_text(s)
p=read(R/'policy.json');p['experiment']=f'Round27 sibling of {C.name}: ONLY FFN hidden768→1536 with exact old function/coordinate moments and own new zero-output features; all adopted data/objective/LR fixed';p['nllSuccessThreshold']=read(C/'execution/optimizer-audit.json')['bestWeightedDevelopmentNllPerByte'];p['capacity']=dict(oldHidden=768,newHidden=1536,oldParameters=4655808,newParameters=7021248,oldCoordinateInitialLineage=49000,newCoordinateInitialLineage=0,oldCoordinateMoments='bitexact',newCoordinateMoments='zero',newIncoming='own seeded random std0.02',newOutgoing='zero',adamWTensorCounterInherited=10000,newCoordinateIndependentBiasCorrectionAge=False,storage='lossless SHA-bound40MiB chunks; raw atomic optimizer checkpoints local')
p['rationale']={'evidence':'Persistent wholemeaning failures and short subject/predicate errors motivate one isolated capacity test; no prior same-data/objective capacity comparison establishes causality.','limitations':'FFN-only expansion does not compare depth/embedding/context; new moment coordinates inherit global tensor age, not independent fresh bias correction.'}
for k in list(p):
 if k.startswith('control') and k.endswith('ManifestSha256'):del p[k]
p['controlManifestSha256']=sha(C/'execution/artifact-manifest.json');p['codeHashes'].update({f:sha(R/f) for f in ['train.py','initialization.py','capacity.py']});write(R/'policy.json',p)
files=[]
owned={'train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','policy.json'}
for row in read(C/'source-manifest.json')['files']:
 name=row['path']
 if not name.startswith('../') and not name.startswith('multiview/') and name not in owned:
  # Inherited data-preparation evidence remains bound to the immutable control.
  f=C/name;name=os.path.relpath(f,R)
 else:f=R/name
 assert f.exists(),str(f)
 files.append(dict(path=name,sha256=sha(f),bytes=f.stat().st_size))
for f in [R/'capacity.py',R/'checkpoint_chunks.py',C/'execution/artifact-manifest.json',C/'execution/adoption.json',C/'execution/new-validation.json',C/'execution/new-manual.json',C/'continue-10000/model.js',C/'continue-10000/metrics.json']:
 name=os.path.relpath(f,R)
 if not any(x['path']==name for x in files):files.append(dict(path=name,sha256=sha(f),bytes=f.stat().st_size))
write(R/'source-manifest.json',dict(files=files))
write(R/'execution/creation-context.json',dict(scientificControl=C.name,oneChangedFactor='FFN hidden capacity768→1536',actualExperimentalUpdates=0))
for f in (R/'execution').glob('*.sh'):os.chmod(f,0o755)
print('Draft prepared. MUST adapt audit/verify_initial/runtime/paired exposure, source/checkpoint storage, README and run all real preflights before launch.')
