# Reproduction and exact state restoration

The authoritative final files are `execution/final-assessment.json`, the SHA-bound manual records, `execution/ALL_FOUR_STATE_GENERATIONS.md`, `execution/final-numerical-verification.json`, and `execution/artifact-manifest.json`. Historical automatic `mechanical-status`/pending notes describe their earlier time, not the final semantic state. See RESULTS.md for the unsuccessful daily-language outcome.

## Verify saved artifacts without training

From the repository root, restore lossless raw files only if absent:

```bash
python training/language/round38/checkpoint_chunks.py restore training/language/round38/multiview/train.tokens.bin.chunks.json
python training/language/round38/checkpoint_chunks.py restore training/language/round38/continue-10000/checkpoint-0.pt.chunks.json
python training/language/round38/checkpoint_chunks.py restore training/language/round38/continue-10000/checkpoint.pt.chunks.json
python training/language/round38/checkpoint_chunks.py restore training/language/round38/continue-10000/best-aligned-checkpoint.pt.chunks.json
python training/language/round38/checkpoint_chunks.py restore training/language/round38/execution/retained-snapshots/200/checkpoint.pt.chunks.json
python training/language/round38/checkpoint_chunks.py restore training/language/round38/execution/retained-snapshots/1000/checkpoint.pt.chunks.json
python training/language/round38/checkpoint_chunks.py restore training/language/round38/execution/retained-snapshots/5000/checkpoint.pt.chunks.json
python training/language/round38/execution/verify_final_artifacts.py
```

The final verifier can restore a missing frozen-input raw file from its adjacent tracked chunks manifest; it never overwrites a differing existing file. All chunk sizes/SHA and concatenated full-state bytes are checked. Six full states are retained:0/200/1000/5000/selected9500/latest10000. Raw checkpoint files are generated restoration artifacts, not the files to stage; the parts/manifests are tracked. TRAIN raw data likewise has tracked lossless parts.

The initialization is the exact R28 latest full model/Adam20000/Torch/private-Python RNG state, as in R37—not R37 terminal weights. Selected9500 has its own matching Adam29500/RNG; latest10000 has Adam30000/RNG. Never combine selected weights with terminal moments. Selected raw weights/JS are comparison artifacts, not adopted/public weights. NumPy randomness is unused.

## Original corpus preparation

Pinned JMRD source `ku-nlp/JMRD@a20b0a89b4cf6ce1db320039f6e27df10604bf4c/data/train.json` has raw SHA `4c8abd2e8913a7f2bc208052e8934f3af937c72636b573ea2dbfb83ec6945eaa`. Only human utterance text is serialized unchanged with one newline between turns. No reviews, knowledge, questionnaires, role labels or generated positives enter targets. Source/CC-BY-SA4.0 attribution and audits are in added-human-source. Upstream valid/test were not downloaded. Prior protected raw hashing is not heldout model evaluation. Short/near duplicates and cross-source participant disjointness are not guaranteed.

The existing append encoder was used with:

```bash
python training/language/round28/prepare_addition.py --base training/language/round37/multiview --sources training/language/round38/added-human-source --out training/language/round38/multiview
```

That command is for an absent output directory in an isolated preparation copy, not for overwriting the saved experiment. It preserves every old train byte/index row and the tokenizer/validation. Original own glyph+BPE rules, random character-cut seed `2049|originalDocument|startLine`, three views, window257/overlap32 and each target once remain unchanged. The derived end map preserves every old list and appends only exact existing token ends after original utterance separators; no BPE refitting or EOS insertion into original labels. New JMRD utterances have no embedded newline; old RealPersona embedded newlines were not reinterpreted by splitting. Historical preparation scripts suffixed `_as_executed.py` record exact operations with workspace paths and assertions; they are not safe rerun-over-existing-artifacts entrypoints.

## Training trajectory

Python3.12.14, PyTorch2.14.1+cpu, NumPy2.3.5, Linux6.18.55/x86_64; CPU2 threads, FP32, deterministic algorithms, no compile/GPU. Own8x192/heads4/FFN768/context256/dropout.1/vocab5455/4655808parameters. Batch8, LR2.2499999999999998e-5, seed/RNG lineage2049, AdamW inherited moments/counters, wd.05/clip1. Fixed10000 updates and pure mixed-view DEV every500; minimum common DEV selects best9500. BPE40/30/30 and human30%/other70% remain fixed. All R37 learning code and objectives/normalization are byte-identical. Source addition alone changes within-human population/positive draw history and final RNG; independent replay must match this experiment's own state, not R37's.

A run is launched with `bash training/language/round38/execution/run.sh`. It refuses an existing completed checkpoint. For a genuinely partial run, `bash training/language/round38/execution/run.sh --resume` loads full aligned model/moments/Torch/private Python RNG, reconciles traces and preserves the actual retained counter. This finished experiment has no remaining updates; do not pass resume or delete its outputs to manufacture another run.

For an independent training reproduction, use a separate checkout/worktree at the recorded source, materialize every frozen-input raw reference from tracked parts, and move aside only that copy's generated R38 output directory/log before a fresh guarded run. Keep this completed record intact. A full reproduction physically performs10000 optimizer updates; sampler replay/evaluation/restoration do not. The launch/supervisor/training lock guards prevent duplicate workers. This actual run used one detached trainer throughout; transient chat transport resets did not restart it.

## Evaluation and interpretation

Old selected R37 and new selected R38 use the same42 prefixes, own unrestricted full-vocabulary greedy192, Python1thread and unchanged tokenizer. Terminal10000 comparison is separately preplanned, not a replacement for common-DEV selection. Full raw model outputs, all token IDs/EOS/UTF-8 flags, JavaScript outputs and raw-vs-rounded generations remain in JSON. `read_full_group.py selected|terminal original17|daily12|native8|mrmp5 [start stop]` prints complete saved prefixes/text only; it does not judge them.

Actual full readings are recorded in explicit SHA-pinned `_as_executed` judgment scripts. These are records of the observed files, not automatic graders for a future model. `confirm_all_new_readings.py` verifies every row binding and duplicate consistency; `assemble_final_four_states.py` verifies old historical provenance and saves all168 complete state outputs; `verify_final_numerics.py` verifies full sequence parity. None changes weights, generation or thresholds. Old readings are reused only after exact same raw-core identity. No new TEST/general-population inference or independent blind human claim.

Practical humanDEV99 is unchanged canonical serialization with terminalEOS, fixed context256/192 new targets/up to64 prior input tokens, Python1thread/batch8. TRAIN99 is the same legacy RealPersona sample, not all expanded TRAIN or JMRD. Scope/metadata clarifications—including inherited unexecuted helper prose and R25-only gradient diagnostic—are in diagnostic-metadata-scope.json. Canonical final assembly/assessment uses actual R37 scientific-control paths and the corpus-only condition.

The original strict17/13/9/group gates and fixed practical humanDEV≤0.9107185711429243/daily whole≥0/nonloop≥4 remain unchanged. No optional NLL-only/public promotion. A next source-weight experiment is proposed separately at0 actual updates in NEXT_EXPERIMENT.md.
