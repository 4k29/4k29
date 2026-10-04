# ローカル回答モデルの学習

このサイトは小さなdecoder-only Transformerをブラウザ内で実行し、次の語句の予測、登録情報の検索、文法制約、好みに合う文章の順位付けを組み合わせる。ChatGPT自体の重みを変更する機能ではない。

## 現在：仕様値と日本語の文型の追加学習

従来の600,000回に10,000回ずつ3段階を追加し、今回までの追加更新は630,000回、初期学習を含む採用経路は640,700回になった。すべて実際のAdamW更新。各段階の最終10,000更新を採用し、記録を `transformer-specifications-first-training.json`、`transformer-specifications-second-training.json`、`transformer-training.json` に保存した。以前の600,000回までの教師と記録は `transformer-600000-*` に残す。

2層4 heads・37,984パラメーター。語彙は477から619へ追加し、以前のID・embedding行を保って初期化。文法718例を608訓練／110検証に分け、公式で確認した仕様33項目と本人指定のドラマ紹介2文について、日英・2口調の140例を訓練へ追加した。計858例。専用制御トークンに続く数値や語句そのものを次トークンの正解にし、仕様の制御トークン自体は損失に含めない。外部の学習済み重みは使用しない。

`product-specifications.json` の値、ANC・codec・ケースの条件と出典を、生成器がそのまま `neuralModel.specificationMemory` に同梱する。質問を項目に対応付けて専用制御トークンから値を生成し、出典付きの値と完全一致したかを確認する。不一致時には確認済みモデル内メモリーを使い、数値を創作しない。

最初の段階のgreedy値再現は日英66仕様中58、2段階目は65。3段階目はドラマ紹介4文を含め70/70完全一致。これは学習済み値の再現であり、未知の知識の正答率ではない。文法検証損失は1段階目1.479959、2段階目1.518081、3段階目1.427590。3段階目では以前の600,000回の自作モデルを別の凍結教師として使い、文法忘却を抑制した。仕様値の行に教師の疑似正解は使わない。

不自然な趣味の文型、製品を主語として「が使っている」とする文型などを除外。Tecircを趣味に分類しない。文末の口調変換は確認した活用を扱い、単語途中の「います」を置換しない。語句の選択には学習した分布を使い、自然さ・本人の指定・数値の正確さには生成制約と回帰評価も併用する。

再現例（PyTorch 2.6.0 CPU、build-only。ブラウザには不要）:

```sh
node training/prepare-transformer.mjs /tmp/spec-grammar.json --direct-only --extended
node training/prepare-specifications.mjs /tmp/spec-grammar.json /tmp/spec-corpus.json
python training/train-transformer.py --corpus /tmp/spec-corpus.json --initialize-model training/transformer-600000-teacher.js --expand-vocabulary --rounds 1 --updates-per-round 10000 --batch-size 16 --threads 1 --learning-rate 0.00015 --distill 2 --compile-loss --export-final --version 2026-10-04.transformer-5 --output /tmp/spec-first.js --artifacts-prefix /tmp/spec-first
```

続く2段階目は `transformer-specifications-first.js` から学習率0.00006、dropout0.05、distill1。3段階目は `transformer-specifications-second.js` から学習率0.00008、dropout0.03、distill8、`--distill-model training/transformer-600000-teacher.js`。評価と実測は `evaluation/specification-recall-results.json` と `evaluation/japanese-conversation-results.json`。

10セット×100,000更新の長い追加学習には `--rounds 10 --updates-per-round 100000 --adaptive-learning-rate` を使う。`--export-final`を指定しない場合は、全セットを実行した上で文法検証損失が最良の重みを採用する。`completedSteps`（実行した回数）と`bestStep`（採用までの回数）を区別し、途中の採用重みを全更新後の重みとは表示しない。

## 過去：50ラウンドの追加学習

指定された50ラウンドを、各10,000回、合計500,000回の実際のAdamW更新で完了した。出発点は前回の10,700更新のモデルで、今回の最終チェックポイントまでの学習経路は累計510,700更新になる。最低回数を満たした途中の最良モデルに戻す方法は採らず、`--export-final` で全更新後の状態を配信する。途中の検証損失も診断用に保持する。

