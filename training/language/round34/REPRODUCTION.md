# Round34 reproduction and exact full-state restoration

Actual training completed10000 updates once. Selected8000 (Adam28000,lineage67000); latest10000 (Adam30000,lineage69000). Initialization was Round28 latest model/Adam20000/Torch/privatePythonRNG,lineage59000. Round33 is the scientific sibling comparator; its updates are not added to this model's lineage. Fixed conditions and all367 initial input SHA are in policy.json/source-manifest.json; runtime and initial gradient/DEV checks are under execution/preflight-*.json. All84 new state outputs were actually read. final-assessment.json supersedes the historical automatic pending-language records.

## Restore artifacts in a clean checkout

Python with the recorded PyTorch/NumPy runtime and Node is required. Run from repository root. The restore helper only reconstructs missing artifacts directly referenced by each manifest from lossless adjacent parts, validates SHA/bytes and refuses to overwrite a differing file. It does not train or fetch a model.

```bash
python training/language/round34/execution/restore_referenced_chunks.py --manifest training/language/round33/execution/artifact-manifest.json
python training/language/round34/execution/restore_referenced_chunks.py
python training/language/round33/execution/verify_manifest.py
python training/language/round34/execution/verify_manifest.py
```

The raw multiview/train.tokens.bin is reconstructed from its own three parts. Latest,zero,selected8000 and actual200/1000/5000 full states each have checkpoint chunk manifests. For a single artifact:

```bash
python training/language/round34/checkpoint_chunks.py restore training/language/round34/continue-10000/checkpoint.pt.chunks.json
```

Use the analogous best-aligned-checkpoint.pt.chunks.json for selected8000; it contains its own moments and RNG. model.js/selected-weights.pt are inference artifacts and cannot resume optimizer training. All full-state SHA/counters are in optimizer-audit.json,selected-optimizer-audit.json and retained-state snapshots. Final artifact-manifest.json records all six full states, source/input hashes and all outputs.

## Completed evaluation

No completed trial should be rerun with run.sh, supervise.py or pipeline.sh. To recompute aggregates from saved unedited generations and actual manual judgments:

```bash
python training/language/round10/review.py --generation training/language/round34/execution/new-validation.json --manual training/language/round34/execution/new-manual.json --out /tmp/round34-selected-review.json
python training/language/round10/review.py --generation training/language/round34/execution/terminal-state-diagnostic/original17-python.json --manual training/language/round34/execution/terminal-state-diagnostic/original17-manual.json --out /tmp/round34-terminal-review.json
python training/language/round34/execution/verify_final_outputs.py
```

The last script verifies saved raw FP32/export/JS fields and writes complete unedited four-state comparisons. It performs no model forward or optimizer update and assigns no judgments. Current numerical scope: new selected42 and terminal42 all match Py/JS and raw/export. Old selected current-runtime Py/JS42 and raw/export25; its original17 raw was not regenerated here. Old terminal evidence is the pinned historical Round33 result. Historical Round10 near-tie divergence remains disclosed in NUMERICAL_LIMITS.md; tolerance2e-4 is unchanged. Existing public-model962 repository and2580 public regression checks are not experimental-language scores.

The original fixed-source after_final.py failed because its frozen evaluate.py allowed Round28 instead of the scientific comparator Round33. The original code/logs/SHA are retained. For a clean rerun of this read-only5-context measurement use fixed-source-mrmp-dev/after_final_recover_control33.py and evaluate_control33.py; only the model-path allowlist and separate generation log names differ. It waits for actual10000 and primary completion, then measures both old/new without changing weights, decoding, inputs, gates or labels. Full recovery provenance is execution/fixed-source-allowlist-recovery.json. Other final-only diagnostics are execution/assess_terminal_state.py and execution/wait_human_train_gap.py; existing complete diagnostics are guarded against accidental duplication. No new TEST generation is allowed.

R33 original control17 judgments were rebound only after full raw-field identity. Old daily/native/source reviews retain prior completed reading provenance plus exact current identity checks. All42 selected and42 terminal new prefixes/continuations were read in full with individual reasons; no fresh current-turn reread of all84 old state outputs is claimed. Source5 is one cast family, not five independent populations. Human TRAIN99 is fixed before scoring, not the whole TRAIN mean; DEV99 includes one duplicate pair. Loss logging every100 coincides with sequence-UL every10, so periodic total loss is not an all-update mean. The unchanged validation selector uses pure CE.

## Interrupted-run procedure, not an instruction to restart this completed trial

For a genuinely incomplete, nonrunning reconstruction only, restore its retained full state, put that full checkpoint at continue-10000/checkpoint.pt and use execution/run.sh --resume. The guarded runner restores model/moments/Torch/privatePython RNG/settings and reconciles logs/rollout trace with actual retained step, archiving later unretained records. Never count those later records or requested10000 as completed. Never duplicate a controller. Retained200/1000/5000 are recovery evidence, not licenses to retrain the already completed Round34. Any new scientific trial must use a new round, fixed configuration and its own real update count.
