"""Reproducible post-selection measurements; never performs model training.

Sequential execution keeps training and Python work out of the local JS timing.
Install only the compute dependencies for Python; no outside model downloads.
Manual quality reviews are deliberately separate from these raw measurements.
"""
import json,pathlib,subprocess,sys

root=pathlib.Path(__file__).resolve().parents[2]
p='training/dialogue/'
model=p+'switch-candidate.js';corpus=p+'switch-corpus.json';audit=p+'switch-audit.json'
raw=json.loads((root/model).read_text().split('export const dialogueModel=',1)[1].strip().removesuffix(';'))
data=json.loads((root/corpus).read_text())
assert raw['training']['sourceSha256']==data['sourceSha256'],'Refuse mixed model/corpus artifacts'
assert raw['training']['completedSteps']==11000,'This experiment requires a completed1000+10000 run'
commands=[
 [sys.executable,p+'evaluate.py','--model',model,'--corpus',corpus,'--out',p+'switch-test-results.json'],
 [sys.executable,p+'evaluate.py','--model',model,'--corpus',corpus,'--partition','validation','--out',p+'switch-full-validation-results.json'],
 [sys.executable,p+'evaluate.py','--model',model,'--corpus',audit,'--out',p+'switch-audit-results.json'],
 [sys.executable,p+'evaluate_language.py','--model',model,'--corpus',corpus,'--out',p+'switch-language-results.json'],
 [sys.executable,p+'evaluate_partition_loss.py','--model',model,'--corpus',corpus,'--out',p+'switch-partition-loss-results.json'],
 [sys.executable,p+'evaluate_semantic.py','--model',model,'--corpus',corpus,'--audit',audit,'--out',p+'switch-semantic-results.json'],
 ['node',p+'evaluate_js.mjs','--model',model,'--corpus',corpus,'--out',p+'switch-js-results.json'],
 ['node',p+'evaluate_js.mjs','--model',model,'--corpus',audit,'--out',p+'switch-audit-js-results.json'],
 ['node',p+'evaluate_rollouts.mjs','--model',model,'--corpus',p+'switch-rollouts.json','--out',p+'switch-rollout-results.json'],
 ['node',p+'benchmark_prefix_cache.mjs','--model',model,'--corpus',p+'switch-rollouts.json','--out',p+'switch-cache-benchmark.json'],
 ['node',p+'evaluate_raw_generation.mjs','--model',model,'--corpus',p+'switch-raw-probes.json','--out',p+'switch-raw-results.json'],
 ['node',p+'evaluate_js.mjs','--model',model,'--corpus',audit,'--beam-size','4','--length-penalty','0.6','--out',p+'switch-beam-audit-results.json'],
 ['node',p+'evaluate_rollouts.mjs','--model',model,'--corpus',p+'switch-rollouts.json','--beam-size','4','--length-penalty','0.6','--out',p+'switch-beam-rollout-results.json'],
]
for command in commands:
    print('RUN '+' '.join(command),flush=True)
    subprocess.run(command,cwd=root,check=True)
