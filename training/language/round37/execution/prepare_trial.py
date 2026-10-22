"""Create one prospective main-CE exclusion trial, not actual training."""
import pathlib,shutil,json,hashlib,subprocess,re,datetime
repo=pathlib.Path('/workspace/4k29');B=repo/'training/language';P=B/'round36';R=B/'round37';E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def advance(s):
 for a,b in [('round36','__LOW__'),('Round36','__CAP__'),('R36','__ABBR__')]:s=s.replace(a,b)
 for a,b in [('round35','round36'),('Round35','Round36'),('R35','R36')]:s=s.replace(a,b)
 return s.replace('__LOW__','round37').replace('__CAP__','Round37').replace('__ABBR__','R37')
assert not R.exists()and not subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip()
assert read(P/'execution/final-assessment.json')['fullOutputReviewPending']is False
subprocess.run(['git','switch','-c','experiment/round37-remove-competing-newline-ce'],cwd=repo,check=True);E.mkdir(parents=True)
for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','checkpoint_chunks.py','prefix_selection.py','utterance_end_objective.py','human-turn-token-boundaries.json','source-policy.json','.gitignore','.gitattributes']:shutil.copy2(P/n,R/n)
for n in ['multiview','sources','prospective-daily-source']:shutil.copytree(P/n,R/n,ignore=shutil.ignore_patterns('__pycache__'))
keep=re.search("keep='([^']+)'",pathlib.Path('/workspace/prepare_round34.py').read_text()).group(1).split()
keep+='test_prefix_selection.py test_utterance_end_objective.py preflight_prefix_policy.py preflight_eos_masks.py assess_terminal_state.py wait_terminal_diagnostic.py wait_human_train_gap.py human_train_sample_likelihood.py assemble_full_outputs.py assemble_three_states.py assemble_matched_terminal.py pin_terminal_control.py freeze_pretraining.py paired_training_audit.py audit_eos_exposure.py restore_referenced_chunks.py plot_paired_development.py describe_training_termination.py complete_mechanical_assembly.py retain_paired_milestones.py'.split()
for n in keep:
 if (P/'execution'/n).exists():(E/n).write_text(advance((P/'execution'/n).read_text()))
