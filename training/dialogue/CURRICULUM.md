# 独自Transformerの言語・対話カリキュラム

Wikipediaは使用しない。学習済みの外部モデル、外部トークナイザー、外部の生成AI APIは使用しない。PyTorchは計算ライブラリとして訓練時だけ使う。

## 本人情報と質問の区別

`prepare_generalization.py` は承認済みのプロフィールと公式仕様から、手作業で定義した質問群と回答を作る。類似する質問を同じfamilyへまとめ、重複する入力が訓練・検証・テストをまたがないようにする。架空の個人情報、違う製品、他人の持ち物には、本人の登録情報を流用しないように未知情報の例を含める。

3,356訓練例／160検証問／178評価問、97 intent。独自byte BPEの語彙は1,030、最大pieceは12 byte。原文182例で次トークンの事前学習1,000更新、その後に質問・履歴を損失からマスクした回答全文の対話学習10,000更新を実行した。モデルは乱数初期化、3層・4 heads・96次元・MLP192次元・128トークン、335,712パラメーター。選択は検証の全文一致数、同点ならtoken損失だけで行う。

`generalization-candidate.js` は実行11,000更新のうち8,000更新時点を選択した重み。検証153/160、評価162/178の厳密な全文一致。失敗には、使っている音響機器を聞くと好きなものを返すこと、CMF BudsのANCを電池持ちと取り違えること、未登録の学校や現在の為替へ無関係な本人情報を返すことがある。完全一致には正しい言い換えの不一致も含まれる。

以前の小さい全文候補は同じ178問で57/178。ただし、今回は既知の仕様項目と未知情報の回答を追加し、語彙・モデル規模・データ・事前学習をまとめて変更した。特定の変更だけの効果や、一般会話能力の比較ではない。一部の旧評価質問は再利用しており、次候補での同じ178問は開発回帰となる。

## Wikipedia以外の原文

`collect_web_language.py` は気象庁と農林水産省の公式解説・FAQだけを取得する。50ページ、61,232文字。天気、地震、火山、海洋、農業、米、豆、野菜、食品、畜産、林業、水産などを含む。サイトごとの利用条件、取得日時、URL、HTMLと本文のSHA、加工内容を `web-language-sources.json` に保存する。

出典：気象庁ホームページ・農林水産省ホームページを加工して作成。各ページのURLと出典表記は `web-language-sources.json` の `sources` を参照。両サイトの記録した利用条件は「公共データ利用規約（第1.0版）」で、規約本文は https://www.digital.go.jp/resources/open_data/public_data_license_v1.0 。HTMLから本文の見出し・段落を抽出し、空白、重複、ナビゲーション、連絡先を除去した。画像・添付ファイルは取得しない。公開機関が本モデルや加工したデータを作成・推奨したという意味ではない。

文章はページ単位で40訓練／5検証／5テストへ分ける。同じ原文の重複も除き、評価記事は語彙学習に使わない。生の文章を予測する事前学習と、質問へ答える対話学習の目標を分ける。FAQを切った冒頭だけで回答にすると、前提や説明が欠ける例があるため、回答用ラベルは単独で成立する完全な段落に限る。長文・外部参照・例の導入だけの文は原文用に残し、回答ラベルから除く。128トークンに収まらない回答例は記録して除外し、黙って切り詰めない。

`prepare_web_curriculum.py` は原文と訓練QAだけで独自byte BPEを再学習し、UTF-8の文字を壊さず最大64 BPEトークンの原文へ分ける。1,286語彙、原文1,249訓練／101検証／122テスト、対話3,478訓練／160検証／178テスト。うち122例は出典付きのFAQ訓練例。生文の検証損失で最も良かった事前学習の重みから対話学習を始める。事前学習で実行した回数と、出発点へ採用した回数は別に記録する。

## 実行と検証

```sh
python training/dialogue/prepare_generalization.py
PYTHONPATH=/tmp/4k29-torch-training TORCHINDUCTOR_COMPILE_THREADS=1 \
python training/dialogue/train_curriculum.py --compile-loss
python training/dialogue/collect_web_language.py
python training/dialogue/prepare_web_curriculum.py
PYTHONPATH=/tmp/4k29-torch-training TORCHINDUCTOR_COMPILE_THREADS=1 \
python training/dialogue/train_curriculum.py \
  --corpus training/dialogue/web-curriculum-corpus.json \
  --pretrain-steps 3000 --steps 10000 --length-buckets --compile-loss \
  --checkpoint /tmp/4k29-web-curriculum-checkpoint.pt \
  --output training/dialogue/web-curriculum-candidate.js \
  --artifacts-prefix training/dialogue/web-curriculum \
  --version 2026-10-04.dialogue-web-curriculum-1
```

途中のチェックポイントは250更新ごとにmodel・optimizer・乱数・選択中の重み・設定・データSHAを保存し、同じコマンドに `--resume /tmp/4k29-web-curriculum-checkpoint.pt` を加えて再開できる。長さ別バッチはバケットの合計重み、次に中の例の重みで選び、各例の周辺選択確率を維持する。短い例を毎回長い例までpaddingしない。

