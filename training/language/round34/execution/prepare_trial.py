"""Create one prospective prefix-policy trial after Round33 final human assessment.
Preparation script only; it never starts or counts optimizer updates.
"""
import pathlib,shutil,json,hashlib,subprocess
repo=pathlib.Path('/workspace/4k29');B=repo/'training/language';C=B/'round28';P=B/'round33';R=B/'round34';E=R/'execution';prep=pathlib.Path('/workspace/round34-preparation')
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not R.exists()
a=read(P/'execution/adoption-decision.json');assert a['actualCompletedUpdates']==10000
assert read(P/'execution/final-assessment.json')['fullOutputReviewPending'] is False
assert (P/'execution/artifact-manifest.json').exists()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip()
subprocess.run(['git','switch','-c','experiment/round34-human-negative-turn-boundary'],cwd=repo,check=True);E.mkdir(parents=True)
for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','checkpoint_chunks.py','source-policy.json','.gitignore','.gitattributes']:shutil.copy2(P/n,R/n)
for n in ['multiview','sources','prospective-daily-source']:shutil.copytree(P/n,R/n,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(prep/'prefix_selection.py',R/'prefix_selection.py');shutil.copy2(prep/'true-turn-token-boundaries.json',R/'human-turn-token-boundaries.json')
p=R/'train.py';s=p.read_text().replace('from rollout_trace import reconcile_trace, append_trace','from rollout_trace import reconcile_trace, append_trace\nfrom prefix_selection import load_selector')
needle="    train,train_values=load_partition(directory,'train');valid,valid_values=load_partition(directory,'validation')"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n    prefix_selector=load_selector(ROOT/'human-turn-token-boundaries.json',tok,train,policy['humanNegativePrefix']['featureMapSha256'],sha(directory/'tokenizer.json'),sha(directory/'train.index.json'),sha(ROOT/'sources/documents.jsonl'),min_tokens=8,max_tokens=32)")
needle="            prefix=x[:1,:min(policy['sequenceUnlikelihood']['prefixTokens'],rows[0]['length']-1)]";assert s.count(needle)==1
s=s.replace(needle,"            prefix_length=prefix_selector.length(rows[0],int(x[0,0]))\n            prefix=x[:1,:prefix_length]");p.write_text(s)
keep='execute.py supervise.py watch_resume.py archive_best_aligned.py verify_best_archive.py progress.py freeze_results.py verify_manifest.py preflight_initial_validation.py verify_runtime.py check_sampling.py inspect_checkpoint.py verify_initial.py audit.py replay_sampler.py compare_losses.py decode_training_rollouts.py rebind_old.py check_export_rounding.py diagnose_parity.py diagnose_parity.mjs diagnose_generation.py diagnose_gap.py measure_repetition.py assemble_numerical.py repository-checks.sh diagnose_sequence_saturation.py compare.sh compare_daily.sh evaluate_daily.py assemble_daily.py check_daily_rounding.py compare_human_daily.sh daily_human_likelihood.py assemble_human_daily.py run.sh persistent.sh publish_mechanical.py test_objective.py test_sequence_objective.py test_rollout_trace.py test_checkpoint_chunks.py preflight_data.py check_final_native_rounding.py pipeline.sh'.split()
paired={'compare.sh','compare_daily.sh','compare_human_daily.sh','rebind_old.py','check_export_rounding.py','diagnose_parity.py','diagnose_parity.mjs','measure_repetition.py','pipeline.sh'}
for n in keep:
 s=(P/'execution'/n).read_text().replace('round33','round34').replace('Round33','Round34')
 if n in paired:s=s.replace('round28/continue-10000/model.js','round33/continue-10000/model.js').replace('round28/continue-10000 --generation','round33/continue-10000 --generation').replace("'round28/execution'","'round33/execution'").replace('Round28 control','Round33 control')
 if n=='compare_losses.py':
  s=s.replace('show unequal corpus exposures','verify equal positive exposures').replace('exposureEqualityRequired=False','exposureEqualityRequired=True').replace('for x in events:',"assert all(r['oldTargetTokens']==r['newTargetTokens']and r['oldTargetBytes']==r['newTargetBytes']for r in rows)\nfor x in events:")
 if n=='publish_mechanical.py':s=s.replace('ONLY continued dose beyond aligned Round28 latest','ONLY human self-negative prefix end placement; paired same R28 initial state and10000 dose as R33').replace('aligned Round28 parent; adoption anchor remains Round25','aligned Round28 parent; paired comparator Round33; adoption anchor remains Round25')
 if n=='pipeline.sh':s=s.replace('python training/language/round34/execution/replay_sampler.py','python training/language/round34/execution/replay_sampler.py\npython training/language/round34/execution/paired_training_audit.py')
 if n=='verify_runtime.py':
  s=s.replace("x,y=pack(rows,v,256);m.train();", "selector=load_selector(ROOT/'human-turn-token-boundaries.json',read(ROOT/'multiview/tokenizer.json'),i,read(ROOT/'policy.json')['humanNegativePrefix']['featureMapSha256'],sha(ROOT/'multiview/tokenizer.json'),sha(ROOT/'multiview/train.index.json'),sha(ROOT/'sources/documents.jsonl'));x,y=pack(rows,v,256);m.train();")
  s=s.replace("x[3:4,:min(32,rows[3]['length']-1)]","x[3:4,:selector.length(rows[3],int(x[3,0]))]")
 (E/n).write_text(s)
shutil.copy2(prep/'paired_training_audit.py',E/'paired_training_audit.py')
shutil.copy2(pathlib.Path(__file__),E/'prepare_trial.py')
for n in ['daily-probes.json','DAILY_REVIEW_PROTOCOL.md','HUMAN_DAILY_DEV_PROTOCOL.md']:shutil.copy2(P/'execution'/n,E/n)
shutil.copytree(P/'execution/content-native-dev',E/'content-native-dev',ignore=shutil.ignore_patterns('new-*','old-*','__pycache__'))
s=(prep/'test_prefix_selection.py').read_text();s="import sys,pathlib\nsys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))\n"+s;(E/'test_prefix_selection.py').write_text(s)
# Same fixed evaluation sets and final-only supplemental diagnostics, no new TEST.
shutil.copytree(P/'fixed-source-mrmp-dev',R/'fixed-source-mrmp-dev',ignore=shutil.ignore_patterns('__pycache__'))
f=R/'fixed-source-mrmp-dev/after_final.py';t=f.read_text().replace('round33','round34').replace('Round33','Round34');t=t.replace("R.parent/'round28'","R.parent/'round33'").replace('R33','R34').replace('R28','R33').replace('R33 parentactual10000 versus R34additionalactual10000; cumulative progress differs.','R33 versus R34, both actual10000 from the same aligned Round28 parent.');f.write_text(t)
for n in ['assess_terminal_state.py','wait_terminal_diagnostic.py','wait_human_train_gap.py','human_train_sample_likelihood.py','human-train-gap-plan.json','terminal-diagnostic-plan.json','assemble_full_outputs.py']:
 t=(P/'execution'/n).read_text()
 if n not in ['human_train_sample_likelihood.py','human-train-gap-plan.json']:t=t.replace('round33','round34').replace('Round33','Round34')
 if n in ['wait_human_train_gap.py','assemble_full_outputs.py']:t=t.replace('round28/continue-10000/model.js','round33/continue-10000/model.js')
 if n=='assemble_full_outputs.py':t=t.replace('Round28:','Round33:').replace('Scientific parent Round28 actual10000 versus Round34 additional actual10000.','Scientific paired comparator Round33 versus Round34, both actual10000 from the same aligned Round28 parent.')
 (E/n).write_text(t)
p=read(P/'policy.json');p.update(experiment='Round34: ONLY human self-negative prefix end policy; sibling of R33 from same R28 model/Adam/RNG and equal10000 dose',controlManifestSha256=sha(P/'execution/artifact-manifest.json'),nllSuccessThreshold=read(P/'continue-10000/metrics.json')['bestValidationNllPerByte'])
p['sequenceUnlikelihood']['prefixSelection']='Human first sampled row: latest existing token-aligned true after-utterance separator within8..32 original real tokens, provided clean character start; otherwise original min32. All nonhuman rows unchanged. No retokenization or RNG.'
p['humanNegativePrefix']=dict(minTokens=8,maxTokens=32,featureMap='human-turn-token-boundaries.json',featureMapSha256=sha(R/'human-turn-token-boundaries.json'),fallback='exact original prefix',noPositiveTargetOrSamplingChange=True,prefixLengthChangePartOfTreatment=True)
p['rationale']=dict(evidence='R33 final results plus TRAIN-only actual negative endpoint and repeated-fourgram audits; fixed feature map shows most eligible rows have an earlier true separator',hypothesis='Source-turn-aligned negative histories may better penalize conversational repetition',limitations='Single exposed-DEV seed; endpoint policy necessarily changes prefix length; not pure boundary mechanism; retained source framing does not insert speaker labels')
p['supplementaryEverydayDevelopment'].update(controlHumanDev99Nll=read(P/'execution/daily-human-new-likelihood.json')['nllPerSerializedUtf8Byte'],controlDailyFull=a['daily12']['newMeaning'],controlDailyNonloop=12-a['daily12']['newLongLoops'])
p['codeHashes']={n:sha(R/n)for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','prefix_selection.py']};write(R/'policy.json',p)
write(E/'creation-context.json',dict(scientificControl='round33',initializationParent='round28',adoptionAnchor='round25',oneLearningFactor='Human self-negative prefix end policy only',parentLocalCompletedUpdates=10000,parentOptimizerUpdates=20000,parentWeightLineageUpdates=59000))
write(E/'prospective-evaluation-plan.json',dict(actualOptimizerUpdatesAtFreeze=0,requestedUpdates=10000,scientificControl='round33',initializationParent='round28',adoptionAnchor='round25',oneChangedLearningFactor='human self-negative prefix end policy',selection='Lowest unchanged common weighted exposed DEV at0/every500; no generation-based selection',strictGatesUnchanged=True,dailyPriority=True,samePositiveExposureAndRngMustBeVerified=True,terminalSeparateIfDifferent=True,notNewTest=True,publicModelChanged=False))
(R/'README.md').write_text('# Round34 — human self-negative prefix endpoint\n\nActual optimizer updates0 before preflight. Paired sibling of R33 from the SAME aligned R28latest model, Adam20000 and RNG, same additional10000 dose. Only change: first-row human self-negative prefix ends at the latest already-token-aligned true turn separator in8..32 real tokens when available with clean start; exact original fallback otherwise. No positive labels, sampling, vocabulary, BOS/EOS, decoding, model, LR or regularizer coefficient changes. Prefix length necessarily changes with the policy; no pure-boundary causal claim. R25 adoption anchor/public unchanged.\n')
s=(P/'execution/freeze_pretraining.py').read_text().replace('round33','round34').replace("'rollout_trace.py']","'rollout_trace.py','prefix_selection.py']").replace("for n in ['execution/artifact-manifest.json','execution/adoption-decision.json','RESULTS.md']:paths.add('../round32/'+n)","for n in ['execution/artifact-manifest.json','execution/adoption-decision.json','execution/final-assessment.json','execution/new-manual.json','execution/sampler-replay.json','continue-10000/checkpoint.pt','continue-10000/checkpoint-0.pt','continue-10000/training-rollouts.jsonl','continue-10000/model.js','continue-10000/metrics.json','RESULTS.md']:paths.add('../round33/'+n)").replace("scientificControl='round28'","scientificControl='round33',initializationParent='round28'").replace("oneLearningFactor='Continued training dose only'","oneLearningFactor='Human self-negative prefix end policy only'")
(E/'freeze_pretraining.py').write_text(s)
write(E/'preparation-context.json',dict(actualOptimizerUpdates=0,preparationScriptSha256=sha(pathlib.Path(__file__)),featureMapSha256=sha(R/'human-turn-token-boundaries.json'),prototypeFullTrainValidation=read(prep/'prefix_preparation_validation.json'),needsFullPreflightBeforeTraining=True))
print('Created draft only. Review one-factor diff, paired sampler checks, tests, freeze, runtime gradients and initial DEV BEFORE actual training.')