for n in ['daily-probes.json','DAILY_REVIEW_PROTOCOL.md','HUMAN_DAILY_DEV_PROTOCOL.md']:shutil.copy2(P/'execution'/n,E/n)
shutil.copytree(P/'execution/prospective-eos-objective',E/'prospective-eos-objective',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(P/'execution/content-native-dev',E/'content-native-dev',ignore=shutil.ignore_patterns('new-*','old-*','__pycache__'))
shutil.copytree(P/'fixed-source-mrmp-dev',R/'fixed-source-mrmp-dev',ignore=shutil.ignore_patterns('__pycache__'))
for n in ['evaluate.py','after_final.py']:
 p=R/'fixed-source-mrmp-dev'/n;p.write_text(advance(p.read_text()))
for n in ['human-train-gap-plan.json','terminal-diagnostic-plan.json']:
 d=read(P/'execution'/n);d['inheritedPlanPreparedUtc']=d['preparedUtc'];d['preparedUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['inheritedFromRound36WithIdenticalInputs']=True;d['priorRound36PlanSha256']=sha(P/'execution'/n);write(E/n,d)
helper='''"""Remove competing original newline CE only at the existing true-end EOS mask."""
import torch
from torch.nn import functional as F
def main_ce_without_end_newline(logits,targets,end_mask,newline_id=16):
    if end_mask.dtype!=torch.bool or end_mask.shape!=targets.shape:raise ValueError('Invalid end mask')
    if bool((end_mask & targets.ne(newline_id)).any()):raise ValueError('Only original standalone-newline targets may be excluded')
    valid=targets.ne(-100).sum()
    if int(valid)==0:raise ValueError('No valid targets')
    original=F.cross_entropy(logits.reshape(-1,logits.shape[-1]),targets.reshape(-1))
    if not bool(end_mask.any()):return original,original,original.new_zeros(())
    removed=F.cross_entropy(logits[end_mask],targets[end_mask],reduction='sum')/valid
    return original-removed,original,removed
'''
(R/'end_main_ce.py').write_text(helper)
patches=[
('from utterance_end_objective import eligible_mask, end_eos_loss','from utterance_end_objective import eligible_mask, end_eos_loss\nfrom end_main_ce import main_ce_without_end_newline',1),
("and policy['humanUtteranceEndEos']['coefficient']==0.3","and policy['humanUtteranceEndEos']['coefficient']==0.3 and policy['originalNewlineCeAtEligibleEnds']['excluded'] is True",1),
("settings['humanUtteranceEndEos']=policy['humanUtteranceEndEos']","settings['humanUtteranceEndEos']=policy['humanUtteranceEndEos']\n    settings['originalNewlineCeAtEligibleEnds']=policy['originalNewlineCeAtEligibleEnds']",1),
('same raw targets + 0.3 EOS auxiliary only at original unmasked standalone-newline human TRAIN true utterance ends','same raw targets + 0.3 EOS auxiliary only at original unmasked standalone-newline human TRAIN true utterance ends; exclude only competing original newline main CE with original valid-target denominator retained',1),
("ce=F.cross_entropy(logits.reshape(-1,config['vocabulary']),y.reshape(-1))","ce,original_ce,removed_ce=main_ce_without_end_newline(logits,y,end_mask)",1),
('count,aux.detach()','count,aux.detach(),original_ce.detach(),removed_ce.detach()',1),
('loss,ce_loss,ul_loss,negative_count,end_eos_loss_value=train_objective','loss,ce_loss,ul_loss,negative_count,end_eos_loss_value,original_ce_loss,removed_ce_loss=train_objective',1),
('crossEntropyLoss=float(ce_loss),','crossEntropyLoss=float(ce_loss),originalCrossEntropyLoss=float(original_ce_loss),removedEligibleNewlineCe=float(removed_ce_loss),',2)]
s=(P/'train.py').read_text()
for old,new,count in patches:assert s.count(old)==count,(old,s.count(old));s=s.replace(old,new)
(R/'train.py').write_text(s);write(E/'trainer-change-spec.json',dict(controlTrainSha256=sha(P/'train.py'),newTrainSha256=sha(R/'train.py'),patches=[dict(old=o,new=n,count=c)for o,n,c in patches],oneChangedLearningFactor='Exclude competing original newline main CE at existing eligible human EOS positions only'))
p=read(P/'policy.json');p.update(experiment='Round37: exclude competing original newline CE at existing human true-end EOS positions only; EOS coefficient0.3 unchanged',controlManifestSha256=sha(P/'execution/artifact-manifest.json'),nllSuccessThreshold=read(P/'continue-10000/metrics.json')['bestValidationNllPerByte']);p['originalNewlineCeAtEligibleEnds']=dict(excluded=True,eligibility='Exactly the existing human utterance-end EOS mask; original standalone-newline16 targets only',originalLabelsUnmodified=True,originalValidTargetDenominatorRetained=True,noneligibleTermsUnchanged=True)
p['rationale']=dict(evidence='R36 actual10000 and all84 new outputs read: NLL lower, daily loops8→12, native8 finite closures lost. Matched5000 authentic EOS argmax37→0 after weakening coefficient, original newline CE still competes.',hypothesis='Removing only competing newline CE may learn utterance termination without raising EOS coefficient; whether full content improves must be measured.',limitations='No data/target/tokenizer/LR/seed/other objective/inference change; original NL-gold DEV likelihood stays unchanged and may regress. No automatic meaning claim.')
p['practicalGuardReference']='Keep the exact Round36 fixed practical thresholds inherited from Round35, not the worse Round36 daily nonloop count. Scientific comparator is Round36.'
p['codeHashes']={n:sha(R/n)for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','prefix_selection.py','utterance_end_objective.py','end_main_ce.py']};write(R/'policy.json',p)
# Adapt the actual real-model zero-step audit to the one excluded main-CE component.
f=E/'verify_runtime.py';s=f.read_text();needle="ce=F.cross_entropy(logits.reshape(-1,m.config['vocabulary']),y.reshape(-1));";assert s.count(needle)==1;s=s.replace(needle,'ce,original_ce,removed_ce=main_ce_without_end_newline(logits,y,end_mask);');s=s.replace('crossEntropyLoss=ce.item(),','crossEntropyLoss=ce.item(),originalCrossEntropyLoss=original_ce.item(),removedEligibleNewlineCe=removed_ce.item(),')
start=s.index("for term in ['crossEntropyLoss'");end=s.index("write(ROOT/'execution/preflight-runtime.json'",start)
s=s[:start]+'''for term in ['unlikelihoodLoss','sequenceUnlikelihoodLoss','endEosLoss','eligibleHumanEndPositions']:assert record[term]==control[term],term
assert record['originalCrossEntropyLoss']==control['crossEntropyLoss']
assert abs(record['crossEntropyLoss']-(control['crossEntropyLoss']-record['removedEligibleNewlineCe']))<1e-6
expected=control['gradientLoss']-record['removedEligibleNewlineCe'];assert abs(record['gradientLoss']-expected)<1e-6
record.update(initialOtherObjectiveTermsExactlyMatchRound36=True,onlyEligibleOriginalNewlineCeRemoved=True,originalValidTargetDenominatorRetained=True,expectedCombinedObjectiveFromRound36=expected)
'''+s[end:];f.write_text(s)
f=E/'freeze_pretraining.py';s=f.read_text().replace("'prefix_selection.py','utterance_end_objective.py']","'prefix_selection.py','utterance_end_objective.py','end_main_ce.py']").replace("'execution/adoption-decision.json',",'').replace('Human true utterance-end EOS auxiliary coefficient1.0 to0.3 only','Exclude competing original newline main CE at eligible human EOS ends only');f.write_text(s)
f=E/'pin_terminal_control.py';f.write_text(f.read_text().replace('controlRound=35','controlRound=36'))
f=E/'paired_training_audit.py';f.write_text(f.read_text().replace('onlyHumanEndEosCoefficientChanged=True','onlyCompetingOriginalNewlineCeExclusionChanged=True'))
f=E/'publish_mechanical.py';f.write_text(f.read_text().replace('ONLY human true-utterance-end EOS auxiliary coefficient1.0 to0.3','ONLY original newline main CE excluded at eligible human EOS positions; coefficient0.3 fixed'))
f=E/'plot_paired_development.py';f.write_text(f.read_text().replace('R36 EOS auxiliary coefficient1.0','R36 EOS coefficient0.3, original newline CE retained').replace('R37 EOS auxiliary coefficient0.3','R37 EOS coefficient0.3, competing newline CE excluded'))
f=E/'assemble_matched_terminal.py';f.write_text(f.read_text().replace('EOS auxiliary coefficient1.0 to0.3 as the sole learning-condition change','excluding competing original newline CE as the sole learning-condition change'))
# Record/infer current initial-state gradient and validation only; never synthesize final results.
write(E/'creation-context.json',dict(scientificControl='round36',initializationParent='round28',adoptionAnchor='round25',oneLearningFactor='Exclude original newline main CE at existing eligible human EOS positions',parentOptimizerUpdates=20000,parentWeightLineageUpdates=59000,actualNewOptimizerUpdates=0))
write(E/'prospective-evaluation-plan.json',dict(actualOptimizerUpdatesAtFreeze=0,requestedUpdates=10000,scientificControl='round36',initializationParent='round28',adoptionAnchor='round25',oneChangedLearningFactor='Exclude original newline CE only at already eligible EOS positions',selection='Unchanged pure original-gold common DEV CE every500',strictGatesUnchanged=True,practicalThresholdsExactlyInherited=p['supplementaryEverydayDevelopment'],goldLikelihoodEvaluationUnchanged=True,samePositiveExposureAndRngMustBeVerified=True,terminalSeparateIfDifferent=True,notNewTest=True,publicModelChanged=False))
(R/'README.md').write_text('# Round37 prospective — remove competing original newline CE\n\nActual updates0; preflight pending. Only main CE at already eligible human true-end EOS positions is excluded. EOS coefficient0.3, original valid-target denominator, data/labels/tokenizer/sampling/LR/seed/all other objectives/inference/strict gates remain fixed. Same aligned Round28 parent and10000 actual-update budget. Original NL-gold DEV likelihood remains unchanged, including possible regression. Practical floors remain exactly those inherited by Round36, not lowered to its worse loops.\n')
(R/'REPRODUCTION.md').write_text('# Prospective exact reproduction\n\nRestore SHA-bound own inputs and same aligned Round28 model/Adam/RNG. Verify exact trainer reverse patch, helper losses/gradients/no-mask equivalence, all147986 TRAIN masks, real gradients, initial full DEV equality and runtime before launch. Source SHA and policy frozen at0. Resume only incomplete nonrunning own checkpoints with full moments/RNG/counters; never restart a completed10000 run. No new TEST/public model/site changes.\n')
(E/'SUPPLEMENTAL_PROVENANCE.md').write_text('Inherited probes, source plans and boundary-map prototype markers retain historical provenance, not newly executed R37 outcomes. No new TRAIN source. Same old-control reading reuse only after exact full-core identity. No score, numerical parity or language success claimed before actual execution/reading.\n')
shutil.copy2(pathlib.Path(__file__),E/'prepare_trial.py');print('Prepared Round37 only, actual updates0; preflight and freeze required before launch')
