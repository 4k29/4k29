import pathlib,subprocess,json,hashlib,shutil,os
repo=pathlib.Path('/workspace/4k29');B=repo/'training/language';P=B/'round44';R=B/'round45';E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def advance(s):return s.replace('round44','__N__').replace('Round44','__NC__').replace('R44','__NS__').replace('round43','round44').replace('Round43','Round44').replace('R43','R44').replace('__N__','round45').replace('__NC__','Round45').replace('__NS__','R45')
assert not R.exists()and not subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip();assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()=='e8b5b51538beb71c1b74ea78755b396bbb1ee9fe'
assert read(B/'round44-verification.json')['trackingClosureVerified'];assert read(P/'execution/final-assessment.json')['actualCompletedUpdates']==10000
# Preparation is reversible and may proceed during control CI; verify exact control final CI before launching training.
control_ci=pathlib.Path('/workspace/ROUND44_FINAL_CI.json')
if control_ci.exists():
 ci=read(control_ci);assert ci['headSha']=='e8b5b51538beb71c1b74ea78755b396bbb1ee9fe'and ci['conclusion']=='success'
subprocess.run(['git','switch','-c','experiment/round45-context-ce-coefficient'],cwd=repo,check=True);E.mkdir(parents=True)
core=['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','prefix_selection.py','utterance_end_objective.py','end_main_ce.py','context_preference.py']
for n in core+['checkpoint_chunks.py','.gitignore','.gitattributes','human-turn-token-boundaries.json']:shutil.copy2(P/n,R/n)
for n in ['multiview','sources','prospective-daily-source','added-human-source']:shutil.copytree(P/n,R/n,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.log'))
initial=subprocess.check_output(['git','ls-tree','-r','--name-only','3298933','--','training/language/round44/execution'],cwd=repo,text=True).splitlines()
for name in initial:
 rel=pathlib.Path(name).relative_to('training/language/round44');src=P/rel;dst=R/rel
 if src.suffix in ['.py','.sh','.mjs']or'content-native-dev'in rel.parts:
  dst.parent.mkdir(parents=True,exist_ok=True)
  if src.suffix in ['.py','.sh','.mjs']:dst.write_text(advance(src.read_text()))
  else:shutil.copy2(src,dst)
shutil.copy2(P/'execution/diagnose_parity.mjs',E/'diagnose_parity.mjs')
for n in ['daily-probes.json','DAILY_REVIEW_PROTOCOL.md','HUMAN_DAILY_DEV_PROTOCOL.md','human-train-gap-plan.json','terminal-diagnostic-plan.json','context-plan.json','context-auxiliary-pool.json','context-original-candidates.json']:shutil.copy2(P/'execution'/n,E/n)
shutil.copytree(P/'fixed-source-mrmp-dev',R/'fixed-source-mrmp-dev',ignore=shutil.ignore_patterns('__pycache__'))
for n in ['evaluate.py','after_final.py']:
 f=R/'fixed-source-mrmp-dev'/n;f.write_text(advance(f.read_text()))
(E/'retained-snapshots').mkdir();(E/'retained-snapshots/.gitignore').write_text('*/checkpoint.pt\n')
p=read(P/'policy.json');assert p['contextPreference']['coefficient']==.1;p['contextPreference']['coefficient']=.2
factor='Only correct-context CE coefficient0.1 to0.2; same main sampling40%/5%, all10 core files and1024pool'
p.update(experiment='Round45: '+factor,controlManifestSha256=sha(P/'execution/artifact-manifest.json'),nllSuccessThreshold=read(P/'continue-10000/metrics.json')['bestValidationNllPerByte'],rationale=dict(evidence='R44 human NLL/context gain improved but selected dailywhole0/12; terminal had2 short daily successes and more native loops',hypothesis='Increase only original human correct-context CE contribution to test contextual response learning',limits='No new source/role tags/model/LR/seed/dose/selector/gates; not an R44 terminal extension'))
write(R/'source-policy.json',dict(scientificControl='round44',oneChangedFactor=factor,allMainDataBytesIdenticalToRound44=True,allTenCoreLearningFilesByteIdentical=True,mainSamplingExactlyPreserved=True,newDataOrTokenizerOrTestAccess=False));p['sourcePolicySha256']=sha(R/'source-policy.json');write(R/'policy.json',p)
write(E/'creation-context.json',dict(scientificControl='round44',secondaryControl='round39',initializationParent='round28',adoptionAnchor='round25',oneChangedFactor=factor,actualUpdatesAtCreation=0,mainExposureEqualityExpected=True,initialFullStateEqualityRequired=True))
plan=read(P/'execution/prospective-evaluation-plan.json');plan.update(scientificControl='round44',oneChangedFactor=factor,sameAllDataBytesAndSampling=True,sameSampling=True,mainExposureEqualityExpected=True);write(E/'prospective-evaluation-plan.json',plan)
plan=read(P/'execution/interim-plan.json');plan.update(at1000='Fixed humanDEV99 rawNLL, TRAIN64 diagnosis, same daily12 raw greedy192 against R44 actual1000 full state',mainExposureEqualityExpected=True,earlyTensorIdentityNotExpected=True);write(E/'interim-plan.json',plan)
write(E/'diagnostic-plan-reuse.json',dict(actualUpdatesAtCreation=0,fixedTrain64Sha256=sha(E/'context-plan.json'),poolSha256=sha(E/'context-auxiliary-pool.json'),poolBytesExactlyEqualToRound44=True,train64ExactPoolOverlap=7,trainingDiagnosticNotHeldout=True,noReselection=True))
for n in ['manual-source-sample-plan.json','manual-source-sample-audit.json']:write(E/n,dict(actualOptimizerUpdates=0,priorRound44Artifact=str((P/'execution'/n).relative_to(repo)),priorSha256=sha(P/'execution'/n),poolSha256=sha(E/'context-auxiliary-pool.json'),historicalReadingReusedAfterExactPoolAndDataIdentity=True,noNewFullSemanticReadingClaim=True,notAll1024SemanticAudit=True))
write(E/'pool-selection-proof.json',dict(actualOptimizerUpdates=0,poolBytesExactlyEqualToRound44=True,poolSha256=sha(E/'context-auxiliary-pool.json'),selectedPairs=1024,positiveDocuments=403,train64ExactPositivePairOverlap=7,allTrainOnly=True,candidateOrderOrDonorsOrTextChanged=False))
write(E/'learning-code-delta-proof.json',dict(actualOptimizerUpdates=0,oneChangedPolicyField='contextPreference.coefficient',oldValue=.1,newValue=.2,allTenCoreLearningFilesByteIdentical=all((R/n).read_bytes()==(P/n).read_bytes()for n in core),sameMainSamplingAndData=True))
f=E/'diagnose_paired_1000_daily.py';f.write_text(f.read_text().replace('for n in [43,44]','for n in [44,45]'));assert 'for n in [44,45]'in f.read_text()
f=E/'pin_terminal_control.py';f.write_text(f.read_text().replace('controlRound=43','controlRound=44'))
f=E/'preflight_context.py';s=f.read_text().replace('coefficientFixedBeforeGradients=.1',"coefficientFixedBeforeGradients=p['contextPreference']['coefficient']").replace('weightedAuxToReferenceCeGradientRatio=.1*aux/base',"weightedAuxToReferenceCeGradientRatio=p['contextPreference']['coefficient']*aux/base");f.write_text(s)
f=E/'preflight_sampling_probabilities.py';s=f.read_text().replace('p/old[g],.55/.7','p/old[g],1.0').replace("(R/'batching.py').read_bytes().replace(b\"'realpersona':.40\",b\"'realpersona':.25\")","(R/'batching.py').read_bytes()").replace('onlyOneBatchingSourceMassLiteralChanged=True,otherNineLearningFilesByteIdentical=True','samplingExactlyMatchesControl=True,allTenLearningFilesByteIdentical=True');f.write_text(s)
f=E/'paired_training_audit.py';s=f.read_text().replace("(R/'batching.py').read_bytes().replace(b\"'realpersona':.40\",b\"'realpersona':.25\")","(R/'batching.py').read_bytes()").replace('allOtherNineCoreLearningFilesByteIdentical=True,batchingOnlyDeclaredSourceMassLiteralChanged=True','allTenCoreLearningFilesByteIdentical=True,batchingExactlyUnchanged=True').replace('positiveDrawsAndFinalRngExpectedToMatch=False,exposureDifferencesIntrinsic=True','positiveDrawsAndFinalRngExpectedToMatch=True,exposureDifferencesIntrinsic=False').replace('Main RealPersona probability25% to40%, JMRD5% fixed, other relative proportions preserved',factor);f.write_text(s)
f=E/'compare_losses.py';s=f.read_text().replace('exposureEqualityRequired=False','exposureEqualityRequired=True').replace('mixtureChanged=True,exposureDifferencesIntrinsic=True','mixtureChanged=False,exposureDifferencesIntrinsic=False');f.write_text(s)
for name in ['freeze_pretraining.py','publish_mechanical.py','pin_secondary_control.py']:
 f=E/name;s=f.read_text().replace('Only main RealPersona probability25% to40%',factor).replace('ONLY increase main RealPersona probability25% to40%','ONLY increase correct-context CE coefficient0.1 to0.2').replace('one new main-source-probability training condition','one new context-CE-coefficient training condition');f.write_text(s)
(R/'README.md').write_text('# R45 — correct-context CE coefficient0.1 to0.2 only\n\n実更新0、開始前監査中。全10core files/資料/主sampling40%+5%/pool1024/他loss/model/LR/seed/R28fullstate/10000dose/selector/gatesはR44と同じ。係数だけ0.1→0.2。意味改善は未測定、公開/R25anchor維持。\n')
(R/'REPRODUCTION.md').write_text('# R45 reproduction\n\n実更新0。入力・勾配・初期fullstate・全診断用実行ファイルclosureを開始前に検証する。実学習を未実施のまま完了扱いしない。\n')
(R/'WORKSPACE_STORAGE.md').write_text((P/'WORKSPACE_STORAGE.md').read_text()+'\nR45も同じlocal sparse layoutを利用し、データ/履歴の一意な削除は行わない。\n')
shutil.copy2(pathlib.Path(__file__),E/'prepare_trial.py');print('R45 prepared at actual0; learning code byte-identical; preflight and frozen metadata consistency still required.')
