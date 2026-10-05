"""Sequential post-selection reproduction, never fitting or selecting weights."""
import json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2];p='training/dialogue/'
model=p+'owner-aligned-candidate.js';corpus=p+'owner-aligned-corpus.json';audit=p+'owner-aligned-audit.json'
export=json.loads((root/model).read_text().split('export const dialogueModel=',1)[1].strip().removesuffix(';'));c=json.loads((root/corpus).read_text())
assert export['training']['sourceSha256']==c['sourceSha256']
assert export['training']['completedSteps']==11000
assert export['training']['randomInitialization'] is False
assert export['training']['ownInitialModel']['sourceSha256']==c['provenance']['parentCorpusSha256']
commands=[
 [sys.executable,p+'reference_extended.py','--model',model,'--corpus',corpus,'--out',p+'owner-aligned-extended-reference.json'],
 [sys.executable,p+'evaluate.py','--model',model,'--corpus',audit,'--out',p+'owner-aligned-pytorch-audit-results.json'],
 ['node',p+'evaluate_js.mjs','--model',model,'--corpus',audit,'--out',p+'owner-aligned-audit-results.json'],
 ['node',p+'evaluate_rollouts.mjs','--model',model,'--corpus',p+'owner-aligned-rollouts.json','--out',p+'owner-aligned-rollout-results.json'],
 ['node',p+'evaluate_raw_generation.mjs','--model',model,'--corpus',p+'owner-aligned-raw-probes.json','--out',p+'owner-aligned-raw-results.json'],
 ['node',p+'evaluate_owner_feedback.mjs','--model',model,'--out',p+'owner-aligned-owner-feedback-results.json'],
 ['node',p+'evaluate_js.mjs','--model',p+'switch-candidate.js','--corpus',p+'owner-aligned-regression-audit.json','--out',p+'owner-aligned-baseline-regression-results.json'],
 ['node',p+'evaluate_js.mjs','--model',model,'--corpus',p+'owner-aligned-regression-audit.json','--out',p+'owner-aligned-regression-results.json'],
 [sys.executable,p+'evaluate_language.py','--model',p+'switch-candidate.js','--corpus',corpus,'--unit','streams','--allow-own-parent','--out',p+'owner-aligned-baseline-language-results.json'],
 [sys.executable,p+'evaluate_language.py','--model',model,'--corpus',corpus,'--unit','streams','--out',p+'owner-aligned-language-results.json'],
 [sys.executable,p+'evaluate_partition_loss.py','--model',model,'--corpus',corpus,'--out',p+'owner-aligned-partition-loss-results.json'],
 [sys.executable,p+'evaluate.py','--model',model,'--corpus',corpus,'--out',p+'owner-aligned-test-results.json'],
 ['node',p+'evaluate_js.mjs','--model',model,'--corpus',corpus,'--out',p+'owner-aligned-js-test-results.json'],
 ['node',p+'benchmark_bpe.mjs','--model',model,'--corpus',p+'owner-aligned-rollouts.json','--out',p+'owner-aligned-bpe-benchmark.json'],
]
for command in commands:
 print('RUN '+' '.join(command),flush=True);subprocess.run(command,cwd=root,check=True)
py=json.loads((root/(p+'owner-aligned-pytorch-audit-results.json')).read_text());js=json.loads((root/(p+'owner-aligned-audit-results.json')).read_text())
py_test=json.loads((root/(p+'owner-aligned-test-results.json')).read_text());js_test=json.loads((root/(p+'owner-aligned-js-test-results.json')).read_text())
for a,b in [(py,js),(py_test,js_test)]:
 expected={r['id']:r for r in a['rows']}
 for r in b['rows']:
  for key in ['answer','exact','eos','validTokens']:assert r[key]==expected[r['id']][key],(r['id'],key)
print('Complete PyTorch/JS full-answer parity on '+str(py['total']+py_test['total'])+' rows',flush=True)