`evaluate.py` は各候補自身のトークナイザーで全文を自由なargmax生成し、異なる候補のtoken IDを流用しない。文型の制限、検索した答えの挿入、仕様値の固定出力は行わない。`evaluate_language.py` の損失・perplexityは別の記事の原文予測であり、自然な対話や事実・推論の評価とは区別する。実行と破棄した試験の区別は `web-curriculum-execution.json`。

公開サイトへの採用には、独立した質問での事実保持、未知情報の境界、文脈、自然さ、推論を確認する必要がある。小さな有限のデータとモデルの実験で、ChatGPT級の能力の実現を主張しない。

## 原文の学習効果を残す追加学習

原文3,000更新＋対話10,000更新を実行した `web-curriculum-candidate.js` は、検証150/160、開発回帰167/178。しかし別記事の次トークン損失は7.6184で、同じ語彙・構造の乱数初期化7.1891より悪かった。対話の例だけを覚えると、原文を予測する能力を忘れる現象が確認された。

そこで、検証で選んだ自作の原文事前学習750更新時点を出発点とし、対話学習へ原文の損失を0.15の重みで混ぜた。学習率は0.0003、対話10,000更新。自作の同じデータ・構造・seedを持つ親チェックポイントだけを受け入れ、出発点と親のSHAを記録する。他者の学習済み重みではない。親の更新回数を今回の実行回数へ二重に足さない。

```sh
PYTHONPATH=/tmp/4k29-torch-training TORCHINDUCTOR_COMPILE_THREADS=1 \
python training/dialogue/train_curriculum.py \
  --corpus training/dialogue/web-curriculum-corpus.json \
  --pretrain-steps 0 --steps 10000 --length-buckets --compile-loss \
  --own-pretrained-checkpoint /tmp/4k29-web-curriculum-checkpoint.pt \
  --replay-weight 0.15 --learning-rate 0.0003 \
  --checkpoint /tmp/4k29-web-replay-checkpoint.pt \
  --output training/dialogue/web-replay-candidate.js \
  --artifacts-prefix training/dialogue/web-replay \
  --version 2026-10-04.dialogue-web-replay-1
node training/dialogue/chat.mjs --question 'MERは？'
```

`web-replay-candidate.js` は360,288パラメーターで、検証149/160、開発回帰164/178。別記事の予測損失5.2247、perplexity185.81で、対話だけの候補のperplexity2035.29より改善した。ただし原文事前学習直後の検証損失4.3518から、追加学習後は5.2095へ悪化しており、忘却が解消したとはいえない。学習率・出発点も変えた比較なので、改善をreplayだけの因果効果とは扱わない。

原文評価は5つの未使用記事にある120 chunk・5,488 token。同じ記事を学習に入れないことに加え、token分割で偶然一致した「ります。」「ます。」の2 chunkを評価から除外した。同一語彙で比べた原文の予測指標であり、自然な回答の正答率や文法の合格率ではない。

## 固定した新しい質問と採用判断

`new-challenge.json` は、最初の2候補が完成し、replay候補の学習データ・設定も固定した後に書いた38問。訓練・語彙・検証の重み選択には使っていない。本人情報18、履歴4、挨拶等2、Web解説6、未確認情報8を含む。開発で見つかった課題の周辺を選んだ有限の診断であり、一般的な会話能力の代表サンプルではない。

| 候補 | 実行更新数 | 開発回帰178問 | 新しい38問 | 未確認情報8問で保留 |
| --- | ---: | ---: | ---: | ---: |
| 本人情報中心 | 11,000 | 162 | 19 | 3 |
| Web原文＋対話のみ | 13,000 | 167 | 24 | 6 |
| 自作原文学習から継続＋原文replay | 10,000追加 | 164 | 23 | 5 |

表の回答数は、EOS・UTF-8が有効な厳密な全文一致。意味が正しい言い換えも不一致になる一方、未知情報へ無関係な説明を返す、製品のANCと電池持ちを取り違える、「CMF Budsは生生です。」のような文を生成する失敗も残る。Web解説6問は全候補で全文一致0で、原文を学んだだけでは質問から知識を取り出して説明できていない。

今回の保持する3候補は実行34,000更新、破棄した試験の確認済み3,000更新を含めると最低37,000更新。これを架空の「思考回数」と呼ばない。replay候補はPyTorchとJavaScriptで178問の生成が一致し、4つの参照logitでも誤差0.0002未満。ローカルCPUの3つの短い質問・90回で温まった状態の中央値4.24ms、p95 5.52ms。モデル取得・画面・通信を含めず、他の規模や実機ブラウザーへの速度保証ではない。

**公開サイトの重みは置き換えない。** 自由な全文生成の日本語・事実・未知情報の境界が不足している。コード・出典付きデータ・重み・実測・失敗例を実験として保存する。次の改善では、仕様の項目・条件を区別する対話、本人の未確認情報と一般の説明を混同しない例、単独で完結した多様な回答、原文能力と対話能力を両方見る検証を増やす。この38問を次候補の改善に使った場合は開発用へ移し、別の未見問題を用意する。
