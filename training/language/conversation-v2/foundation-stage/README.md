# Modern Japanese foundation v1

PR100から分岐する隔離した探索的基盤学習。正式採用/公開置換とは別の判断として、既存原典監査と今回の固定標本63件＋追加12件の読解を利用し、採用条件をPLANへ固定した。

## 原文・リスク・境界

元23.35M候補全体は引き続き未採用。このdirectoryの `data.jsonl.gz` のみを限定研究に使用する。出典はJaQuAD宣言TRAIN由来のWikipedia context、日本語Wikibooks/Wikivoyage公式20261001 dump。固定版・取得SHA・元license・rights根拠は `../foundation-data/sources/` と `catalog.json`、全原文archiveは同既存ディレクトリに保存済み。

JaQuADはSkelter Labs/JaQuAD authors、CC BY-SA3.0。Wiki本文は各pageのcontributor/history/revision URLに帰属し、CC BY-SA4.0。データ加工物の各recordに元のlicense/URL/revision/履歴と加工元SHAを維持し、一括した別licenseを付けない。JaQuADの人手QAという出版社の説明はWikipedia本文が全て人間執筆という証明ではない。Wikiも最新editorや年だけでbot/AI未混入を証明しない。残る執筆性の不確実性は、隔離した基盤研究のリスクとして明示して受容する。原典事実の全件検証や、現在の旅行/法律助言への適用は承認しない。

引用/個人情報の疑い、code/list、過度な法律/専門・古語を除外。標本で発見した誤記・図表参照・不自然な文・未検証の強い断定はunit/familyで隔離。特定の政治的立場を合格条件にせず、今回の中立的な自然/文化/科学説明というscopeと品質で選別する。残る小さな文体/事実の不確実性もQUALITY reviewsに記録し、全sourceを一律拒否する基準にはしない。権利申立て時はprovenanceで対象unitを隔離し、将来scheduleから除く。学習効果の完全な個別削除は保証しない。

候補→固定標本読解→subset採用→追加標本→最終dataという履歴を別fileで保持。`admitted.jsonl.gz` は中間subset、**学習に使用する最終版はdata.jsonl.gz**。DATA_AUDITに最終実数を記録。人間原文の書き換えや外部生成APIによる補完はしない。

JaQuAD contextは記事の連続全文ではないため、各contextを独立fragmentとして扱い、BOS/EOSを付加しない。Wikiは元の派生page paragraph ordinalが連続する部分だけを連結し、真のprocessed-page先頭/末尾が残る場合のみBOS/EOSを付ける。途中の選別・256窓境界には特殊tokenを挿入しない。原典pageを跨がず、全target位置を一回だけ処理。PADはloss対象外。paragraph parserによる省略の限界は既存pipeline監査を保持する。

旧splitを維持し、既知component/familyの横断0。確認できるWiki最終editorはTRAIN/DEV分離。JaQuAD原著者IDは不明で、全contributor/意味family/地理topicの独立は未証明。新DEVは未学習文書の探索的診断であり、封印TESTでも独立母語話者評価でもない。

## 実行

PLANのSHAを照合してから `python train.py`。既存3470のmodel/Adam/RNGをdeepcopyして継承、plain proseの全CE、同じ3997BPE/context256、LR3e-5/clip1/CPU2/FP32。1回読みの有限予算で、4更新時の実プロセス再開一致に合格してから継続する。固定terminalを採用研究endpointとし、DEV best選択しない。最初の4更新も保持数に含み、子の2replayは実callへ別加算する。

`python -m unittest discover -s training/language/conversation-v2/foundation-stage -p 'test_*.py' -v` は境界/target一回性、分離、atomic保存例外を確認する。初段real-modelゼロ更新PREFLIGHTは4batchのfinite loss/grad/独立CE・100Adam状態を確認済み。

SIGTERM/SIGINTは次の更新境界でatomic保存し、`python train.py --resume`。完了receiptがあれば追加更新を拒否。保存後に完了した未保存更新は固定RNGからreplayし、保存済みloss/gradient traceと照合して実callに加える。intentだけ残った曖昧な中断は、実行回数を推測せず停止・報告する。未完了.pendingは完成snapshotと見なさない。

原型 `../grounded-objective` のcheckpoint作業コピーだけをGit blob照合後にsparse省略して空きを確保。元blob、履歴、正式モデルは保持し、必要時は旧共通loaderのGit fallbackで復元できる。

学習/評価/次段階の実績は後続REPORTとRESUME_STATUSへ保存する。自然な文章と適切な応答は別評価とし、NLL改善だけで次段階達成にしない。
