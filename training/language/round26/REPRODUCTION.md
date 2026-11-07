# Reproduction

Training uses Python3.12.14, PyTorch2.14.1+cpu, NumPy2.3.5, twoCPU threads, FP32 deterministic operations. Source extraction additionally used mwparserfromhell0.7.2; tokenization/inference are own implementations. All sources/rights/raw/code SHA are frozen in source-manifest.json and policy.json.

Rebuild into a new directory, with no network or model updates:

```bash
python training/language/round26/prepare_addition.py --base training/language/round25/multiview --sources training/language/round24/next-candidate-drafts/wiki-addition/source-cache/quality-sources --out /tmp/round26-rebuilt
python training/language/round26/execution/verify_corpus.py --prepared /tmp/round26-rebuilt --base training/language/round25/multiview --sources training/language/round24/next-candidate-drafts/wiki-addition/source-cache/quality-sources --out /tmp/round26-rebuilt-check.json
```

The admitted historical source/attribution/license snapshots are immutable Round24 inputs, not fetched anew. Cache source attempts are archived; quality-sources is the final adopted subset. OldTRAIN/validation/tokenizer byte equality and new target-once proofs are explicit. No reserved/newTEST is encoded or scored.

Actual training:

```bash
bash training/language/round26/execution/run.sh
```

Use --resume only on an incomplete non-running run with exact frozen source/code/settings identity. Latest checkpoint.pt stores aligned weights/AdamW/Torch/private Python RNG, actual steps/history and rollout counters. Full training-rollouts.jsonl is reconciled to retained checkpoint, unretained later lines archived without claiming completed updates. Selected-weights.pt is the best CE model, not optimizer-aligned with latest moments for restart. A completed run must not be started again. persistent.sh runs all mechanical evidence and saves to draftPR even if chat disconnects; complete semantic reading is performed separately.

## 完了後の扱い
実10000更新を完了したため訓練の--resumeを再実行しない。latestとselected9500の整合full checkpointを保存。欠けた評価だけを個別コマンドで再実行する。日常12件のPython/JS・raw/export比較、人間DEV99、selected optimizer監査をexecutionに保存。新TESTは未使用。最終採否はRESULTS.md/adoption.json。
