# 未採用の現代日本語・人手QA候補の原文監査

JaQuADの固定revisionのTRAIN先頭shardだけを取得した。790,020bytes、24記事/355contexts/1002QA。全文はtmpfs上のみ、SHA/URL/取得時刻をretrieval.jsonに保存。DEV/TEST・既存baseline重み・既成Tokenizerは取得していない。30段落/18記事/87QAを固定SHA順で抽出し、無修正の原文と既存の人手QAをsample.jsonに保存した。CC BY-SA3.0はLICENSE.txtとATTRIBUTION.mdを参照。現TRAINへの追加やモデル評価には使用していない。

root assistantが30段落を全文読んだ。全て百科事典の説明・歴史・伝記として意味を追えるが、4段落に明瞭な語句/句読点/翻訳調の懸念、7段落に前段・表への参照がある。引用元の権利や事実精度は未検証で、現代文の表記であることと日常会話の内容分布は同じではない。1shardの18記事という偏った小標本から全体の品質率を推定しない。正式な人間母語話者評価ではない。判断ごとの理由はquality-reading.json。

現在の独自BPEで13,122文字→11,671tokens、1.124文字/token。RP TRAINの約1.700より効率が低い。未見glyph47種/73出現はbytefallbackで完全復元でき、87回答の原文offsetも全て一致した。30段落中22は256tokensを超える。Token列が復元できることは、現モデルが説明文を理解/生成できる証拠ではない。現RP187,667発話との空白正規化後の段落丸ごとexact一致は0だが、近重複・意味・記事familyの独立性は未監査。

**判断：資料全体の学習投入は保留。** 記事revision/原著者・引用帰属、genre品質、近重複、TRAIN/DEV/将来TESTの分離、Tokenizer効率とwindow設計を確認する。原文の不自然さをLLMで修正したものを正解にせず、除外/加工の理由を記録する。QAの抽出spanは、そのまま自然なassistant全文の正解ではない。

再取得・無修正sample/offset検証は `python training/language/conversation-v2/epoch1/verify_jaquad_candidate.py --fetch`。取得先は固定TRAIN shardに限定される。
