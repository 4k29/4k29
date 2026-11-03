# Coherent Japanese paragraph study

This is isolated research after PR105. Main goal: at least two new, connected, meaningful Japanese sentences on held-out source material. Short caption completion and NLL are separate diagnostics. No public model/site replacement or merge.

## Frozen conditions

`PLAN.json` version2 and `COMPARISON_DESIGN.json` define the experiment. Both arms inherit the complete own B-6361 state:11,225,280 parameters, own BPE3997, context256, Adam step6361, model unique-update counter12820, inherited Torch/private-Python/global-Python/NumPy RNG. LR stays at the inherited floor1e-5, clipping1, ordinary genuine-target causal CE. New finite schedules begin at cursor0; old sampler history is preserved in the parent archive, not falsely replayed against new data.

A uses previously unconsumed eligible STAIR annotation strings. B uses reviewed new official explanatory prose. Each receives591,997 genuine teacher targets in579 updates, at fixed checkpoints4/289/579. Terminal is the main comparison; intermediates are diagnostic. Source, genre, length, EOS frequency and dropout tensor shapes differ, so this does not isolate paragraph length alone. No repeated source positions fill the budget.

New prose:1,572 units,359 original pages,592,132 body tokens, one Ministry source. This misses the requested2–5M planning target. It is a bounded distribution experiment, not a broad modern-Japanese foundation corpus.32 fixed units were fully read:27 accepted,1 conditionally useful as dated language material,4 held. Main-assistant review is not independent human evaluation or fact-by-fact certification. Applicable source-heading families are held without rewriting their words.

New source-held-out Osaka DEV has5 cases and low statistical power; all Osaka is excluded from TRAIN. Existing45 prose cases,32 caption cases and other exposed diagnostics are retained. SealedTEST is never used. Supplementary20 newly consumed TRAIN probes never enter DEV success counts.

## Run and inspect

From the active research checkout:

```sh
python training/language/conversation-v2/paragraph-foundation/preflight.py
python training/language/conversation-v2/paragraph-foundation/drive.py
```

The driver requires a completed baseline evaluation, verifies actual updated-state replay, archives full checkpoints, pushes them, proves Git-only restoration, releases only its own verified disposable mirrors, and continues the fixed budget. It does not select/adopt a model or start another epoch. Read `DRIVER_STATUS.json`, `LIVE_STATUS.json`, `RESUME_STATUS.json`, receipts and actual-call ledgers. Planned579 is never a completed count.

`train.py --arm A --until 289 --resume` restores the latest SHA-verified durable state, verifies all frozen inputs and compares any recovery replay to the completed-call trace. An unmatched intent is an explicit blocker, not an assumed optimizer call. The same applies to B. Do not use a fresh launch over existing ledgers.

## Storage and recovery

Scratch checkout and new Git objects live on `/tmp` tmpfs. They are not durable. `/workspace/4k29/training/language/conversation-v2/paragraph-foundation/private/durable/` holds the active arm's full checkpoint/receipt and per-call fsynced ledger.128-update checkpoints use atomic replacement with a256MiB persistent reserve. Actual peak storage was tested; tmpfs and cgroup memory reserves are also guarded.

Every completed fixed checkpoint is split into<=32MiB lossless Git chunks. Its manifest records whole/chunk SHA and complete state digest. `receipts/*-GIT_RESTORE_PROOF.json` records pushed commit confirmation plus an actual Git-only full-state reload before removing newly derived working copies. Old formal checkpoints and Git history are never deleted. The source B-6361 archive is unchanged.

To restore a completed archived stage to the durable working mirror, use, for example:

```sh
python training/language/conversation-v2/paragraph-foundation/stage_checkpoint.py A-289 --restore
```

Prefer a later valid active durable checkpoint if it exists. Never overwrite it blindly with an older archive. After recreating a lost scratch checkout, reconstruct `private/run/<arm>/receipt-<step>.json` from the corresponding verified public `receipts/<arm>-<step>.json` so completed stages are skipped; restore the active state and ledger before resuming. The parent source raw scratch file can be rebuilt from its unchanged PR105 Git chunks and expected SHA. Corpus, schedules and small source receipts are mirrored to the workspace and committed.

Process-level updated-state replay and fixed-stage Git-only recovery are tested. Complete loss of both the workspace and scratch between remote archives is not claimed to preserve unpushed calls; report any such uncertainty rather than inventing an exact count.

## Preserved failures and implementation repairs

- Deleting identical lower-layer derived token caches did not reclaim overlay blocks; measured outcome and restore references are retained.
- Extractor v1 assigned EOS at parent-to-child headings. V2 removes94 such teachers, retains the exact32 selected source texts, and preserves the old code/sample/No-Go evidence. No earlier PR model is invalidated.
- First baseline inference job failed on duplicate source/generated `text` keys after33 logged cases, before optimizer updates. Schema is repaired, both texts are retained separately and per-case raw outputs are journaled. Criteria/data/decoding are unchanged; PLAN v1 and failure evidence remain.
- A metadata-only edit to a frozen admission file triggered the SHA guard before the next worker updated anything. Exact original bytes were restored; explanation moved to an operational report. Do not edit frozen inputs during the run.

`python -m unittest discover -s training/language/conversation-v2/paragraph-foundation -p 'test_*.py'` runs lightweight boundary, deduplication, schedule and output-schema contracts. GitHub CI runs the same tests. Python/JS parity uses short raw-FP32 probes only and does not establish complete-reply equivalence.

The capacity comparison resource gate is separate. A27.40M model needs at least925,978,624 bytes for two FP32 model/Adam generations plus reserve, before overhead, exceeding current persistent free space. Its old zero-update probe is not language or training-throughput evidence.

## Completed result

See [REPORT.md](REPORT.md), [NEXT_STRATEGY.md](NEXT_STRATEGY.md), RESULTS.json and UPDATE_ACCOUNTING.json. Both arms completed579 retained updates/591,997 targets. New connected paragraphs0/5 and old developed prose0/45; formal adoption remainsNo-Go. Capacity feasibility subsequently executed fresh11M/27.40M each4 retained+2 replay using separately tested remote-previous/single-local storage, without relaxing256MiB reserve. This supersedes only the bounded resource-probe execution status, not the original two-local-generation No-Go or the absence of language capacity evidence. No job is left running.
