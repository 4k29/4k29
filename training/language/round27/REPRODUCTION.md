# Round27 reproduction

Scientific control: Round25 (adopted), not rejected Round26. Source/data/policy SHA in source-manifest.json/policy.json and execution/frozen-draft.json. Actual preflight receipts in execution/preflight-runtime.json and single-factor-audit.json. Source environment Python3.12.14, Torch2.14.1+cpu, NumPy2.3.5, noGPU, CPU2threads, FP32.

From repository root, fresh run only: `bash training/language/round27/execution/persistent.sh`. No external pretrained weights/tokenizer or AI teacher. Scientific initial state is existing own Round11 latest, not selected-model/latest-optimizer mixing. Fixed10000 optimizer updates, no multi-condition sweep.

Resume only if partial and no live controller/trainer: `bash training/language/round27/execution/persistent.sh --resume`. execute.py restores SHA-bound raw checkpoints from chunk manifests when needed, acquires a run lock, preserves retained loss records, and resumes exact optimizer/RNG/sampler state. Refuses duplicate/completed execution. Never rerun training to fill missing evaluation after10000; invoke only missing evaluation scripts. Do not infer completion from a requested count.

Full checkpoint raw files exceed100MiB: checkpoint_chunks.restore(manifest) reassembles byteidentical content from40MiB parts with size/SHA verification. Zero, latest, and selected full snapshot remain distinct. Initial new AdamW coordinates inherit global tensor age10000 (zero moments), not independent age0 bias correction; preserve this for reproduction.

pipeline.sh records original17 old/new greedy192/trueEOS Python/JS, raw/export comparison and all diagnostics, plus fixed daily12 and humanDEV99. These are DEVELOPMENT, not fresh TEST. Same original strict policies and frozen Pareto criterion. Final manual grading is recorded only after actual full-output reading. No production model/site change.
