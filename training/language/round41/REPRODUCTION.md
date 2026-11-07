# R41 再現・復元

## 完了した状態をまず検証する

現在は実10000更新完了。再開/再訓練をしない。全入力・成果・lossless parts・6 full model/Adam/RNG・actual counters・読解/数値結果とGit追跡を検証する。

```bash
python training/language/round41/execution/verify_final_artifacts.py --require-tracked
```

rawが欠けていて隣接chunks.jsonがあれば、verifierはpartsの個別/連結SHAを検証して復元する。個別復元は次の形式。

```bash
python training/language/round41/checkpoint_chunks.py restore training/language/round41/continue-10000/checkpoint.pt.chunks.json
```

実10000/Adam30000、選択9000/Adam29000。latest full-state SHA `f2493f26cb01e92244d9f4487b26a8a0ba598e5b5ed2a838bfad4a5fc66beaa1`、selected full-state SHA `2aae53291d75af683141cfccbe5e622d42f49e5cc76dd850f9c075635333aee8`。6役割の全SHAはRESULTS.mdとexecution/artifact-manifest.json。selected modelをlatest momentsへ混ぜていない。生のfloat32 selected weightsとJS export、旧新全168全文、100瞬間loss/21DEV/1000aux events、全自己negative traceを保持する。

## 学習手順と再開guard

実施した開始コマンドは`bash training/language/round41/execution/persistent.sh`。training/controller両lockと完了拒否guardを備え、model/optimizer/Torch・private Python RNG/実step/履歴を保持する。稼働中の重複起動、完了10000の再実行をしない。未完了checkpointを調べた場合だけ同じコマンドに`--resume`を付ける。未保持trace/logは退避され、保持stepのRNG/momentsから一致して再開する。今回は再開・破棄更新はない。

ゼロ更新の設定・データ・監査はpretraining commit `13318e83d8d28a013053670b467dce7ad569709e` に保存。そのcommitの別worktreeで独立に再実験する場合、まずsource-manifest.jsonの410入力の欠損rawを対応する追跡済chunks.jsonから復元し、全SHAを照合する。現状の成果を消して再実験しない。既存snapshotの復元はbytes単位で一致するが、再訓練のserialized checkpoint/JS metadataはelapsed等を含むのでSHAの一致とtensor/RNGの一致を区別する。

記録されたstackはPython3.12.14/PyTorch2.14.1+cpu/NumPy2.3.5、train CPU2/FP32/deterministic、inference Python1thread。異なるhardware/library全体へのbit一致保証ではない。新84のPy/JS・raw/exportはこの実行で実測一致し、旧R10 near-tie16/17も記録したまま。

## 原典と評価の再現

訓練はGit内のprepared token/index、独自tokenizer、元発話境界map、固定poolとSHAを使う。原典JSONの再監査・human99 lossの再計算には、既存のpinned acquisition記録（prospective-daily-sourceのsource commit/sourcePath/SHAとlicense）に対応するTRAIN/development原本が必要。実行時cacheは`/workspace/daily-conversation-source-audit/human-only-raw`。この外部cache依存を省略しない。原典を再取得する場合も対象TRAIN/developmentと元SHAを照合し、reserved TESTをtokenize/評価しない。

```bash
python training/language/round41/execution/daily_human_likelihood.py --model training/language/round41/continue-10000/model.js --out /tmp/r41-replayed-human.json --raw-cache /workspace/daily-conversation-source-audit/human-only-raw
```

再生成は同じ42prefix・own full vocabulary greedy192/Python1thread/no repair。elapsed等を含むJSONの再生成SHAは変わり得るため、完全prefix/text/token/EOS/UTF8 coreとモデルtensorを比較する。`compare.sh`/`compare_daily.sh`/content-native-dev/evaluate.py/固定source evaluatorが実施条件を保存する。original17の集計はR10 review.pyと凍結gateを用いた。新しい文章の意味は実全文を読み直す必要があり、as_executed記録器はこの生成SHA専用で将来モデルの自動graderではない。

中間1000生成と5000 NLL、選択9000とterminal10000を分け、旧S42は再生成core/SHA一致後の過去判定、旧T42は凍結履歴として扱う。新84を77独立のprefix/text対として照合しても、77独立問題の統計的標本とはしない。評価は既知DEVで新TESTではない。公開モデル・サイト・R25 anchorは変更していない。