2層、4 attention heads、埋め込み32次元、MLP 64次元、文脈32トークン、語彙477、学習パラメーター33,440個。学習可能な位置埋め込み、causal self-attention、残差接続、LayerNorm、GELU、共有された入力埋め込みと出力headを持つ。言語・回答の関係・口調を制御トークンとして置き、次のトークンと文末EOSを予測する。

日英848件の元の文法例から、本人の直接の回答として使える724例を選んだ。「プロフィールに登録」「本人は挙げている」など第三者による説明の文法は、訓練と回答候補から除いた。同一文が異なる口調で訓練・検証の両方に現れないよう、言語・関係・トークン列をSHA-256で分割。612例・538グループが訓練、112例・97グループが検証となる。データSHA-256は `895d9df9cba6ed4fcba6f651799e3ab4d9581d5bc4f23c5f99cc44eb688bed88`。

`{value}` と `{label}` は登録値と種類を保持するスロット。本人の人物情報や製品名を推測する学習ではない。今回追加した好きな作品・ブランドの説明は公式情報を確認して `profile.json` に保存した。`favorite-grammar.js` の追加文法は既存の語彙と関係トークンで予測・順位付けされるが、今回の500,000更新の訓練対象には含まれない。好きな理由、購入・視聴履歴を学習したとは扱わない。

AdamW、batch 16、最大学習率0.00002、1000-step warmupとcosine decay、勾配上限1、weight decay 0.02、dropout 0.12。2,000更新ごとにcross-entropyを計測し、10,000更新ごとにラウンドを記録する。検証の停滞に応じて学習率を下げ、下限0.000002で継続する。凍結した出発点の教師から訓練文だけの分布を温度2で保存し、正解のcross-entropyに重み2のKL蒸留項を加える。検証文と外部評価文は訓練損失に使わない。

CPU上の計算はPyTorchのコンパイルで高速化した。最初の40,000更新後、model・optimizer・乱数状態・検証経過をチェックポイントから復元し、損失全体のコンパイルへ切り替えて続行した。カウンターだけを増やす処理はない。最終の重み出力のために500,000更新のチェックポイントを読み直す操作は、追加更新を実行しない。

訓練損失は0.402923→0.355550、検証損失は1.379694→1.382870。訓練への適合は進んだが、検証では約0.23%悪化し、今回の反復だけによる精度改善は確認できなかった。経過に記録した所要時間は約51.9分。結果は `transformer-training.json` と `transformer-selection.json` に保存した。

## 以前の学習と補助モデル

前回は848例を714訓練・134検証へ分け、3条件それぞれで10,000更新した。初期化からの2条件の最終検証損失は1.27663と1.40999、700更新の教師から蒸留した採用条件は初期1.18852、最終1.19161。採用モデルの経路が10,700更新となった。記録は `transformer-10000-selection.json`、さらに前の検討は `transformer-initial-selection.json` に保存する。固定教師は `transformer-teacher.js`、今回の出発点は `transformer-rounds-teacher.js`。教師は配信サイトに読み込まない。

1〜4-gramの条件付き予測は元の848例から学習。文章の順位付けには、作成した36組の好み比較から7特徴の重みを600反復で学習した。損失0.693147→0.200342。実際の人間の評価を集めたRLHFではなく、合成した比較データによるpairwise logistic learningである。

## 回答と個人設定

`neural-inference.js` はJavaScriptとFloat32Arrayで学習側と同じ計算を実行する。12ケースの全logitsをPyTorchと照合する。共有K/V状態を512件まで保存し、固定文法の経路の予測値を再利用する。質問への直接性、長さ、直近の重複は回答ごとに評価する。

`predictive-generator.js` はTransformer 85%、統計モデル15%で次のトークン確率を混合し、文法trieの許可する次トークンに進む。幅64のbeamで完成文を評価する。文章は作成した文法に制約されており、あらゆる自由文を生成するモデルではない。登録値とリンクはそのまま保持する。

初期設定は希望された `friendly` / `normal`。口調・長さの明示的な希望をブラウザの質問履歴に記録し、次回も順位付けへ反映する。「今回は」は永続化せず、未知・要確認の回答から好みを強化しない。生成回答を本人の承認とみなして自己学習することもない。履歴は同じブラウザ内だけに最大300件保存する。

