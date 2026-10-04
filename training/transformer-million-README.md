# 10セットの日本語追加学習と再開手順

学習データは `transformer-million-corpus.json` の固定スナップショット。718文型を訓練／検証に分け、公式に確認した33仕様と本人指定のドラマ紹介2文の日英・2口調140例を訓練専用に加えた。元の語彙IDを保つ619語彙、37,984パラメーターの自作Transformerを使う。

```sh
python training/train-transformer.py \
  --corpus training/transformer-million-corpus.json \
  --initialize-model training/transformer-630000-teacher.js \
  --distill-model training/transformer-630000-teacher.js \
  --rounds 10 --updates-per-round 100000 --minimum-steps 10000 \
  --batch-size 8 --threads 1 --learning-rate 0.00001 --dropout 0.12 \
  --distill 8 --compile-loss --validation-every 10000 \
  --adaptive-learning-rate --checkpoint /tmp/japanese-million-checkpoint.pt \
  --version 2026-10-04.transformer-6 \
  --output /tmp/japanese-million.js --artifacts-prefix /tmp/japanese-million
```

CPU版PyTorch 2.6.0は訓練専用で、公開サイトは外部の学習済みモデルやMLライブラリを読み込まない。例ごとの重みを用いたサンプリング、AdamW、勾配のクリップ、dropout、凍結した自作教師との蒸留を使う。各10万更新時点でモデル・optimizer・乱数状態・検証履歴を保存する。再開には同じ設定に `--resume /tmp/japanese-million-checkpoint.pt` を加える。

制限による中断前は56万更新までログで確認でき、50万更新の保存データから再開した。中断後に保存されていなかった6万更新は再実行した。履歴の到達更新数と、再実行を含む実際の計算回数を区別する。

`transformer-million-training.json` は各セットの到達更新数と検証値、`transformer-million-candidate.js` は検証に基づく候補重み、`transformer-million-reference.json` はPyTorchの推論値。全セットの実行回数を、途中で選んだ候補の更新数へ置き換えない。一方、過学習を避けるため、最終更新の重みを無条件に採用もしない。実行数は `completedSteps`、候補時点は `bestStep`。

その後、文末を自然にする `natural-final-corpus.json` で1万更新を追加する。元の文型からの自然な語尾の別候補とも、同じ検証文で比較する。仕様140例の自由なgreedy生成が完全一致し、元の検証文で悪化が2%以内の候補から、現在の文型の検証誤差が最小の候補を選ぶ。外部の言語holdoutは選択に使わない。

`language-selection-manifest.json` の対象ファイルに対して `node training/select-language-model.mjs training/language-selection-manifest.json` を実行すると、比較・値の再現・実行回数の記録を確認して重みと照合用の値を配信側へコピーする。比較は `compare-validation.py`、値の再現は `evaluate-literal-recall.py` で再検証できる。いずれも既知の仕様の記憶と開発時の文型検証であり、一般会話能力の評価ではない。
