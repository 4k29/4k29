# Paragraph foundation research — work in progress

Goal: independently generated, coherent Japanese of at least two to three new sentences. Caption-ending completion is a separate capability. Public models, sites and formal adoption criteria remain unchanged.

Base: PR #105, commit 60f0ddaeb38b2d1c7e60f0858af721af10c5efb6. Candidate initial full state: B-6361, SHA 8109d11f80edba3e4ba6acbb513890db42c1b2fb8b612f79f5fc3d5d27c74e2e. No optimizer updates have been performed in this study.

## Current work

A bounded acquisition of 437 officially hosted historical Environment Ministry whitepaper HTML pages is running. Acquisition is not TRAIN approval. The official policy, PDL 1.0, source receipts, robots rules and fixed URL selection are recorded. Third-party columns, quotations, images, maps, figures and dependent prose are excluded or held. Environmental prose remains a concentrated genre; annual editions are correlated and require near-duplicate audits.

The extractor preserves consecutive original paragraphs, with explicit barriers for omitted material. Empty modern HTML main anchors and legacy body layouts are handled separately. Five boundary tests pass. Candidate quantity in PARTIAL_EXTRACTION_AUDIT.json is provisional, not admitted data. Full semantic review, source/family separation and final corpus/token budgets are pending.

## Storage

Deleting SHA-identical derived lower-layer working caches did not reclaim overlay space. R46/R47 references and Git history were retained; STORAGE_RECLAMATION.json records the actual outcome and restoration method. Working scratch and new Git objects are on non-durable /tmp tmpfs. Durable full-state atomic replacement was tested on /workspace with two real generations: the observed minimum free space exceeded the 256MiB reserve. This proves byte-level storage only, not optimizer/RNG restoration or update-resume equivalence. Those checks remain mandatory before training.

## Evaluation and control limitations

All existing DEV sets remain exposed research diagnostics. No sealed TEST or independent native-speaker evaluation is used. New paragraph DEV and scoring rules must be frozen before model outputs. Unused STAIR annotation text is available for a short-text control, but its image families were already encountered in PR105; it is not new-scene data. New paragraph source, length, genre and EOS distribution will differ, so any A/B result cannot isolate paragraph length alone.

No training, formal adoption, public replacement, merge, paid resources, external pretrained models/tokenizers, external generation APIs or subagents have been used. Acquisition and implementation continue; this is not a completed-results report.
