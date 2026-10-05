# 本人情報、説明の長さ、会話履歴への追加学習

**状態：ユーザーが日本語原文の事前学習を最優先へ変更したため、中断して保存。** 最後のatomic checkpointで7,500更新（原文1,000＋対話6,500）を確認し、比較用exportは検証で選んだ7,000更新時点（原文の選択750＋対話6,000）の自作重みです。11,000更新の完了とは扱いません。`owner-aligned-suspended/checkpoint.pt` にoptimizer・乱数・選択状態を保持し、`SUSPENDED.json` に中断理由・実数・SHAを記録しています。新しい最優先の原文実験は `training/language/` で進め、公開モデルは変更しません。以下の学習回数は中断前の計画です。

前回の `switch-candidate.js` は、好きなものを古い4項目で答え、AppleやHCIへの関心を答えられませんでした。Headphoneの詳細にも重量1項目だけを返す例があります。公開サイトのPR34で直した分類・回答処理とは別に、この実験では自作Transformerの数値的な重みを追加学習します。外部の学習済みモデル、既成トークナイザー、生成AI API、Wikipediaは使いません。

## 根拠と学習データ

親モデルはこのリポジトリで乱数初期化から作った `switch-candidate.js`。11,000更新を実行し、検証だけで選択した9,000更新時点の自作のexport重みを使います。旧optimizerや最後の不採用重みは引き継ぎません。親のコーパスSHAは `23f999e661397ebc79d417cc4ac337b733b040823df85b418f99d95518f8d384` です。

回答は現在の `docs/profile.json` と、公式出典を記録した `training/product-specifications.json` から作成します。好きなものは10項目の名称だけ。HCI・小規模言語モデル・人や状況に合わせた情報体験は興味の一覧だけに含めます。個別の興味9種類、興味一覧、短い製品紹介、詳しい製品紹介を区別し、旧回答を使っていた履歴も更新します。モデルが生成した回答を学習の正解にしません。

Headphoneの詳しい説明はデザイン、40mmドライバー、Bluetooth 5.3、AAC/SBC/LDAC、IP52、329g、有線接続、コーデックとANC条件別の再生時間をつながる文章にします。短い紹介は見た目と基本仕様を一文にまとめ、細かな再生時間を省きます。本人の購入理由など未確認の体験へ仕様を流用しない境界は、従来のデータに残します。

TRAIN30,488／VAL4,184／DEV TEST4,226行。新しい質問形式は24／4／4のfamilyごとに分割。全体でも同じ正規化質問文字列が複数partitionへ入りません。矛盾する「一言で詳しい説明」などの33例と、質問の範囲を変える関心wrapper132例は追加前に除外します。最長の全文は322トークンで、512トークンの文脈を超えて文を切った行はありません。数え上げと実際の正解は `owner-aligned-data.json`、全行は `owner-aligned-corpus.json` に保存します。

語彙は前回の独自byte-BPEをそのまま使用し、1,286トークン。新しい検証・テスト文で再学習しません。新しいコーパスSHAは `f2d1c665aeb9204f1b02543130c56f6ce6a9a9ab9b2f87f96602fca23931492d` です。

原文は以前取得した政府・MDN資料を使い、文末までそろった192トークン以下の段落を追加します。原文の訓練3,445／検証270／テスト262フレーム。追加段落はTRAIN1,606／VAL122／TEST116。政府・MDN本文を変更せず、本人作成の旧プロフィール原文だけを更新して変更前後のSHAを保存します。MDN派生の原文、QA、新しい質問にはURLとCC BY-SA 4.0を引き継ぎます。[利用条件](MDN-DATA-LICENSE.md)と元の `web-language-sources.json` に出典・取得時の条件を記録しています。

## 固定した検査と採点

修正版の学習前に68問を固定しました。本人情報24問＋同じ24問を別の話題の正しい履歴の後で聞く検査、短い紹介4問、未確認情報8問、出典に基づく定義8問。質問文字列は全コーパスpartitionと以前の検査に存在せず、語彙、重み、checkpointの選択へ使いません。

別の9会話27ターンでは、実際に生成した有効な回答だけを次の履歴へ追加します。正解文で置き換えません。文脈を超えたら失敗として数え、黙って切りません。

原文6検査はTESTページの別の完全文段落の先頭28文字から、BOS＋全文彙greedyで続きを生成します。出力の修理・検索・差し込み・文法の語彙制限はありません。参考の続きと異なっても、seedとつないだ文法と意味が成立すれば合格です。ページ自体は以前も検査した資料であり、独立した新しい一般言語ベンチマークとは扱いません。

本人報告の4問は今回はTRAINにも含まれます。`switch-owner-feedback.json` の合格数は要望への適合を確認する開発診断であり、未知の質問への性能ではありません。

