# Round35 reproduction and exact resume

This trial is running. Never start a second controller or resume over a live checkpoint. Completed updates come only from the retained full checkpoint, not the requested10,000 budget. Original initialization is Round28 latest, Adam20000, weight lineage59000; the scientific comparator is Round34. Sibling round updates are not added to this model's lineage.

The only learning change is coefficient1.0 additional EOS2 CE at human TRAIN authentic utterance-end targets that are originally unmasked standalone newline16. Divide its sum by the batch's original nonmasked target count. Keep original gold newline CE, R34 negative-prefix selection and all other training/inference settings. policy.json and source-manifest.json bind code/data/SHA. The no-admitted-source dossier is future research only; none of its dialogue files were acquired or added.

## Restore missing referenced inputs in a fresh checkout

Use own lossless parts; never replace an existing mismatched raw file. The helper accepts either the training source manifest or final artifact manifests, and restores only missing referenced paths with verified adjacent chunks. It never runs a model or optimizer.

```bash
python training/language/round35/execution/restore_referenced_chunks.py --manifest training/language/round35/source-manifest.json
python training/language/round34/execution/restore_referenced_chunks.py
python training/language/round34/execution/verify_manifest.py
python training/language/round35/checkpoint_chunks.py restore training/language/round35/continue-10000/checkpoint-0.pt.chunks.json
```

Actual200/1000/5000 paired full states are retained under execution/retained-paired-N/. Their parts contain the exact model, moments, RNG and additional counters at that update. At5000 Adam25000 and weight lineage64000; original positive exposure7,793,175 targets/27,221,289 bytes. Their snapshot JSON binds actual checkpoint SHA and paired-control proof. They are archival states, not an instruction to overwrite the live/latest run. The initial zero checkpoint and all fixed data parts are preserved separately.

## Preflight already executed before training

single_factor_audit.py reverses only the EOS objective/eligibility/logging hooks and recovers Round34 trainer byte-exactly. It verifies all positive source/data bytes and R34 prefix policy unchanged. preflight_data.py, preflight_prefix_policy.py, check_sampling.py, preflight_eos_masks.py,27 unit tests, verify_runtime.py and preflight_initial_validation.py passed at zero new optimizer updates. The independent position criterion matched all147,986 rows; original labels and RNG were unchanged; no-eligible loss/model gradients matched the old objective exactly; real model gradients were finite/nonzero. All initial DEV views/sites exactly matched Round28 NLL/byte0.9718989571266189, and Adam/RNG were restored exactly.

Do not rerun these zero-update evidence writers into the live frozen trial. Reproduce them only in a separate clean tree before a new launch, preserving the frozen policy/source SHAs. The current model and data implementation are already saved; the initial setup script is historical preparation, not a command to recreate over this trial.

## Exact continuation only if incomplete and not running

For an incomplete nonrunning continue-10000 full checkpoint, use execution/run.sh --resume. The guarded executor refuses duplicate locks, missing resume identity and completed10,000 runs. It preserves model/Adam, Torch/private Python RNG, actual counters, original positive exposure, EOS cumulative positions/batches and rollout trace reconciliation. Inference model.js and selected-weights.pt cannot resume training. A detached supervisor, best-aligned-state archive and read-only checkpoint monitor already run independently of chat. Their original PIDs are in launch.json/monitor-processes.json; do not launch duplicates. The paired milestone observer retains fixed200/1000/5000 states without model forwards or extra updates.

At completion, audit_eos_exposure.py independently replays fixed positive draws and verifies actual EOS eligibility counters/RNG. paired_training_audit.py compares Round34/R35 initial full states, final RNG/exposure/draw trace and every negative prefix history. compare_losses.py separately checks original CE, both unlikelihood terms and the additional EOS term. Periodic training losses are every100 updates and always coincide with sequence-negative updates; they are not all-update averages.

## Evaluation

Keep the original pure common-DEV CE selector and strict language gates. Daily12/native8/source5 are exposed development diagnostics, not new TEST; source5 are one cast family. Final source5 runs only after actual10,000; its correct control34/current35 model allowlist was checked prospectively. Save complete selected and terminal generations under identical own bounded greedy192/context256, with Python/JS and raw FP32/seven-decimal export comparisons. If selected and terminal arrays are exactly identical, reuse identical outputs with explicit reading provenance, not a false claim of freshly reading84 distinct new outputs. Semantic judgments require actually reading the full prefixes and continuations. No EOS/repetition/loss-only language pass, output repair, public/site replacement or new TEST generation.

NUMERICAL_LIMITS.md preserves the historical Round10 near-tie branch. execution/ROUND34_CONTEXT_CORRECTION.md distinguishes the measured192 generation cap from context256 for these42 fixed prompts. Final artifact verification and semantic assessment remain pending actual completion, not recorded as done.
