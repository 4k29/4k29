# Round48 preflight — validation only

This independent branch validates the proposed response-position main-CE rule against Round46. It does not contain a Round48 training launcher. No validation weights may replace research/adopted/public models. Round25 remains the formal anchor.

`PREREGISTRATION.json` fixes stage ordering, sample selection, invariants, operational gradient screens and the disposable resume test **before gradient measurements**. Thresholds screen a substantial optimization change; they are not theoretical safety guarantees or evidence of Japanese ability. A failure remains a failure, without silently adding a weight cap, source filter, new denominator or changed threshold.

## Minimal changes and their reasons

- Copy the existing standalone response-position prototype and authentic TRAIN span builder into this audit directory so code and data provenance can be reviewed. Existing Round46/47 files remain unchanged.
- Add loss-helper end-mask validation (dtype, shape, valid original newline only). The weight builder already enforced it, but a direct caller could previously bypass that check. This rejects invalid input; it does not alter valid-input weighting.
- Add authentic speaker/source and fixed semantic-sample audits, a frozen receipt, real-model gradient diagnostics, fallback/no-op checks, and a tiny isolated full-state resume test.

The treatment preserves old active content mass, original valid-target denominator, BOS/EOS weights and existing newline/EOS handling. “Content” includes any original separator not already excluded. Full original ordinal adjacency is retained even when a BPE endpoint is unaligned. No reply-to annotations are invented.

## Update accounting

Gradient and source audits execute zero optimizer updates. The resume validation is explicitly separate: nominal auxiliary schedule indices9..12, four uninterrupted updates and four split-path updates per condition, baseline and treatment, **16 actual disposable optimizer updates total**. Completed validation updates remain1..4 per trajectory; nominal schedule indices are not claimed as completed training. These updates are excluded from Round48 training and model lineage, and all results must be reported even on failure.

Original full-state checkpoints are read only. Validation saves belong only to this directory's ignored disposable area. All original model/data/tokenizer/optimizer/RNG hashes are recorded; no external weights, tokenizer, generation API or generated positive targets are used. DEV/TEST and public/site behavior are untouched.

## Research fallback

If response-position concentration fails the preflight or later fails to improve full contextual Japanese generation, retain separate diagnostic proposals for capacity, data distribution, teacher-forced versus autoregressive behavior, and learning allocation. Do not continue loss-coefficient changes mechanically.
