"""One prospective EOS auxiliary trial; never starts training."""
import pathlib,shutil,json,hashlib,subprocess,re
repo=pathlib.Path('/workspace/4k29');B=repo/'training/language';P=B/'round34';R=B/'round35';E=R/'execution';prep=pathlib.Path('/workspace/round35-preparation')
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def advance(s):return s.replace('round34','__NEWLOW__').replace('Round34','__NEWCAP__').replace('round33','round34').replace('Round33','Round34').replace('__NEWLOW__','round35').replace('__NEWCAP__','Round35')
assert not R.exists();assert not subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip();assert read(P/'execution/final-assessment.json')['fullOutputReviewPending'] is False
subprocess.run(['git','switch','-c','experiment/round35-human-utterance-eos-aux'],cwd=repo,check=True);E.mkdir(parents=True)
for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','checkpoint_chunks.py','prefix_selection.py','human-turn-token-boundaries.json','source-policy.json','.gitignore','.gitattributes']:shutil.copy2(P/n,R/n)
for n in ['multiview','sources','prospective-daily-source']:shutil.copytree(P/n,R/n,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(prep/'utterance_end_objective.py',R/'utterance_end_objective.py')
f=R/'utterance_end_objective.py';s=f.read_text().replace('"""UNTRAINED candidate objective. No import or use by running Round34."""','"""Round35 auxiliary EOS at authentic human TRAIN utterance endings. Original labels retained."""');f.write_text(s)
# The new loss uses the existing validated true boundary map, no new tokenizer or positive data.
f=R/'train.py';s=f.read_text();s=s.replace('from prefix_selection import load_selector','from prefix_selection import load_selector\nfrom utterance_end_objective import eligible_mask, end_eos_loss')
s=s.replace("    settings['unlikelihood']=policy['unlikelihood']","    settings['humanUtteranceEndEos']=policy['humanUtteranceEndEos']\n    settings['unlikelihood']=policy['unlikelihood']")
s=s.replace("same raw targets'","same raw targets + 1.0 EOS auxiliary only at original unmasked standalone-newline human TRAIN true utterance ends'")
s=s.replace('rollout_calls=0;rollout_generated=0;rollout_negative=0','rollout_calls=0;rollout_generated=0;rollout_negative=0;end_eos_positions=0;end_eos_batches=0')
s=s.replace("rollout_negative=saved['rolloutNegativePositions']","rollout_negative=saved['rolloutNegativePositions'];end_eos_positions=saved['endEosPositions'];end_eos_batches=saved['endEosBatches']")
s=s.replace('rolloutNegativePositions=rollout_negative','rolloutNegativePositions=rollout_negative,endEosPositions=end_eos_positions,endEosBatches=end_eos_batches')
s=s.replace('def objective(x,y):','def objective(x,y,end_mask):').replace('return ce+1.0*ul,ce.detach(),ul.detach(),count',"aux=end_eos_loss(logits,y,end_mask,eos_id=2)\n            return ce+1.0*ul+policy['humanUtteranceEndEos']['coefficient']*aux,ce.detach(),ul.detach(),count,aux.detach()")
s=s.replace('loss,ce_loss,ul_loss,negative_count=train_objective(x,y)',"end_mask=eligible_mask(rows,y,prefix_selector.ends,newline_id=16)\n        loss,ce_loss,ul_loss,negative_count,end_eos_loss_value=train_objective(x,y,end_mask)")
s=s.replace('optimizer.step();laststep=step;',"optimizer.step();end_eos_positions+=int(end_mask.sum());end_eos_batches+=int(end_mask.any());laststep=step;")
s=s.replace('negativeCandidates=negative_count,sequenceUnlikelihoodLoss=', 'negativeCandidates=negative_count,endEosLoss=float(end_eos_loss_value),endEosPositionsThisBatch=int(end_mask.sum()),sequenceUnlikelihoodLoss=')
# Runtime validation of token identity and the fixed, prospectively chosen coefficient.
s=s.replace("    config=dict(vocabulary=", "    assert tok['bytes'][16]=='0a' and tok['bytes'][2]=='' and policy['humanUtteranceEndEos']['coefficient']==1.0\n    config=dict(vocabulary=")
f.write_text(s)
# Reuse audited infrastructure, replacing trial/control paths separately; Round28 remains initialization.
old=pathlib.Path('/workspace/prepare_round34.py').read_text();keep=re.search("keep='([^']+)'",old).group(1).split()
keep+=['test_prefix_selection.py','preflight_prefix_policy.py','assess_terminal_state.py','wait_terminal_diagnostic.py','wait_human_train_gap.py','human_train_sample_likelihood.py','assemble_full_outputs.py','freeze_pretraining.py','paired_training_audit.py','assemble_three_states.py','assemble_matched_terminal.py','pin_terminal_control.py']
for n in keep:
 if (P/'execution'/n).exists():(E/n).write_text(advance((P/'execution'/n).read_text()))
for n in ['daily-probes.json','DAILY_REVIEW_PROTOCOL.md','HUMAN_DAILY_DEV_PROTOCOL.md']:shutil.copy2(P/'execution'/n,E/n)
for n in ['human-train-gap-plan.json','terminal-diagnostic-plan.json']:
 x=read(P/'execution'/n);(E/n).write_text(advance(json.dumps(x,ensure_ascii=False,indent=2))+'\n')
shutil.copytree(P/'execution/content-native-dev',E/'content-native-dev',ignore=shutil.ignore_patterns('new-*','old-*','__pycache__'))
shutil.copytree(P/'fixed-source-mrmp-dev',R/'fixed-source-mrmp-dev',ignore=shutil.ignore_patterns('__pycache__'))
# Prospectively use the corrected evaluator with EXACT control34/current35 allowlist.
(R/'fixed-source-mrmp-dev/evaluate.py').write_text(advance((P/'fixed-source-mrmp-dev/evaluate_control33.py').read_text()))
s=advance((P/'fixed-source-mrmp-dev/after_final_recover_control33.py').read_text()).replace('evaluate_control33.py','evaluate.py').replace('-generation-recovered.log','-generation.log').replace('R34 versus R34','R34 versus R35').replace('R34:', 'R35:')
# Named output-state field must advance too; these numbers are identifiers, not changes to settings.
s=s.replace('actualRetainedR34Updates','actualRetainedR35Updates')
(R/'fixed-source-mrmp-dev/after_final.py').write_text(s)
for n in ['after_final_recover_control33.py','evaluate_control33.py']:(R/'fixed-source-mrmp-dev'/n).unlink(missing_ok=True)
p=read(P/'policy.json');p.update(experiment='Round35: ONLY additional EOS auxiliary at original human TRAIN true utterance endings; paired sibling of R34 from same aligned R28 model/Adam/RNG',controlManifestSha256=sha(P/'execution/artifact-manifest.json'),nllSuccessThreshold=read(P/'continue-10000/metrics.json')['bestValidationNllPerByte'])
p['humanUtteranceEndEos']=dict(coefficient=1.0,eosId=2,standaloneNewlineId=16,featureMap='human-turn-token-boundaries.json',featureMapSha256=sha(R/'human-turn-token-boundaries.json'),eligibility='human-chat TRAIN only; true utterance-end target is original standalone newline16; originally unmasked; no compound newline tokens',normalization='Sum auxiliary EOS CE / original nonmasked target count in same batch',retainOriginalGoldTargets=True,noExtraModelForwardOrRandomDraw=True)
p['rationale']=dict(evidence='R34 all84 new full outputs read; selected and terminal daily12/native8/source5 meaning all0; selected conversation EOS0/25; prefix endpoint alone did not improve daily semantics',hypothesis='Original training has many inter-utterance newlines but relatively sparse EOS; auxiliary EOS at authentic human utterance endings may suppress endless acknowledgement and turn takeover',limitations='Competing newline and EOS targets can worsen unchanged pure-CE selector; ending alone does not establish relevance, grammar or meaning; one exposed-DEV seed')
a=read(P/'execution/adoption-decision.json');p['supplementaryEverydayDevelopment'].update(controlHumanDev99Nll=read(P/'execution/daily-human-new-likelihood.json')['nllPerSerializedUtf8Byte'],controlDailyFull=a['daily12']['newMeaning'],controlDailyNonloop=12-a['daily12']['newLongLoops'])
p['codeHashes']={n:sha(R/n)for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','prefix_selection.py','utterance_end_objective.py']};write(R/'policy.json',p)
f=E/'freeze_pretraining.py';s=f.read_text().replace("'prefix_selection.py']","'prefix_selection.py','utterance_end_objective.py']").replace("oneLearningFactor='Human self-negative prefix end policy only'","oneLearningFactor='Human true utterance-end EOS auxiliary coefficient1.0 only'");f.write_text(s)
write(E/'creation-context.json',dict(scientificControl='round34',initializationParent='round28',adoptionAnchor='round25',oneLearningFactor='Additional true-human-utterance-end EOS auxiliary coefficient1.0 only',parentLocalCompletedUpdates=10000,parentOptimizerUpdates=20000,parentWeightLineageUpdates=59000,actualNewOptimizerUpdates=0))
write(E/'prospective-evaluation-plan.json',dict(actualOptimizerUpdatesAtFreeze=0,requestedUpdates=10000,scientificControl='round34',initializationParent='round28',adoptionAnchor='round25',oneChangedLearningFactor=p['humanUtteranceEndEos'],selection='Unchanged pure common weighted exposed DEV CE at0/every500; no generation-based selection',strictGatesUnchanged=True,dailyPriority=True,samePositiveExposureAndRngMustBeVerified=True,terminalSeparateIfDifferent=True,notNewTest=True,publicModelChanged=False))
D=E/'prospective-eos-objective';D.mkdir()
for n in ['audit_end_markers.py','end-marker-counts.json','audit_eligible_end_rows.py','eligible-end-row-counts.json','check_candidate_objective.py','synthetic-objective-checks.json','check_full_training_masks.py','full-training-mask-checks.json','replay_candidate_target_mass.py','candidate-target-mass-replay.json','utterance_end_objective.py','HYPOTHESIS.md']:
 if (prep/n).exists():shutil.copy2(prep/n,D/n)
write(D/'provenance.json',dict(scope='Previously executed TRAIN-only prospective checks while Round34 ran; NOT Round35 optimizer updates or language results',files={p.name:sha(p)for p in D.iterdir()if p.is_file()},actualRound35OptimizerUpdates=0))
(R/'README.md').write_text('# Round35 — human utterance-end EOS auxiliary\n\nActual new optimizer updates0; preflight pending. Paired sibling of Round34 from identical aligned Round28 model/Adam20000/Torch/private Python RNG, lineage59000; same10000 dose. Only learning change: coefficient1.0 additional EOS2 CE where a human TRAIN true utterance-end original unmasked target is standalone newline16; summed and divided by original valid target count. Original newline CE remains. R34 negative prefix selection remains. No other learning/decoding/data change or new TEST. Daily conversation is priority; ending alone cannot establish meaning. Strict gates and pure-CE DEV selector unchanged; public model and R25 adoption anchor unchanged.\n')
(R/'REPRODUCTION.md').write_text('# Round35 prospective reproduction\n\nRestore and verify Round28 full terminal checkpoint and Round34 zero/latest paired states from their lossless chunks and artifact manifests. Preflight original data, targets, boundary maps, all masks, numerical objective gradients and exact no-eligible control, sampling, runtime gradients, Adam/RNG and full initial DEV before launching the fixed10000-update run. Never restart an already completed run. Resume incomplete nonrunning checkpoint with execution/run.sh --resume, preserving exact settings, model, moments, counters and RNG. Original gold CE and all R34 negative prefix logic retained; only auxiliary EOS coefficient1.0 changes. Same original strict gates, all raw output saving and Python/JS comparisons; no new TEST or public replacement.\n')
shutil.copy2(pathlib.Path(__file__),E/'prepare_trial.py')
print('Created prospective Round35 only; actual optimizer updates0. Complete all audits before freeze/launch.')
