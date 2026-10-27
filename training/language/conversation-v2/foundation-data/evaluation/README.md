# 内容必須DEVの評価基盤

相槌だけ、短いEOSだけ、NLL低下だけを成功にしない。旧17/13/9厳格ゲート・Pareto・日常反復上限・R25 anchor/R46比較対象/R48 No-Goは変更しない。今回は評価基盤を実装・検証した段階で、モデル推論・optimizer更新・正式な人間評価は実施していない。

## 実際に整備した件数

| 系列 | 件数 | 原文/正解の性質 | 測れることと限界 |
|---|---:|---|---|
| 提供文脈付きQA DEV | 32 | JaQuAD upstream TRAINから新コーパスDEV記事だけを選択。質問/回答spanは原典の人手注釈、本文はWikipedia由来 | 明示情報の取り出し・比較への内容応答。自然なassistant全文の人手正解ではない。百科/歴史固有名詞が多い |
| 原文の文章継続 DEV | 12 | 原文段落を実際の句点位置で分割。prefix＋参照restを結合すると完全な元段落 | 文意味/文法/文章接続の全文生成。参照と完全一致する必要はない。記事内の段落依存や古い時点の表現を含む |
| 研究者作成入力のみDEV案 | 24 | Codexが入力と意味基準を作成。正解返答なし、人間原文ではない、学習禁止 | 質問2/理由2/比較2/説明2/相談2/条件付き依頼4/履歴参照8/外部知識2。人間の正解・独立人間評価・TESTとは数えない |

合計68入力。人間QA32件の実際の内容タグは通常の事実質問25、比較7であり、人間原文の理由/説明/相談/条件付き指示を網羅したとは主張しない。研究者作成24件は、提供情報で判断可能な22件と、外部知識を必要とする2件を別表示する。履歴参照は4つの最小対で、同じ最終質問でも前の情報に従って必要な内容が変わる。

## 分離と原典の監査

pipelineの最終combined splitにより、記事/書籍familyとexact・正規化・near-paragraph duplicateの連結componentをTRAIN/DEV/reserveへまとめて割り当てた。評価はJaQuADのDEV58記事のうち入力が完全に収まるものだけを使用し、評価familyとcandidateTRAIN componentの重なり0をチェックする。upstreamDEV/TESTは取得していない。reserveはpipelineが原文を扱った保留領域で、**封印TESTではない**。新しい独立TESTは未整備。

当初の固定SHA順候補は34QA。全文の原典照合で次を発見し、モデル出力を見る前に2件を隔離した。補充・言い換え・正解修正はしていない。初回選択34IDと隔離後32IDの関係はselection-history.json、元の誤注釈/本文はquarantined-source-cases.jsonに残す。

- `tr-597-09-003`：再版年を聞く質問なのに、正解注釈1873年が別の火災年を指す。本文の再版年は1870年。
- `tr-247-20-001`：質問の「スクールメイト」と本文「スタークルメイト」が一致しない。

`tr-365-00-000`の「大量で読んだ」という不自然な原文もそのまま残して懸念を記録した。**人手注釈・offset一致は意味上の正解を保証しない。** 他の全31,748QAが意味監査済みという主張はしない。現32QA/12文章継続をCodex担当者が全文読んだが、日本語母語話者による独立評価の達成ではない。

QA32件は一記事一問。文章継続と合わせると33記事familyで、同じ記事/段落のDEV内重複がある。68件全部を独立標本として合算せず、系列別・category別・knowledge mode別・family別に評価する。意味的な言い換えfamilyまで全て検出したとの保証はない。長い完全文脈は4,217QAで入力192token上限を超えたため除外された。この短文選択の偏りはcontext256の制約として記録する。

## 入力契約と実装

`build_dev.py` は原文context/question/人手answerとURL・固定revision・rawSHA・family/componentを保存する。本文/正解の生成や修正はしない。`build_challenges.py` はCodex作成入力のみと明記した別ファイルを生成する。

`freeze_plan.py --final-split <final-article-splits.json>` は最終splitを照合してPLAN.jsonにコード/入力/Tokenizer/checkpoint SHAを固定する。現在は **inferenceAuthorized=false**。学習開始やモデル評価を自動で認可する計画ではない。

`run_benchmark.py --plan PLAN.json --plan-sha <SHA> --prepare-only` は68入力のencodingとbudget適合だけを確認し、重みを読まない。生成の実行にはrootが事前固定した別の明示Goが必要。推論時もown中型3470終端のみ、optimizerを作らず、model/RNG不変をチェックする。全vocabulary greedy、QA/入力案64tokens・文章継続128tokens、no crop/mask/penalty/repairで、無修正全文・byte/token列・TFを保存する。

現モデルのrole3/4は人間A/B用であり、QAの「資料/質問」ラベルは評価側の追加serializationである。AI応答の役割が学習済みとは言わない。この新形式で失敗しても、容量不足や文脈利用不能だけの因果証明にはならない。

## 採点とGo/No-Go

RUBRIC.jsonは全文の文法、適切性、具体的内容、提供文脈との整合、制約、参照、反復、逸脱、終了をtrue/false/nullで分ける。短い相槌や入力反復だけは内容失敗。参照spanの字面一致は不要で、文脈に適切な言い換え/全文を許す。抽出span末尾のEOS尤度は便宜的TF指標で、自然な返答がそこで終わらなければならない条件ではない。

機械集計はEOS/UTF8/特殊token/4gram反復だけでsemanticSuccessを返さない。全文を条件名を伏せて独立に読み、不確実性/不一致を保存する。正式な採用には追加の人間原文category、母語話者評価、独立封印TEST、既存厳格ゲートが必要。現在はそのGo条件を満たしていない。

検証：`python training/language/conversation-v2/foundation-data/evaluation/test_benchmark.py`。TRAIN component漏れ、component変化、生成正解の混入、context超過の隠蔽、隔離注釈の改変を防ぐ6テストを実行した。モデル推論/追加学習は0回。