## 再実行

Node 24.19.0、Python 3.12、PyTorch 2.6.0+cpuを使用。Python/PyTorchは訓練用で、配信には必要ない。

```sh
node training/train-generation.mjs --check
node training/prepare-transformer.mjs /tmp/4k29-direct-corpus.json --direct-only
python -m pip install --target /tmp/4k29-torch-training -r training/requirements.txt
PYTHONPATH=/tmp/4k29-torch-training TORCHINDUCTOR_COMPILE_THREADS=1 python training/train-transformer.py \
  --corpus /tmp/4k29-direct-corpus.json --initialize-model training/transformer-rounds-teacher.js \
  --threads 1 --batch-size 16 --rounds 50 --updates-per-round 10000 --minimum-steps 10000 \
  --validation-every 2000 --compile-loss --distill 2 --learning-rate 0.00002 --adaptive-learning-rate \
  --export-final --version 2026-10-04.transformer-3 --checkpoint /tmp/4k29-rounds50-checkpoint.pt \
  --output /tmp/4k29-rounds50.js --artifacts-prefix /tmp/4k29-rounds50
node training/select-transformer.mjs /tmp 4k29-rounds50 --minimum-updates=500000
node --test tests/*.test.mjs
node evaluation/evaluate-prediction.mjs --out=evaluation/prediction-results.json
```

同じ設定に `--resume /tmp/4k29-rounds50-checkpoint.pt` を加えると最後の完了ラウンドから再開できる。中断した未保存更新は採用経路には数えない。CPU、コンパイル方法、Node/ICUによる語句分割、浮動小数点差により数値・時間の完全な一致は保証しない。

日本語フォントはNoto Sans JPの400を自己配信する。ライセンスと出所は `docs/assets/noto-sans-jp-OFL.txt` / `noto-sans-jp-source.txt`。fonttools 4.66.1とbrotli 1.2.0を用意し、`python training/subset-japanese-font.py 'NotoSansJP[wght].ttf'` で再作成できる。

## 評価

固定回帰219問、追加した開発用168問、今回の好きなもの22問、NodeとPC・モバイルの操作で確認する。これらは開発・回帰ケースで、一般の質問に対する正答率ではない。別の26文・297トークンの句の評価は学習・選択に使わず、最終状態を固定してから行う。未登録語13トークンは `<unk>` とする。実測の損失・速度・サイズと評価結果は `evaluation/prediction-results.json`、前回の結果は `evaluation/prediction-10000-results.json` に保存する。

500,000更新後の評価は回帰219/219、追加168/168、好きなもの22/22、Node749/749。ウォーム状態300回答の中央値1.12ms、p95 2.82ms。未見26文の損失は2.09178、perplexity 8.09930で、前回10,000更新の8.77137より下がった。この狭い句の評価での変化と、訓練中の検証損失の悪化は別の結果であり、一般の回答精度向上とは解釈しない。

## 過去：続く10ラウンドの追加学習

その後の指示で10ラウンド×10,000更新をさらに実行し、合計600,000回の追加更新を完了した。採用重みの学習経路は累計610,700回。50万更新の最終重み `transformer-500000-teacher.js` から開始し、本人の口調の文法724例に、好きな種類の文法20例と説明用の保護された値の文法4例を追加した。748例のうち633例・553グループが訓練、115例・99グループが検証。新たな本人情報や説明内容そのものを重みの正解として学習したとは扱わない。

50万更新の記録は `transformer-500000-training.json` / `transformer-500000-selection.json` に保存。この10万更新の記録は `transformer-600000-training.json` / `transformer-600000-selection.json`。モデル・optimizerの出発点は自作モデルだけで、外部の学習済みモデルは使わない。

再実行は上記の prepare-transformer に `--direct-only --extended` を指定し、初期化を `training/transformer-500000-teacher.js`、roundsを10、学習率を0.00001、versionを2026-10-04.transformer-4へ変える。出力は `/tmp/4k29-rounds10.js` と対応するJSON、選択の最小更新数は100000。

現在の追加10万更新の訓練損失は0.418244→0.365487、検証損失は1.402132→1.402410。検証では約0.020%悪化しており、更新回数だけを精度向上とは評価しない。所要時間約10.0分。
