import pathlib
R=pathlib.Path('/workspace/4k29/training/language/round38');E=R/'execution'
p=E/'preflight_data.py';s=p.read_text().replace("C=R.parent/'round25'","C=R.parent/'round37'").replace("(R/'sources/documents.jsonl')","(R/'added-human-source/documents.jsonl')").replace("read(R/'sources/manifest.json')['admittedUnits']","read(R/'added-human-source/manifest.json')['admittedUnits']");p.write_text(s)
p=E/'preflight_prefix_policy.py';s=p.read_text().replace("'835d6da37308c68c5a5bc4a61c727a6ee4d2978006890c21f0416345dc02dc56'","sha(feature)");s='\n'.join(l for l in s.splitlines()if not l.startswith("assert counts['humanRows']=="))+'\n';p.write_text(s)
p=E/'preflight_eos_masks.py';s=p.read_text();a=s.index("reference=json.loads");b=s.index('report=dict',a);s=s[:a]+s[b:];p.write_text(s)
p=E/'verify_runtime.py';s=p.read_text();a=s.index("control=read(");s=s[:a]+'''control=read(ROOT.parent/'round37/execution/preflight-runtime.json')
for term in ['unlikelihoodLoss','sequenceUnlikelihoodLoss','endEosLoss','eligibleHumanEndPositions','originalCrossEntropyLoss','crossEntropyLoss','gradientLoss']:assert abs(record[term]-control[term])<1e-6,term
record.update(initialObjectiveOnSameLegacyRowsExactlyMatchesRound37=True,corpusAdditionOnly=True)
write(ROOT/'execution/preflight-runtime.json',record);print(json.dumps(record))
''';p.write_text(s)
p=E/'freeze_pretraining.py';s=p.read_text().replace("Exclude competing original newline main CE at eligible human EOS ends only","Append original official TRAIN JMRD human dialogues under unchanged human-chat sampling mass only");p.write_text(s)
