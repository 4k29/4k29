# Grounded response objective v1

独自11.23M Transformerで同入力のfull CE/返答CEを比較し、各512更新＋探索的curriculum各96更新を完了した研究。実call1,248、保持1,216、再開照合replay32。正式採用・公開置換No-Go。

- [REPORT.md](REPORT.md): 結果、入力契約、限定された改善と退行、全ての限界。
- [NEXT_STRATEGY.md](NEXT_STRATEGY.md): 基盤原文・応答学習・容量・資源と段階通過条件案。
- [GENERATIONS.md](GENERATIONS.md): 省略なし生成全文。token/raw byte列は `evaluation/*.json` / `evaluation-extra/*.json`。
- `PLAN.json` / `CONTRAST_PLAN.json`: 各段階の実行前固定条件。補助context/NLL/parityのpost-primary時点は各protocolに明記。
- `SUMMARY.json`, `run/*trace.json`, `run/*updates.jsonl`: 実数・loss・gradient・処理量・replay。
- `run/{full,response}-{32,512,extra}/archive/checkpoint.json`: 全model/Adam/RNG/sampler provenance/active cursor。全6個、最大chunk32MiB。
- [ATTRIBUTION.md](ATTRIBUTION.md): 原典・license・加工・権利の範囲。
- `EXECUTED_CODE.json`: 学習/評価時の実ソースコピーとSHA。現在のentrypointには完了後の再実行防止とarchive読込対応を追加。

## 既存成果の継承

PR92〜99の原典監査・1epoch・比較runnerを再利用した。公開コードや正式重みは変更していない。旧17/13/9/Pareto等の採用条件は維持。封印TESTの内容は未使用。新DEVはentity-disjointなプログラム診断で、話者/文書/template独立のTESTではない。`SPLIT_LIMITATIONS.json` に原典object共有数を明記した。

## オフライン検証

repo rootから：

```bash
python training/language/conversation-v2/grounded-objective/verify.py
python -m unittest discover -s training/language/conversation-v2/grounded-objective -p 'test_*.py' -v
```

全13 testsには既存環境のPyTorch/NumPyを使う。実optimizer更新は0。GitHub CIはstdlibの `test_results.py` 6 testsとSHA/byte検証のみで、学習を再実行しない。既存runtimeはSUMMARY.json参照。manifestはこのPRの固定成果物向けであり、再評価して結果fileを変えた場合は、旧ファイルを別系列に残して別manifestを作る。

## Checkpointを復元する

```bash
python training/language/conversation-v2/grounded-objective/checkpoint_io.py --restore response-512 --output /scratch/response-512.pt
```

出力先directoryは事前に作り、約136MB以上の空きを確認する。新規ファイルのみ書ける。全chunk/full SHA一致後の全状態で、model-only exportではない。Pythonの信頼できる自作checkpointとしてのみloadする。archiveは6個とも保存済みで、`checkpoint_io.load(name)` はrawがなくてもロードする。active stage cursorは32/512/96、最後の段階はparent512からの追加96である。旧sampler cursorは過去資料の由来であり、新しい教材の再開位置ではない。

## 実学習を再現する場合

**現在の成果物directoryでそのままtrain/contrastを再実行しない。** 完了receiptで拒否する。追加のoptimizer callを無記録で発生させない。

1. 十分な空きのある独立したcheckoutを用意する。最低でもsnapshot保存用1GB以上、Git保管も含め4〜8GB余裕を推奨。
2. commit `fcef305` の元PLAN/data/train.pyで初段を再現する。元初期checkpointは `../epoch1/medium/archive/checkpoint.pt.chunks.json`、full SHAはPLAN。独自tokenizer SHAは本manifestに固定。`python training/language/conversation-v2/grounded-objective/train.py` が各512＋各16replayを実施する。初期weight/Adam/RNGは保存状態を継承し、armごとにdeepcopyする。
3. 同checkoutをcommit `dff7969` のcontrast.py/contrast-data/CONTRAST_PLANに進め、raw512 snapshotsを保持したまま `python training/language/conversation-v2/grounded-objective/contrast.py`。各96を実行する。比較設定を事後的に変更しない。
4. 現在の評価entrypointはlossless archiveも読める。結果出力先は別directoryにコピーしてから変更し、旧評価を上書きせず `evaluate.py` / `evaluate_extra.py` / `context_probe.py` / `context_nll.py` を実行する。追加probeはpost-primary診断である。評価後はfull text/tokenを保存する。

途中の将来再開ではsource SHA/contract/Adam step/trace/active_cursorを照合してから残りの固定scheduleだけを実行する。ここで検証した完全再開一致は16→32の別プロセス実replayで、あらゆる時点の自動復旧を保証していない。追加endpointからの将来学習は、別の事前固定planと新ledgerを要する。

データ再構成にはresponse-data既存の `sources/acquire_jmultiwoz.py` を再利用し、出力を隔離tmpfs `/dev/shm/grounded-source` とこのsourcesに設定する。公式revision/zip/split/TRAIN SHAを本sources receiptと照合してから `build.py` を実行する。取得receiptの時刻は変わるがTRAIN/加工物SHAは同じ必要がある。生会話は公開・正式学習に承認していない。学習再現自体にはコミット済みfact加工例を用い、生会話の再取得は不要。

## 状態保存

`RESUME_STATUS.json` が実完了地点。今回は探索的学習・追加改善・評価・checkpoint保存まで完了し、次の本格学習はNo-Go。狭い仮定設備教材の追加周回を自動開始しない。正式モデル、公開サイト、有料資源、PRマージは対象外。
