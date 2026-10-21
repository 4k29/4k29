# Round36 — human EOS auxiliary coefficient0.3

Training is running. At 2026-10-21T10:54:46.841197+00:00, the latest audited retained checkpoint contains **1800/10000 actual additional optimizer updates**, with Adam counters [21800]. The requested10000 updates are not a completion claim. Full generation reading and language assessment remain pending.

Only the EOS auxiliary coefficient1.0→0.3 changes against Round35. Both rounds start from the same aligned Round28 model/Adam20000/Torch and private Python RNG. The own8-layer192-dimensional model, tokenizer, data/gold targets, BPE40/30/30, negative prefix selection, LR, seed, remaining losses, generation conditions and10000-update budget are unchanged. This is a paired sibling experiment, not continuation from Round35 terminal weights.

Preflight passed:27 objective tests, an independent eligible-position audit across all147986TRAIN rows, exact parent model/optimizer/RNG alignment, initial DEV equality and finite real-objective gradients. Frozen397 input hashes were rechecked during execution. The source manifest/policy/code SHAs are recorded in [execution/launch.json](execution/launch.json).

The initial state and actual200/1000 states are committed as lossless checkpoint parts with model, optimizer and RNG. Latest remote checkpoint: actual1000, commit95b3dcae75d977ccb2aa8321d3ecc616155d610d. See [REPRODUCTION.md](REPRODUCTION.md) for the existing guarded reproduction/resume procedure; do not restart the currently running trainer. Ongoing raw logs and checkpoints are local until subsequent publication.

Same pure-CE DEV selector, original strict gates and practical adoption guard. Daily12 whole-meaning/nonloop and humanDEV99 must not regress. Generic acknowledgements are reported separately from content understanding. [execution/PAIRED_VALIDATION_PROGRESS.md](execution/PAIRED_VALIDATION_PROGRESS.md) records matched-update exposed common DEV curves; it excludes expanded human-chat DEV and is not language evidence.

No new TEST or public model/site replacement. PR: https://github.com/4k29/4k29/pull/77
