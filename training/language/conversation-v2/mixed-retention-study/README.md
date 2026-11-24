# Multi-genre mixed retention study — Draft PR108

結論・限界は[REPORT](REPORT.md)、比較表は[TABLES](TABLES.md)、次の一条件は[NEXT_STRATEGY](NEXT_STRATEGY.md)。正式採用No-Go。579保持更新の一巡は完了しており、追加epochを開始しない。

## 証拠の入口

- `PLAN.json` / `SAMPLING_PROTOCOL.json`：更新前に固定した配分、初期状態、コード・入力SHA。v1→v2はoptimizer0の時点の保存guard修正のみ。
- `corpus.json.gz` / `POSITION_MAP.json.gz` / `schedule.json.gz`：既存TRAIN選択・LF1変換・原典対応・全579batch。
- `SOURCE_AUDIT` / `TEACHER_AUDIT` / `REJECTIONS`：有効教師590,144、重複0、権利・family・既知DEV境界の範囲。
- `UPDATES.jsonl`：実呼出し583のintent/completed、保持579・捨て3・replay1を区別。
- `PREFLIGHT` / `REPLAY_PROOF`：更新後の別process完全再開一致、Adam非共有。
- `artifacts/MIX-{4,289,579}` / `GIT_RESTORE-{4,289,579}`：lossless全状態とremote-only復元証拠。
- `evaluation/*MIX.json`：中間と終端の149件＋自己履歴4episode、無修正text/token/raw bytes/stopReason。
- `evaluation/*-READING.json` / `*-REVIEW_CARDS.json` / `*-SCREEN.json`：主要129件と自己履歴のassistant判定。追加20件はraw保存のみ、未採点。
- `NLL` / `BOUNDARY_COMPARISON` / `WEIGHTS-*`：source別本文予測、40境界のtop10/TF、層別重み変化。
- `parity-terminal-summary` / `FINAL_VERIFICATION` / `CI_RECEIPT`：限定Python/JS、保存済み証拠の照合、専用CI。

## 復旧（Git原本、学習不要）

研究ブランチを新しい作業領域へ取得する。旧/workspaceの巨大cache・一時alternatesへ依存しない。通常cloneの容量不足を避け、`git clone --filter=blob:none --no-checkout --single-branch --branch research/mixed-retention https://github.com/4k29/4k29.git` とsparse-checkoutを使える。保存点は各約135MB、3点全部と原本・一時出力の同時保管量を事前に見積もる。

リポジトリrootから、例：

```sh
python training/language/conversation-v2/mixed-retention-study/restore_checkpoint.py --revision origin/research/mixed-retention --cursor 579 --output /tmp/MIX-579-restored.pt
```

出力先に既存ファイルがある場合は拒否する。各chunkSHA→全体SHA→atomic renameを行い、既存checkpointを上書きしない。`.partial`は未完了であり使用しない。実際のcold Git復元は`verify_git.py`で3点すべてtorch deserializeと全状態integrityまで確認済み。復旧後の`torch.load(...,weights_only=False)`は自身の検証済みcheckpointに限定する。

初期はPR105 B-6361、対照はPR107 LF1の既存lossless保存を使い、[前研究の復旧手順](../lf-boundary-study/README.md)を参照。初期・対照SHAはPLANに固定。今回の終端SHAは`fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7`。

すべてのcheckpointはmodel、Adam、全RNG、sampler/cursor/scheduleSHA、PLAN SHA、traceを含む。CPU torch2.14.1、NumPy2.3.5等の元環境を記録している。終端のAdamstep6940、activecursor579、targets590144で完了。過去ledgerを捨てて同じ更新を再実行しない。

## 再集計・最小検証

元の出典・評価・Tokenizerファイルを親commitから同じSHAで用意して実行する。元取得コードを再実行して最新版を混ぜない。

```sh
python -m unittest discover -s training/language/conversation-v2/mixed-retention-study -p test_contract.py
python training/language/conversation-v2/mixed-retention-study/ci_audit.py
python training/language/conversation-v2/mixed-retention-study/verify_results.py
python training/language/conversation-v2/mixed-retention-study/summarize.py
```

上記にmodel forward・optimizer更新はない。`review_cards.py`は原文表示用、`record_reading.py`は実際に全文を読んだ後の判定記録用であり、一般的な自動意味採点器ではない。人間評価を偽装しない。

`evaluate.py` / `nll.py` / `parity_check.py`は保存した推論手順。再集計に再推論は不要。全語彙greedy、EOS・roleの意味とcontext上限は旧評価を継承する。専用CIは重量checkpointを大量checkoutせず4stdlibテストと凍結artifact監査だけを実行する。

## 保存環境の注意

実作業は/tmp側の独立sparse checkout。/workspace側にfsync ledger・resume receiptを保存した。元Git promisorのcache bytesをSHA付きで/dev/shmへ移動したため、環境再作成後に旧alternates pathが失効する可能性がある。その場合は上の新規cloneまたはcanonical remoteからの取得を使う。元Git refs/history・R25/R46・正式checkpointは変更していない。`PROMISOR_STORAGE`等のreceiptを保持し、一時コピーがあることだけを永続保存の根拠にしない。

公開モデル・サイト変更、マージ、封印TEST、新規データ、有料資源、外部モデル/API、サブエージェントはいずれも使用していない。
