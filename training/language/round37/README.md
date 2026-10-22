# Round37 — exclude competing original newline main CE

Training is running. At 2026-10-22T07:28:33.792887+00:00, the latest audited retained checkpoint contains **300/10000 actual additional optimizer updates**, Adam counters [20300]. No completion or language gain is claimed. See [execution/launch.json](execution/launch.json).

Only main CE at the already eligible authentic human TRAIN utterance-end EOS positions is excluded. EOS coefficient0.3, original valid-target denominator, original raw data/labels, BPE40/30/30, own8x192 model, sampling/LR/seed, teacher and self-generated UL, inference and strict gates remain unchanged. Same aligned Round28 model/Adam20000/Torch/private Python RNG as scientific control Round36; not continuation from its rejected terminal weights. Fixed practical floors inherited from R35 remain unchanged, including daily nonloop≥4.

Preflight passed37 tests, all147986 TRAIN masks/data, exact trainer reverse patch, real finite all-parameter gradients and initial DEV0.9718989571266189 equality in every view/site.397 final source inputs are SHA-frozen. Before any update, the terminal-control reading-reference helper was corrected to verify the separate actual reading receipt, preserving the historical ungraded mechanical record; the protocol fix is documented and final inputs/runtime reverified.

Log crossEntropyLoss is now main CE after the exclusion; originalCrossEntropyLoss and removedEligibleNewlineCe preserve the decomposition. Only unchanged original-gold common/human DEV likelihood supports like-for-like NLL comparison. Raw stream exposure counts still include excluded newline positions; active original-main-CE targets equal original exposures minus endEosPositions. No-mask gradients/RNG and noneligible gradients remain unchanged.

All initial/midpoint/selected/terminal checkpoints, full raw generations and numerical checks will be saved. Actual full semantic reading is pending. No new source, TEST, external weights/tokenizer/API/teacher positives, public/site replacement or merge. See [REPRODUCTION.md](REPRODUCTION.md). PR78: https://github.com/4k29/4k29/pull/78
