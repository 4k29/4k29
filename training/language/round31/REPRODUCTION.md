# Round31 reproduction and exact recovery

This experiment is one sibling of Round25, starting from the aligned Round11 latest model/AdamW/private Python RNG/Torch RNG, not Round25 selected weights mixed with another optimizer. Round31 changes only the suffix transformation in dedup-policy.json. It does not inherit rejected Round30's128-token rollout. All six core learning files are byte-identical to Round25 and use64-token negative rollouts. Public/site models are not changed.

Recorded environment: Python3.12.14, PyTorch2.14.1+cpu, NumPy2.3.5, CPU FP32, deterministic algorithms,2 Torch threads,2CPU quota, no GPU. Node24.19.0/V8 13.6.233.17-node.51. The full runtime record is execution/preflight-runtime.json. Repeating on another numerical stack is not a promise of identical argmax paths.

From the repository root, restore the exact ignored training stream from its committed lossless chunks:

```sh
python training/language/round31/checkpoint_chunks.py restore training/language/round31/multiview/train.tokens.bin.chunks.json
```

The original Round11 and Round25 raw parent/control checkpoints are tracked in this repository; do not retrain them. Source-manifest.json lists199 frozen files, sizes and SHAs, including the transformed index/data, untouched validation/tokenizer, policy, learning code and original inputs. The added operational midpoint diagnostics are not learning conditions. The transformation report records every removed suffix and original/new SHA. Original data.json provenance fields and the inherited BOS wording have explicit qualifications in execution/metadata-errata.json; current actual offsets, lengths and labels are train.index.json.

For independent preparation reconstruction, use a separate unused folder such as training/language/round31-data-rebuild. Copy prepare_suffix.py and dedup-policy.json there, create its execution directory, and copy Round25's complete multiview directory there. Run that copy of prepare_suffix.py. It reads only the actual Round25 TRAIN index/token stream and existing own tokenizer/glyph definitions. Compare the resulting TRAIN token/index/data SHA with the preserved Round31 files. Do not rerun preparation over an existing preserved experiment; the report guard refuses repeated transformation. Unchanged units are copied token-for-token; only127 final selected canonical TRAIN units change,23 empty units are dropped in all views; no internal deletion joins unrelated text. Original source licensing and split remain in the immutable source records. No DEV/TEST text is used to select common lines.

The following preflight tools do zero optimizer updates; their original results are preserved:

```sh
python training/language/round31/execution/verify_single_factor.py
python training/language/round31/execution/check_sampling.py
python -m unittest discover -s training/language/round31/execution -p 'test_*.py'
python training/language/round31/execution/verify_runtime.py
python training/language/round31/execution/preflight_initial_validation.py
```

The fourteen tests passed; all parameters had finite nonzero gradients, exact parent AdamW moments/RNG loaded, and complete initial mixed-view DEV/site scores matched the parent exactly (0.9789190007498177). Do not rewrite frozen policy/source/code/data while a trial runs. See the saved original audits rather than rerunning writers over a live experiment.

The controller was launched with:

```sh
bash training/language/round31/execution/persistent.sh
```

It owns controller/training locks, runs actual updates with atomic checkpoints every100 retained updates and fixed500-update validation, captures aligned selected-step full states, then executes the frozen numerical/full-raw-generation pipeline. A finished10000 trial refuses restart. A chat/network interruption alone does not imply the trainer stopped: inspect execution/launch.json, live processes, checkpoint and logs before any action. Never start a second controller to obtain another status report.

For a separate, genuinely fresh numerical reproduction, use an unused run name:

```sh
python training/language/round31/train.py --merges 512 --steps 10000 --dim 192 --layers 8 --heads 4 --batch 8 --threads 2 --seed 2049 --lr 2.2499999999999998e-05 --validation-every 500 --run reproduce-10000 --precision float32
```

This repeats the frozen learning condition, not a new condition. Keep that output separate from the original continue-10000 evidence. Compare model state tensors, retained counters, loss/DEV histories and sampler exposure/RNG, excluding elapsed timing and run-name metadata. Entire newly serialized checkpoint SHAs can differ because those metadata differ; concatenating the saved lossless chunks, in contrast, must reproduce the exact archived checkpoint SHA.

For exact partial recovery, first confirm that no original controller/trainer owns the locks and no newer local checkpoint exists. Restore the newest retained full model/optimizer/RNG state, never just inference weights. If the final continue-10000 chunks exist, restore them with checkpoint_chunks.py. For a retained-progress-N backup, restore its checkpoint.pt.chunks.json in that backup directory, verify its recorded SHA, and only then place the full checkpoint plus its matching retained training-rollouts.jsonl/train.log at the original run paths. Restore the original checkpoint-0.pt from its own parts if absent. Do not overwrite newer work with an older remote backup. Then use:

```sh
bash training/language/round31/execution/persistent.sh --resume
```

The runner verifies optimizer counters10000+retained step, exact identities and loss events, archives any log beyond retained state and restores private Python/Torch RNG. Any physical work lost beyond the last retained checkpoint must be reported as unknown rather than counted as retained updates. Full selected-state archives are distinct from latest resume states. selected-inference-weights.pt and model.js contain no resumable optimizer/RNG; never combine them with latest moments.

Actual2000 selected2000 full resume backup SHA is8ec7d0ebc6ec9f3c036e7384d917ce74e8b2f4ba7ad453121274d14d5da7e27d. Its complete chunk concatenation matches the midpoint's source checkpoint exactly. Snapshot diagnostics never modify or signal the live trainer. The5000 monitor must record its actual capture and selected steps; those numbers need not be equal. Files in execution/interim-daily-N are inference/evaluation evidence, not the run to resume.

Final old/new original17 and daily12 use identical input/192-token greedy conditions from compare.sh/compare_daily.sh; the original review.py/full-meaning-policy/adoption policy remain unchanged. Additional native8 reuse exact original Round30 probes (SHA88bb6904ae8432ead9e34071dd83160795b6c2b6a0d9c0475192fcdf0952bbb9) with original CC-BY-SA4.0 attribution, not a new TEST. HumanDEV99 likelihood is separate and not full semantic accuracy. No original TEST model evaluation is authorized here; do not run partition test as a reproduction shortcut. Historical R28/29 and fixed TRAIN prefix-sensitivity diagnostics are additional observations, not alternative Round31 training variants or selectors.

After actual final completion, full output reading, reports and lossless archive generation, freeze_results.py and verify_manifest.py bind the actual files/counters/SHA/chunks. A partial interim report is not a completed10000 trial. Existing public/site behavior remains unchanged until the original strict language gates are clearly passed.
