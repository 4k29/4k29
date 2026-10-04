# 自然な語尾の追加学習候補

既存の自作Transformerから、自然な語尾を含む文型で10,000回のAdamW更新を実行した。ブラウザの文型選択には、丁寧な言い方と「使っている。」などの自然な常体を追加し、直前の回答と語尾が重なる候補の順位を下げている。

この候補の重みは `natural-endings-candidate.js` に保存した。この候補を直接配信せず、長い学習の候補から自然な語尾を学習した別候補と比較し、後者を採用した。保存した長時間学習のチェックポイントは変更していない。

検証が最良だった6,000更新目の重みを保存した。実行した更新数10,000と採用候補までの更新数6,000は区別する。モデル構成と語彙は同じで、37,984パラメーター、619語彙。外部の学習済みモデルは使わない。

同じ検証文での比較結果は `natural-endings-comparison.json` に保存した。

| 検証対象 | 文型数 | 追加学習前の損失 | 候補の損失 |
| --- | ---: | ---: | ---: |
| 従来の文型 | 110 | 1.427590 | 1.410965 |
| 語尾を追加した文型 | 163 | 1.423871 | 1.257904 |

製品仕様とドラマ紹介の日英70項目は、候補の重みから70項目すべてを完全再現した。これは既知の値の再現と文型の検証結果であり、一般的な会話能力の評価ではない。

`natural-endings-corpus.json` は今回使った学習データの固定スナップショット。文型生成関数の後続変更によって再現条件が変わらないように、再実行時にはこのファイルを使う。訓練と検証は文型単位のSHA-256で分離し、同じ文が異なる口調で両方に入らない構成。

```sh
python training/train-transformer.py \
  --corpus training/natural-endings-corpus.json \
  --initialize-model training/transformer-630000-teacher.js \
  --rounds 1 --updates-per-round 10000 --minimum-steps 0 \
  --batch-size 16 --threads 1 --learning-rate 0.00008 \
  --dropout 0.05 --distill 1 --compile-loss --validation-every 1000 \
  --version 2026-10-04.transformer-natural-1 \
  --output /tmp/natural-endings-candidate.js \
  --artifacts-prefix /tmp/natural-endings
```

学習環境はPyTorch 2.6.0 CPU。実測した更新履歴は `natural-endings-training.json`、ブラウザ推論との照合用の値は `natural-endings-reference.json` にある。

現在の文末候補を使う別の固定スナップショットは `natural-final-corpus.json`。一律に「よ」で終わる日本語候補を除き、語彙IDを変えずに868文型＋140仕様例、計1,008例を含む。こちらも従来の110文型と同じ検証分割で比較するため、`compare-validation.py`で複数モデルを同一のコーパスに対して評価する。

```sh
python training/compare-validation.py \
  --models training/transformer-630000-teacher.js training/natural-endings-candidate.js \
  --corpora training/transformer-million-corpus.json training/natural-final-corpus.json \
  --out /tmp/validation-comparison.json
python training/evaluate-literal-recall.py \
  --corpus training/natural-endings-corpus.json \
  --model training/natural-endings-candidate.js --out /tmp/literal-recall.json
```

長い学習の再開では、保存済みのモデル・optimizer・乱数状態・検証履歴を復元する。元のコーパスSHAと、学習率・dropout・検証間隔・教師ファイルの指定などが一致しない再開は拒否する。再開前後で教師ファイルとコーパスを変更しない。
