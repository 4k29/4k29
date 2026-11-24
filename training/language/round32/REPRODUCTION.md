# Reproduction and exact continuation

Round32 changes only one executable line in sequence_objective.py versus adopted Round25: self-generated negative histories are scored in eval mode with gradients enabled; caller mode is restored in finally. CE remains in train mode. No suffix cleanup, human mixture, LR, horizon, architecture, vocabulary, source fold, decoding or acceptance change. Original copied multiview/data.json provenance remains Round25; current exact files are bound by source-manifest.json. diagnose_gap.py uses an old fixed TRAIN reference, not the full present TRAIN, and never proves whole-corpus generalization.

In a fresh checkout containing the tracked Round32 experiment before any run, the exact TRAIN tokens are tracked directly (48MiB), so no data download or chunk restore is required:

```bash
python -m unittest discover -s training/language/round32/execution -p 'test_*.py'
python training/language/round32/execution/verify_single_factor.py
python training/language/round32/execution/check_sampling.py
python training/language/round32/execution/verify_runtime.py
python training/language/round32/execution/preflight_initial_validation.py
bash training/language/round32/execution/persistent.sh
```

The checked-in policy/source-manifest is already frozen. Reproduction must use that exact source/data state, not rewrite policy or re-freeze after optimizer updates. verify_runtime loads existing own Round11 latest checkpoint/model/AdamW/RNG; it does not fit a tokenizer or use external weights. Full initial mixed-view DEV must exactly match0.9789190007498177 across every site/view, not merely a rounded scalar. All17 meaningful preflight tests (including synthetic toy resume tests) are distinct from actual Round32 optimizer updates, which start at0.

Actual trainer arguments are fixed in execution/execute.py: merges512, steps10000,dim192,layers8,heads4,batch8,threads2,seed2049,LR2.2499999999999998e-05,validation-every500,run continue-10000,precision float32. This is a sibling of Round25 from aligned Round11 latest state, not another10,000 updates added onto R31. Track real updates/selection separately in checkpoint.pt, train.log, result.json and optimizer-audit.json. Do not sum sibling round update counts as model lineage.

If and only if a partial run exists and no other training/controller holds the lock, restore the latest full checkpoint from its lossless chunks when raw files are missing, then resume the same run:

```bash
python training/language/round32/checkpoint_chunks.py restore training/language/round32/continue-10000/checkpoint.pt.chunks.json
bash training/language/round32/execution/persistent.sh --resume
```

Do not overwrite a newer raw checkpoint with older parts. Existing partial runs refuse restart without --resume; completed10000 runs refuse duplicate training. Full checkpoint contains aligned latest model/AdamW/Torch RNG/private Python RNG and counters. A selected inference snapshot has no matching optimizer/RNG and must never be combined with latest moments for resume. archive_best_aligned.py captures corresponding full selected states separately. Code/data/checkpoint numerical SHA can be verified; runtime/log timestamps and serialized archive-container SHA are not promised bit-identical across machines.

The durable supervisor runs original17 old/new generation+JS, full raw/export checks, daily12 comparisons, humanDEV99 loss, native8 and independent sampler/exposure audits after training. Midpoint monitor retains actual2000/5000 states if caught, with actual/selected steps separately labeled. Generation is greedy192 with unchanged own vocabulary and no repair. These are all exposed DEV, not fresh TEST, independent blind human scoring or proof of unseen generalization. Semantic judgments require actual complete reading after generation; mechanical pipeline never invents them. Prior old TEST-reference exposures in R29/R31 remain disclosed, so legacy references cannot be called human-blind. Never print/grep the compact mixed DEV/TEST generation-policy JSON; parse only explicitly whitelisted scalar fields when necessary. Keep known Round10 near-tie divergence visible. No public/site replacement without strict original language gates.

## Post-training evaluation recovery actually executed

The first completed-training controller stopped at inherited compare_losses.py because creation-context.json was missing. Recover its scientificControl=round25 from frozen execution/single-factor-audit.json, then run `bash training/language/round32/execution/complete_missing_evaluations.sh`. This starts at loss comparison, never invokes run.sh or any optimizer. The source-manifest204 learning inputs are unchanged. Final native raw/export checker commands: `python training/language/round32/execution/check_final_native_rounding.py --snapshot training/language/round32/continue-10000 --generation training/language/round32/execution/content-native-dev/new-python.json --out training/language/round32/execution/content-native-dev/new-rounding.json`; replace snapshot with round25 and generation/out with old files for the scientific control. Selected-weights.pt is inference-only and never an exact resume state. Latest full checkpoint.pt is actual10000; best-aligned-checkpoint.pt is actual9500 with its own moments/RNG. Do not restart completed runs. New source5 source/reproduction/license details remain in prospective-fresh-human-dev.
