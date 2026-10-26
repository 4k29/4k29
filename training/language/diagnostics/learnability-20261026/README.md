# Conversation correspondence learnability assay

Disposable diagnostic for GOAL.md; never an adopted model or a restart of R48 full-mass CE concentration. Original R46 model, tokenizer, production training/inference and public site are untouched. Sealed TEST is not used.

## Frozen design and actual accounting

`candidate-panel.json` is intentionally retained byte-for-byte under its original candidate filename/status. Authorization is in `PLAN.json`, frozen in commit `466f105` **before all optimizer updates and evaluation**. `PREFLIGHT_PLAN*.json` authorize zero updates only.

64 original RealPersona TRAIN pairs are used for updates; 32 other TRAIN pairs are not updated by this assay. All96 were in a previously supervised R46 pool: held-aside does not mean unseen by R46. Documents, NFKC/whitespace-normalized whole-document families and speaker-pair families are unique; the two groups also have disjoint original speaker IDs. This cannot prove all latent topic/family independence.

A uses original correspondence. B swaps contexts in fixed same-own-BPE-length pairs within the64; the targets and context multisets are unchanged. Original texts/utterance ordinals/speakers/provenance and additive BPE boundaries are verified. No examples were redrawn or removed after manual review. Some B replies are plausible; B is **not** an all-invalid semantic-negative label. Both independent review files, their disagreements and the data reviewer's No-Go recommendation are retained. The main decision permits the limited original-versus-permuted association assay, not a guaranteed all-negative benchmark. Primary results include all rows; the intersection of both reviewers' clear mismatches is supplementary.

Both arms start from own R46 selected9500 aligned model/AdamW counter29500/Python and Torch RNG. Existing ordinary response CE is used: target-token mean per example then example mean; no EOS target; eval mode/fork_rng as in the existing implementation. Same inherited AdamW/LR, batch8, shuffled index order, target dose, lengths and numerical settings. This recipe is not the entire R46 production objective and is not a single-factor comparison against production R46.

Each arm executed **198 unique updates + 2 disk-resume replay updates = 200 actual optimizer steps**. Total400 actual,396 retained unique,4 replay. End Adam counter29698; do not call this200 retained updates. No update extension or checkpoint selection. The fixed terminal is evaluated. Midpoint step2 and replay3/4 full state and traces matched bitwise.

**Finite exposure limitation:** 198 unique updates end inside an epoch. Each target has the same dose across arms, but24/64 context identities differ by one exposure (24 or25). Normalized context multiset TV difference0.007575758. Dataset marginals and complete epochs match; the full retained trajectory's context marginals do not match exactly. This is an oversight in the198-plus-replay design, disclosed without changing or rerunning conditions. Do not claim an exact cumulative-marginal causal isolation.

## Numerical audit and measurement correction

Initial zero-update audit stopped on a flat-FP32 gradient-norm reduction discrepancy. `preflight-A.log` and the original committed code/plan are preserved. Independent `assay-norm-audit.json` shows finite gradients and an inaccurate4.66M-element FP32 reduction, rather than nonfinite model behavior. The audit reference alone was changed to FP64; clipping, tolerances, objective, optimizer and data did not change. Corrected A/B audits matched the immutable original CE scalar and all parameter gradients; model/Adam/RNG remained unchanged. See `measurement-correction.json` and the preflight reports. No optimizer update occurred before these passed.

## Evaluation

All96 original targets are teacher-forced under both contexts for baseline/A/B (576 rows). EOS at the gold end is scored separately. Full-vocabulary greedy192, actual EOS and no repair/penalties are used for a pre-output SHA-selected16fit+16held-aside, both contexts, three endpoints (192 full outputs). No sealed TEST, new checkpoint selection or adoption gate modification.

Blind assistant reading uses prefix and the complete unmodified continuation only; endpoint, arm, original target and TF scores are withheld. This is not independent human validation. `blind-key.json` maps blind IDs after reading. Naturalness, meaning, appropriate reply, content-specific appropriate reply, genericness, harmful repetition and topic drift are separate. Canonical gold is not the only acceptable response. The generated-history gold NLL probe after departure is counterfactual sensitivity, not aligned language accuracy.

`analyze.py` reports macro and token-weighted metrics, all cases, reviewer intersection/disputed strata and target-length strata. Bootstrap uses the32/16 fixed exchange pairs, not independent rows. Confidence intervals are descriptive for this selected TRAIN panel. A-B gain alone can result from B degradation; inspect baseline→A and baseline→B and full raw outputs separately.

## Reproduce and inspect

Use the repository environment and admitted original TRAIN files listed in panel `inputReceipts` (CC-BY-SA4 attribution preserved per row and prior source files). Restore the existing own R46 aligned checkpoint if necessary using its chunk manifest. Own raw tokenizer is `round46/multiview/tokenizer.json`.

`build_panel.py` reproduces the candidate with no model imports. The plan binds exact panel and code SHA256s. `assay_runtime.py` and `evaluate.py` require `--panel`, `--panel-sha256`, `--plan`, `--plan-sha256`, `--output` and arm/endpoint. Use a **new** output directory. Training refuses an existing ledger/checkpoint and a plan without explicit training authorization. Do not rerun under this task's consumed400-step budget. Reproduction is a new separately budgeted experiment, not permission to extend this one.

Each isolated `training/{A,B}/terminal.pt.chunks.json` reconstructs the exact terminal fullstate: model, optimizer moments/counters, RNG, data order/cursor, complete loss/gradient history, hashes and accounting. Restore with the existing `training/language/round46/checkpoint_chunks.py restore MANIFEST` helper. This terminal is an assay state, not a production-trainer checkpoint. No adopted-weight export is made.

Raw Python FP32 diagnostics are not a new JavaScript/export parity claim. Existing inference source and public weights are unchanged. Historical numerical branch disclosures, including the R10 near-tie, remain applicable. No JS output repair or disguised parity claim is made.
