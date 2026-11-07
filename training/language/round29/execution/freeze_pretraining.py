import pathlib,json,hashlib,subprocess,sys,datetime
R=pathlib.Path(__file__).resolve().parents[1];C=R.parent/'round25';E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (R/'continue-10000/checkpoint.pt').exists() and not (E/'train.log').exists()
p=read(C/'policy.json');source=R/'sources/manifest.json';p.update(experiment='Round29 sibling of adopted Round25: ONLY human everyday-conversation corpus mass0→0.10; old masses×0.90, all model/objective/LR/seed fixed',genreSampling={**{k:v*.9 for k,v in p['genreSampling'].items()},'human-chat':.1},nllSuccessThreshold=read(C/'execution/optimizer-audit.json')['bestWeightedDevelopmentNllPerByte'],newSourceManifestSha256=sha(source),newSourceDocumentsSha256=sha(R/'sources/documents.jsonl'),sourceManifestReference='sources/manifest.json',sourcePolicySha256=sha(R/'source-policy.json'),rationale={'target':'Natural everyday Japanese; practical domain declared before training','evidence':'Round28 mass30% improved human DEV NLL1.288001→0.928190 but common DEV NLL worsened0.971422→0.971899 and daily loops11→12. Test mass10% alone to measure retention/domain tradeoff; do not adopt rejectedRound28.','factor':'Human TRAIN corpus mass0→10%, preserve every old TRAIN row and old relative masses. Neither capacity, vocabulary, LR nor objectives change.','limitation':'One seed, exposed development, no new TEST language claim; source-only64char hash hygiene does not guarantee no short/fuzzy overlap.'},supplementaryEverydayDevelopment={'fixedDailyProbesSha256':sha(E/'daily-probes.json'),'humanDev99PreviouslyExposed':True,'oneExactDuplicateDevFile':True,'usedForWeightSelection':False,'originalStrictGatesUnchanged':True,'additionalPracticalAdoptionGuard':'Original Pareto plus humanDEV99 NLL must not rise and daily12 full/nonloop counts must not fall; ambiguity can block adoption','controlHumanDev99Nll':1.2880010131269757,'controlDailyFull':0,'controlDailyNonloop':1,'reservedTestModelEvaluation':False,'rawReservedTestUsedOnlyForPretrainingDuplicateHashes':True})
for k in list(p):
 if k.startswith('control') and k.endswith('ManifestSha256'):del p[k]
p['doseComparison']={'round':'round28','mixture':.3,'artifactManifestSha256':sha(R.parent/'round28/execution/artifact-manifest.json'),'notAdopted':True};p['controlManifestSha256']=sha(C/'execution/artifact-manifest.json');p['codeHashes']={n:sha(R/n) for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py']};write(R/'policy.json',p)
subprocess.run([sys.executable,str(E/'verify_single_factor.py')],check=True)
# Learning input and source/license identities, including all posttraining evaluation code.
paths=set()
for f in R.rglob('*'):
 if not f.is_file() or '__pycache__' in f.parts or 'continue-10000' in f.parts or f.name in ['source-manifest.json','frozen-preflight.json','preflight-runtime.json'] or f in [R/'README.md',R/'REPRODUCTION.md'] or f.suffix=='.log':continue
 paths.add(str(f.relative_to(R)))
for row in read(C/'source-manifest.json')['files']:
 f=(C/row['path']).resolve()
 if f.exists():paths.add(__import__('os').path.relpath(f,R))
for f in ['../round28/execution/artifact-manifest.json','../round28/execution/adoption.json','../round28/RESULTS.md','../round28/policy.json','../round28/continue-10000/model.js','../model.py','../round25/execution/artifact-manifest.json','../round25/execution/adoption.json','../round25/policy.json','../round25/continue-10000/model.js','../round25/continue-10000/checkpoint.pt','../round27/execution/artifact-manifest.json','../round27/execution/adoption.json','../round27/RESULTS.md','../round10/review.py','../round10/evaluate.py','../round10/evaluate_js.mjs','../round10/full-meaning-policy.json','../round10/generation-policy.json','../round11/continue-10000/checkpoint.pt']:
 paths.add(f)
files=[]
for n in sorted(paths):
 f=R/n;assert f.is_file(),str(f);files.append(dict(path=n,sha256=sha(f),bytes=f.stat().st_size))
write(R/'source-manifest.json',dict(files=files,actualExperimentalUpdatesAtFreeze=0,oneLearningFactor='human everyday corpus mixture0→10%',scientificControl='round25',sourceHygieneTestHashingOnly=True))
write(E/'frozen-preflight.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),policySha256=sha(R/'policy.json'),sourceManifestSha256=sha(R/'source-manifest.json'),actualExperimentalOptimizerUpdates=0,requestedUpdates=10000,trainingCompleted=False,realRuntimeAndGradientPreflightStillRequired=True))
print('Frozen',len(files),'source/input files, actual experimental updates0')