関連性・事実・日本語・文体の各0〜2点、すべて2＋EOS完了＋有効UTF-8だけを厳格合格とします。全文一致しない回答は一つずつ理由を記録します。短い正しい概要は、goldにあるすべての項目を含まなくても、質問に過不足なく答えれば合格です。明示されたデザイン、詳細、特定の条件を落とせば不合格。実装アシスタントによる採点であり、独立した人による代表的な会話調査ではありません。

学習前は全文一致28/68、厳格合格33/68。適切な短い概要5件を意味的な同等性で加点しました。paired24問は単独11/24→履歴後9/24。実際の会話は7/27ターン、全ターン合格の会話0/9。原文の自然さは1/6です。基準の補足と学習前のレビューは、修正版候補の出力を見る前に確定しています。

## 学習、文脈、速度

原文追加学習1,000更新＋対話追加学習10,000更新。新しいAdamWから始め、次トークン損失、answer-only損失、0.3の原文replay、0.3の訓練用semantic補助損失を使います。補助headを推論の回答検索や修理には使いません。

古い256位置のembeddingと他の生成用重みは自作親モデルからコピーし、新しい256位置はseed429から独自に初期化します。構造、語彙、出典SHA、tensorの形と有限性を点検し、未宣言の文脈変更を拒否します。生成部分は627,840、訓練用headを含む総パラメーターは644,094。文脈容量512だけで、未学習の長い会話への対応を主張しません。

重みは、学習前に固定した検証256問の全文一致数、同率なら次トークン損失だけで選びます。選択IDのSHAは `91d4d7c7a6f97949097128c6f62702e7098776e12e578c69f0296db81dbc5d9d`。68問、実際の会話、原文検査では選びません。

更新回数は実際の `optimizer.step` を数えます。親の実行回数と選択時点、今回の実行回数、原文と対話の選択時点、不採用更新を区別します。replayや思考回数を別の更新として足しません。

JavaScriptに、同じBPEを隣接pairのheapで処理する任意オプションを加えます。優先順位は学習済みルールの順位、同順位では元の左位置。分割結果を変えず、全ルールを全位置へ当て続ける計算を減らします。既定の `rank-loop` は維持し、`--fast-tokenizer` で選択。固有コーパス・検査文字列すべてでtoken IDを比較し、greedy・beam・logit・KVキャッシュの一致も検査します。速度は同じ数値モデル・同じKVキャッシュの6回の実際の会話を、実行順を交互にして比較します。通信やUI込みのブラウザー速度とは扱いません。

## 中止した初回実行

初回データには、一言の依頼へ長い説明を割り当てる問題がありました。データ品質を直すため実行を中止し、原本コーパス・ログ・理由を `owner-aligned-abandoned/` に保存しています。最後のatomic checkpointで4,250更新を確認していますが、中断までの追加の途中更新は正確に数えられないため、完了実行の合計へ足しません。この実行の重みは親モデルにも公開サイトにも使いません。修正版は元の自作switchモデルからやり直します。

## 再現

```sh
python training/dialogue/prepare_owner_alignment.py
python training/dialogue/prepare_owner_alignment_controls.py
PYTHONPATH=/tmp/4k29-torch-training TORCHINDUCTOR_COMPILE_THREADS=1 python training/dialogue/train_curriculum.py \
  --corpus training/dialogue/owner-aligned-corpus.json \
  --own-initial-model training/dialogue/switch-candidate.js \
  --parent-corpus training/dialogue/switch-corpus.json \
  --pretrain-steps 1000 --steps 10000 --dim 128 --layers 3 --context 512 \
  --batch-size 8 --threads 1 --seed 429 --learning-rate 0.0003 \
  --validation-every 1000 --validation-limit 256 --length-buckets --compile-loss \
  --replay-weight 0.3 --semantic-weight 0.3 \
  --checkpoint /tmp/4k29-owner-aligned-v2-checkpoint.pt \
  --output training/dialogue/owner-aligned-candidate.js \
  --artifacts-prefix training/dialogue/owner-aligned \
  --version 2026-10-05.dialogue-owner-aligned-1
node training/dialogue/chat.mjs --model training/dialogue/owner-aligned-candidate.js --fast-tokenizer
node training/dialogue/benchmark_bpe.mjs --model training/dialogue/owner-aligned-candidate.js \
  --corpus training/dialogue/owner-aligned-rollouts.json --out training/dialogue/owner-aligned-bpe-benchmark.json
```

計算用PyTorchだけを使用し、外部の学習済みモデルはダウンロードしません。CPU版PyTorchの場所に応じて `PYTHONPATH` を変更してください。ローカル対話は明示的に候補の `--model` を指定します。公開サイトが自由生成候補へ置き換わったという意味ではありません。
