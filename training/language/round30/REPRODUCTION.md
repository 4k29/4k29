# Round30 reproduction and continuation

## Scope and frozen treatment

This run tests ONLY own generated-negative maximum length64→128, versus adopted Round25 settings. It is a sibling using the SAME aligned Round11 latest model/AdamW/Torch RNG/private Python RNG, not a continuation of rejected Round29 or a mixture of selected weights and latest moments. All positive data and tokenizer files are byte-identical to Round25. The code difference is one rollout caller using the frozen policy value128. Parameter count4,655,808;8layers,dim192,heads4,FFN768,context256; own BPE40%/Glyph30%/random-character-boundary30%; batch8,threads2,seed2049,FP32; constant LR2.2499999999999998e-5,AdamW wd0.05,clip1;teacherUL1.0/window64 and sequenceUL0.1/every10/prefix32/window64. Generated tokens are negatives only.

Requested10,000 is not a completed count. Actual state is in the atomic checkpoint and retained-state records. Original parent optimizer counter10,000 plus actual new-run step determines the real optimizer counter. Selected weights need their own aligned selected-step optimizer/RNG archive; never combine beststate with latest moments.

## Restore exact existing evidence first

From the repository root, restore the ignored training stream using the committed lossless parts:

```sh
python training/language/round30/checkpoint_chunks.py restore training/language/round30/multiview/train.tokens.bin.chunks.json
```

The restore command checks every chunk SHA/size and assembled SHA. It refuses to overwrite different existing bytes. Parent Round11 and control Round25 aligned checkpoints must be present at their frozen paths. If a parent is stored as parts in a fresh checkout, restore it from its own committed chunk manifest before validation. Do not recreate parent weights by training.

To restore a saved main latest/zero/selected full state, use the matching `continue-10000/*.pt.chunks.json` manifest once available. A retained-progress backup has its own manifest inside that backup directory: restore there, verify its recorded actual step and all hashes, then copy the full checkpoint AND its matching retained trace/log into the original run paths only if the original trainer/controller is absent and no newer state exists. Preserve any later evidence instead of overwriting it. An interim inference snapshot contains selected weights only and is NEVER resumable.

## Preflight and exact main-run continuation

The original preflight verified all positive byte identities and full target coverage,14 tests, all parameters' finite nonzero gradients with actual128-token rollout, exact parent AdamW/RNG loading, and full initial DEV bit-exact equality0.9789190007498177. The authoritative pretraining source-manifest has199 entries, SHA434956ade7fa236a730213e45694f24de929e2774b5818ea7c24c7d7b25b2007. Source/policy identities remain fixed throughout training.

```sh
python training/language/round30/execution/verify_single_factor.py
python -m unittest discover -s training/language/round30/execution -p 'test_*.py'
python training/language/round30/execution/verify_runtime.py
python training/language/round30/execution/preflight_initial_validation.py
```

Runtime checks do not perform optimizer updates. Verify all recorded source-manifest identities before any training. Do not rerun a live controller. If the MAIN run is partial and its exact full latest checkpoint is present, with no trainer/controller alive:

```sh
bash training/language/round30/execution/persistent.sh --resume
```

The guarded runner restores model/AdamW/used RNG states exactly, retains only events consistent with the saved actual step, archives unretained log events, and reconciles raw rollout traces. A completed10,000-update checkpoint is refused; no automatic duplicate learning is allowed. This is fault recovery, not a scheduled interruption. The current experiment has no voluntary pause.

## Independent full training reproduction

Do not invoke the main guarded runner to retrain a completed trial. After restoring all frozen inputs, an independent reproduction can use a NEW unused local run name with the frozen trainer and identical arguments:

```sh
python training/language/round30/train.py --merges 512 --steps 10000 --dim 192 --layers 8 --heads 4 --batch 8 --threads 2 --seed 2049 --lr 2.2499999999999998e-05 --validation-every 500 --run reproduce-10000 --precision float32
```

This writes to `round30/reproduce-10000`, preserving the original experiment. Do not label those newly executed updates as part of the original trial. Run names, elapsed-time fields and serialization metadata differ, so complete checkpoint/export file SHAs are not promised to match across a new training execution. Compare actual selected parameter tensors, curves and full generations on the pinned numerical runtime. Exact original checkpoint bytes are reproduced by the lossless chunks.

Pinned numerical environment: Python3.12.14,Torch2.14.1+cpu,NumPy2.3.5;Node24.19.0/V8 13.6.233.17-node.51. CPU quota2, RAM8GiB, no GPU, no mixed precision/compile. Current kernel6.18.55 differs from original R25 kernel6.18.44; initial full DEV and the first common rollout tokens match exactly. See execution/preflight-runtime.json and runtime-context.json. Do not claim universal cross-platform bit identity or hide the historical R10 Python/JS near-tie branch.

## Evaluation

The original final pipeline evaluates the selected export against the unchanged R25 export on17 original DEV openings and12 everyday DEV openings, saving every raw generated token/character, Python/JS references and rawFP32/export comparisons. All use unchanged greedy decoding, full own vocabulary,192-token cap and original strict gates. Full manual reading remains required. A reproduction's export can be passed directly to the unchanged evaluator:

```sh
python training/language/round10/evaluate.py --model training/language/round30/reproduce-10000/model.js --partition validation --out /tmp/r30-reproduced-original-dev.json --reference
node training/language/round10/evaluate_js.mjs "$PWD/training/language/round30/reproduce-10000/model.js" /tmp/r30-reproduced-original-dev.json /tmp/r30-reproduced-original-js.json
python training/language/round30/execution/evaluate_daily.py --model training/language/round30/reproduce-10000/model.js --out /tmp/r30-reproduced-daily-dev.json
```

Eight additional native-format human mid-dialogue contexts were frozen in Git before generation on those contexts. Use the committed probes, not a newly selected set. Attribution/license and deterministic source-offset selection are preserved under execution/content-native-dev. They are exposed supplementary DEV, not a new TEST or a replacement gate. HumanDEV99 likelihood is unchanged canonical serialization and supplementary only, never checkpoint selection. Midpoint2000/5000 selected inference snapshots are diagnostic; comparisons to R25 final have unequal progress and cannot establish an equal-progress causal generation effect.

No reserved TEST model use. The prior R29 oldTEST-reference visibility incident remains disclosed; those old excerpts are not human-blind. No foreign pretrained weights/tokenizer/teacher, no generated positive targets, no output repair, no public model/site promotion.

Final run is complete: actual10000, selected9500. Do not resume it as an incomplete run. Supplementary content-native-final evaluates the same selected model on the frozen content-native-dev probes; native-javascript.json and native-unrounded.json record full8/8 sequence comparisons. RESULTS.md documents final manual judgments; timestamped earlier mechanical pending flags are historical.
