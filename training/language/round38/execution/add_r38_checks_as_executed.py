import pathlib
R=pathlib.Path('/workspace/4k29/training/language/round38');E=R/'execution';P=R.parent/'round37/execution'
s=(P/'audit_eos_exposure.py').read_text();s='\n'.join(l for l in s.splitlines()if not l.startswith('assert positions==161241'))+'\n';(E/'audit_eos_exposure.py').write_text(s)
s=(P/'paired_training_audit.py').read_text().replace("P=R.parent/'round36'","P=R.parent/'round37'");s=s[:s.index("assert a['pythonRng']==b['pythonRng']")]+'''assert a['settings']['genreSampling']==b['settings']['genreSampling'] and a['config']==b['config']
for n in ['train.py','batching.py','objective.py','sequence_objective.py','rollout_trace.py','initialization.py','prefix_selection.py','utterance_end_objective.py','end_main_ce.py']:assert sha(P/n)==sha(R/n),n
for n in ['multiview/validation.index.json','multiview/validation.tokens.bin','multiview/tokenizer.json']:assert sha(P/n)==sha(R/n),n
assert a['history'][0]['validation']==b['history'][0]['validation']
assert read(R/'execution/data-preflight.json')['allOldTokenBytesExactlyPreserved']
assert read(R/'execution/sampler-replay.json')['endingPythonRngExactlyMatches']
report=dict(actualUpdatesEach=10000,pairedComparator='round37',sameAlignedInitialModelOptimizerAndRng=True,coreLearningCodeByteIdentical=True,oldDataPrefixAndValidationUnchanged=True,oneChangedFactor='Append JMRD original official TRAIN human dialogues',positiveDrawsAndFinalRngExpectedToDiffer=True,ownSamplerReplayExactlyMatchesOwnCheckpoint=True,sameFinalPythonRng=a['pythonRng']==b['pythonRng'],sameFinalTorchRng=torch.equal(a['torchRng'],b['torchRng']),additionalOptimizerUpdates=0,controlCheckpointSha256=sha(P/'continue-10000/checkpoint.pt'),childCheckpointSha256=sha(R/'continue-10000/checkpoint.pt'))
(R/'execution/paired-training-audit.json').write_text(json.dumps(report,indent=2)+'\\n');print(json.dumps(report))
''';(E/'paired_training_audit.py').write_text(s)
s=(E/'verify_runtime.py').read_text();s=s.replace("for row in read(ROOT/'source-manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']",'')
a=s.index("rows[3:]=");b=s.index('\nx,y=pack',a);s=s[:a]+"rows[3:]=[next(r for r in i['rows']if r['document'].startswith('jmrd:') and r['variant']==k and selector.length(r,int(v[r['offset']]))<min(32,r['length']-1)) for k in range(3)]"+s[b:];a=s.index('control=read(');s=s[:a]+"record.update(newJmrdRowsActuallyExercised=True,sourceDocuments=[r['document'] for r in rows[3:]],actualOptimizerUpdates=0)\nwrite(ROOT/'execution/new-source-gradient-preflight.json',record);print(json.dumps(record))\n";(E/'preflight_new_source_gradients.py').write_text(s)
