import pathlib,shutil,subprocess,json,hashlib,re,os
repo=pathlib.Path('/workspace/4k29');P=repo/'training/language/round38';R=P.parent/'round39';E=R/'execution'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def advance(s):return s.replace('round38','__NEW__').replace('Round38','__NEWCAP__').replace('R38','__NEWAB__').replace('round37','round38').replace('Round37','Round38').replace('R37','R38').replace('__NEW__','round39').replace('__NEWCAP__','Round39').replace('__NEWAB__','R39')
assert not R.exists() and not subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip()
assert read(P/'continue-10000/result.json')['completedSteps']==10000
subprocess.run(['git','switch','-c','experiment/round39-human-source-balance'],cwd=repo,check=True);E.mkdir(parents=True)
for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','checkpoint_chunks.py','prefix_selection.py','utterance_end_objective.py','end_main_ce.py','.gitignore','.gitattributes','human-turn-token-boundaries.json']:shutil.copy2(P/n,R/n)
# Immutable input bytes only, hardlinks avoid redundant local disk usage. Never rewrite these files.
for n in ['multiview','sources','prospective-daily-source','added-human-source']:shutil.copytree(P/n,R/n,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.log'))
keep=re.search("keep='([^']+)'",pathlib.Path('/workspace/prepare_round34.py').read_text()).group(1).split()
keep+='test_prefix_selection.py test_utterance_end_objective.py test_end_main_ce.py preflight_prefix_policy.py preflight_eos_masks.py assess_terminal_state.py wait_terminal_diagnostic.py wait_human_train_gap.py human_train_sample_likelihood.py assemble_full_outputs.py assemble_three_states.py assemble_matched_terminal.py pin_terminal_control.py freeze_pretraining.py complete_mechanical_assembly.py paired_training_audit.py audit_eos_exposure.py preflight_new_source_gradients.py'.split()
for n in set(keep):
 if (P/'execution'/n).exists():(E/n).write_text(advance((P/'execution'/n).read_text()))
for n in ['daily-probes.json','DAILY_REVIEW_PROTOCOL.md','HUMAN_DAILY_DEV_PROTOCOL.md']:shutil.copy2(P/'execution'/n,E/n)
shutil.copytree(P/'execution/content-native-dev',E/'content-native-dev',ignore=shutil.ignore_patterns('new-*','old-*','__pycache__'))
for f in (E/'content-native-dev').glob('*.py'):f.write_text(advance(f.read_text()))
shutil.copytree(P/'fixed-source-mrmp-dev',R/'fixed-source-mrmp-dev',ignore=shutil.ignore_patterns('__pycache__'))
for n in ['evaluate.py','after_final.py']:
 f=R/'fixed-source-mrmp-dev'/n;f.write_text(advance(f.read_text()))
for n in ['human-train-gap-plan.json','terminal-diagnostic-plan.json']:shutil.copy2(P/'execution'/n,E/n)
# Code and explicit policy define the sole intervention.
f=R/'batching.py';s=f.read_text();start=s.index('    counts=');end=s.index('    masses=',start)
s=s[:start]+'''    source=lambda r: ('jmrd' if r['document'].startswith('jmrd:') else 'realpersona') if r['site']=='human-chat' else 'other'
    counts=collections.Counter((r['site'],r['variant'],source(r)) for r in rows)
    strata=collections.defaultdict(list)
    for r in rows:
        width=next(w for w in WIDTHS if r['length']-1<=w)
        strata[(r['site'],r['variant'],width,source(r))].append(r)
    source_masses={'realpersona':.25,'jmrd':.05}
    assert abs(genres['human-chat']-sum(source_masses.values()))<1e-12
    assert {k[2] for k in counts if k[0]=='human-chat'}==set(source_masses)
    weights={k:(source_masses[k[3]] if k[0]=='human-chat' else genres[k[0]])*VIEWS[k[1]]*len(v)/counts[(k[0],k[1],k[3])] for k,v in strata.items()}
'''+s[end:];f.write_text(s)
p=read(P/'policy.json');p.update(experiment='Round39: ONLY within-human source sampling balance RealPersona0.25 + JMRD0.05; total human0.30 unchanged',controlManifestSha256=sha(P/'execution/artifact-manifest.json'),nllSuccessThreshold=read(P/'continue-10000/metrics.json')['bestValidationNllPerByte'])
p['humanSourceSampling']={'realpersona':.25,'jmrd':.05};p['rationale']={'evidence':'R38 reduced common DEV NLL, worsened authentic everyday DEV and kept selected daily full meaning0/12; posthoc film derailments appeared.','hypothesis':'Restore existing everyday source exposure25% while retain JMRD5%, potentially recover authentic everyday loss and reduce topic derailment.','limitations':'One exposed-DEV seed; source draw changes lengths, positive histories and RNG, not a pure semantic-content mechanism; no other learning factor changes.'}
p['humanNegativePrefix']['noPositiveTargetOrSamplingChange']='Prefix policy unchanged; source sampling balance separately changes positive draws'
write(R/'source-policy.json',{'scientificControl':'round38','oneChangedFactor':'Within-human source mass only: RealPersona0.25 + JMRD0.05; total0.30','sourceWeights':p['humanSourceSampling'],'allDataBytesIdenticalToRound38':True,'upstreamProvenancePolicy':'../round38/source-policy.json','upstreamProvenancePolicySha256':sha(P/'source-policy.json'),'noNewAcquisitionOrTestAccess':True,'actualUpdatesAtFreeze':0})
p['sourcePolicySha256']=sha(R/'source-policy.json');write(R/'policy.json',p)
write(E/'creation-context.json',{'scientificControl':'round38','initializationParent':'round28','adoptionAnchor':'round25','oneChangedFactor':'Within-human source sampling weights only','actualUpdatesAtCreation':0})
write(E/'prospective-evaluation-plan.json',{'actualUpdatesAtFreeze':0,'requestedUpdates':10000,'scientificControl':'round38','oneChangedFactor':'Human source weights RealPersona25% JMRD5%','sameAlignedR28FullInitialState':True,'sameAllDataBytes':True,'ownSamplerReplayRequired':True,'oldFinalDrawsAndRngNeedNotMatch':True,'selector':'Unchanged common DEV lowest NLL at0/every500','humanDevBound':.9107185711429243,'dailyWholeBound':0,'dailyNonloopBound':4,'strictGates':[17,13,9],'all42SelectedAnd42TerminalFullOutputsMustBeRead':True,'allExposedDevelopmentNotTest':True,'publicModelChanged':False})
shutil.copy2('/workspace/ROUND38_FINAL_CI.json',E/'control-final-ci.json')
# Identical corpus, no appended documents; independently check every data file hash.
f=E/'preflight_data.py';f.write_text('''import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round38';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for n in ['multiview','sources','added-human-source','prospective-daily-source'] for p in (R/n).rglob('*') if p.is_file() and '__pycache__'not in p.parts]
for p in files:assert sha(p)==sha(P/p.relative_to(R)),str(p)
assert sha(R/'human-turn-token-boundaries.json')==sha(P/'human-turn-token-boundaries.json')
a=dict(actualOptimizerUpdates=0,allOldTokenBytesExactlyPreserved=True,allDataFilesByteIdenticalToRound38=True,verifiedFiles=len(files),allValidationAndTokenizerBytesExactlyPreserved=True,featureMapExactlyPreserved=True,noDataAcquisitionOrTestAccess=True)
(R/'execution/data-preflight.json').write_text(json.dumps(a,indent=2)+'\\n');print(a)
''')
f=E/'paired_training_audit.py';s=f.read_text().replace("['train.py','batching.py',","['train.py',").replace('coreLearningCodeByteIdentical=True','allOtherCoreLearningCodeByteIdentical=True').replace("oneChangedFactor='Append JMRD original official TRAIN human dialogues'","oneChangedFactor='Within-human source weights RealPersona25% JMRD5% only'")
s=s.replace("assert a['history'][0]", "assert sha(P/'batching.py')!=sha(R/'batching.py')\nfor n in ['train.index.json','train.tokens.bin']:assert sha(P/'multiview'/n)==sha(R/'multiview'/n)\nassert a['history'][0]");f.write_text(s)
f=E/'verify_runtime.py';s=f.read_text().replace('corpusAdditionOnly=True','withinHumanSourceWeightChangeOnly=True');f.write_text(s)
f=E/'compare_losses.py';s=f.read_text().replace('corpusAdditionNaturallyChangesPositiveTargets=True','sourceWeightChangeNaturallyChangesPositiveTargets=True');f.write_text(s)
f=E/'freeze_pretraining.py';s=f.read_text().replace("oneLearningFactor='Append original official TRAIN JMRD human dialogues under unchanged human-chat sampling mass only'","oneLearningFactor='Only within-human source sampling weights RealPersona25% JMRD5%'");f.write_text(s)
f=E/'publish_mechanical.py';s=f.read_text().replace('ONLY append original JMRD official TRAIN human dialogue corpus','ONLY adjust human source masses RealPersona25% JMRD5%').replace('LR, sampling masses and64-token','LR, total genre masses and64-token');f.write_text(s)
(R/'README.md').write_text('# Round39 — human source weights only\n\nActual optimizer updates0. RealPersona25% + JMRD5%, human total30%; exact R38 data, vocabulary, boundaries, all objectives, LR, seed,10000 dose, selector, inference and strict gates. Same aligned full R28 parent, not rejected R38 continuation. R25 anchor/public unchanged. Actual training and full generation assessment pending.\n')
shutil.copy2(pathlib.Path(__file__),E/'prepare_trial.py')
print('Prepared R39, actual optimizer updates0')
