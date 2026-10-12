"""Freeze final artifacts only after actual counters and comparison are audited."""
import pathlib,json,hashlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=read(ROOT/'continue-10000/result.json');audit=read(ROOT/'execution/optimizer-audit.json');comparison=read(ROOT/'execution/comparison.json');policy=read(ROOT/'policy.json')
assert r['completedRun'] and r['completedSteps']==r['requestedSteps']==10000
assert audit['actualCompletedUpdates']==comparison['actualCompletedUpdates']==10000
assert audit['checkpointSha256']==r['checkpointSha256']==sha(ROOT/'continue-10000/checkpoint.pt')
assert comparison['models']['new']['modelSha256']==audit['modelSha256']==sha(ROOT/'continue-10000/model.js')
paths={p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact-manifest.json' and p.suffix!='.tmp'}
external=['../model.py','../round10/reproducibility-manifest.json','../round10/word-512-continue-10000/checkpoint.pt','../round10/word-512-continue-10000/model.js','../round10/word-512-continue-10000/validation.json','../round10/word-512-continue-10000/validation-manual.json','../round10/full-meaning-policy.json','../round10/evaluate.py','../round10/evaluate_js.mjs','../round10/review.py','../round10/train.py','../round8/generation-policy.json','../round6/generation-policy.json','../../dialogue/inference.mjs','../../dialogue/tokenizer.py']
external+=['../round10/'+p for p in policy['sourceHashes']]
paths.update(ROOT/p for p in external)
files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths,key=str)]
manifest=dict(schemaVersion=1,baseGitCommit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),partialRunGitCommit='d69389e8f93e6aeb70deb684d635787a947896a6',actualCompletedUpdates=10000,requestedUpdates=10000,remainingUpdates=0,completedRun=True,selectedStep=r['bestStep'],naturalJapaneseEstablished=comparison['naturalJapaneseEstablished'],developmentLanguageGatePassed=comparison['developmentLanguageGatePassed'],testEncodedOrGenerated=False,publicModelReplaced=False,trainingStopped=True,scope='Completed run, unmodified development outputs, assistant review and referenced source/code identities; excludes only itself, temporary files and Python caches; step1000 historical artifacts are preserved in partialRunGitCommit',files=files)
(ROOT/'execution/artifact-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(frozenFiles=len(files),actualCompletedUpdates=10000,selectedStep=r['bestStep'])))
