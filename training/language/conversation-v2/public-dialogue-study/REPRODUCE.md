# 再現と範囲

この研究はASDCの架空の宿泊相談における条件確認に限定したpilotです。広範な質問回答・理由説明・比較・手順の本格比較ではありません。外部の学習済みモデル・Tokenizer・生成APIは使用しません。

## 固定条件

`PLAN.json` / `PLAN.sha256` / `DATA.json` / `DEV_PROTOCOL.json` が更新前の固定条件です。初期状態はPR #108 MIX-579、完全state SHA `fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7`。A/Bとも同じ66入力・順序・17更新を一巡し、Aは4,880教師、Bは2,058本文＋66真EOS＝2,124教師です。語彙3997、context256、LR1e-5、clip1、継承AdamW。回答は架空の宿泊案内役の発話であり、利用可能な実在施設や予約能力を示しません。

## ライセンスと原文

ASDC（Yuta Hayashibe / Megagon Labs, LREC2022/NLP2021）, revision `f37d6575c73602adcb8ae3687520726793baa672`。コーパス・注釈・文書はCC BY 4.0、プログラムはApache2.0です。`asdc-LICENSE.txt` と出典・変更記録を保持してください。出版社提供の `text_fixed` がある場合はそれを使い、それ以外は `text` を使用しています。元の発話順・話者・EOSは変えていません。独自の文章補修はしません。

`ACQUISITION.json` は取得URL・日時・archive SHA・1590ファイルのSHAです。全取得ファイルをTRAINへ採用していません。公開した学習原文は審査済みの `DATA.json` だけです。ニュース本文・tweet・ichikara由来データは学習へ含めていません。

## 原文からの再構築（モデル更新なし）

```sh
python training/language/conversation-v2/public-dialogue-study/reproduce_data.py \
  --v2-root training/language/conversation-v2 --output /tmp/asdc-rebuild
```

空の出力先を使用します。固定revisionの公式archiveを取得し、元の抽出・保留・保存済み読解判定を適用します。既に取得した公式archiveの展開先がある場合は `--source-cache /path/to/asdc` を指定できます。全1590ファイルのSHAを確認し、再取得せずに再構築します。`DATA_REPRO_RECEIPT.json` はこのcache経路でDATA・teacher監査・DEV・splitの4ファイルが完全一致した記録です。人間の再審査を実施したという意味ではありません。

## 学習と復旧

`.github/workflows/public-dialogue-pilot.yml` は無料public GitHub Actions CPUの専用実行です。sparse checkout、Python3.12、Torch2.14.1+cpu、NumPy2.3.5、Torch2 threads、GPUなし。`GO-sparse.json` は起動commitのparentを固定し、実行済みledgerがあれば再実行を拒否します。PLAN本体のSHAはcheckpointにも記録します。既存のGOを変更して再学習を起動しないでください。

完全stateは `artifacts/{A,B}-PILOT{9,17}/checkpoint.json` の順序で32MiB chunkを連結し、各chunk SHA・全体SHA・内部integrityを照合します。重みだけではなくAdam、全RNG、sampler、cursor、traceを復元してください。`COLD-*.json` は、新しいbare repositoryがremote commitだけから復元し、全state digestが一致した証拠です。正式モデルや過去checkpointの置換は行いません。

`PREFLIGHT.json` は独立プロセスでの更新後再開一致、初期A/B logits一致、Adam非共有、maskと質問本文勾配の検証です。捨て原更新4回、replay2回を保持34回へ混ぜません。optimizer実呼出しは `UPDATES.jsonl`、forwardは `FORWARDS.jsonl` が実数です。曖昧なledgerを自動replayしません。

## 評価

新DEV15件は公式DEVの会話・質問family分離であり、独立人間評価ではありません。判定基準は `DEV_PROTOCOL.json`。crowd作業者のIDは不明なので、話者完全独立TESTとは呼びません。既知MAIN話者のみ分離しました。公開source TESTの形式確認例2件は学習・評価から除外しており、プロジェクト封印TESTは使用していません。

旧129ケース＋自己履歴4エピソードは露出済み診断です。初期の旧評価はPR #108の保存済み結果を再利用します。生成全文・token列・raw bytes・停止理由は `evaluation/*.json`。全語彙greedyを用い、LF抑制や補修はしません。表示用の反復圧縮ビューは `reading_view.py` に限定し、生出力・採点対象は変更しません。
