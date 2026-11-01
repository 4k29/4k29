# 現代日本語コーパス拡充（継続作業中）

GOAL.mdに向け、PR104の完了済み学習を再実行せず、新しい種類の独立原文を取得・検証する。研究ブランチは `research/modern-japanese-corpus`、Draft PR105。サブエージェントは使わない。

現時点でGlobal Voicesの2022年以前の公開記事2,676件を取得した。独自BPE3997で原文候補7,023,700本文tokens、機械フィルター後1,392,965tokensである。**いずれも採用量ではない**。第三者引用・転載・写真説明・前後関係の欠落があり、無条件のTRAIN投入はしない。45段落の追加固定標本はすべて読解し、判定理由を `CENSUS_QUALITY_REVIEW.json` に保存した。独立人間評価ではない。

公式のCC BY3.0、再利用方針、AI方針、robotsを確認し、取得は10秒間隔。制限された利用者APIは使わず、公開RSSから原著者・翻訳者・原文リンクを確認中。公開記事100件とRSSの原著者名は100件一致した。配信元の不正XMLは原本を保持し、失敗履歴と本文を修正しないメタデータ回収を別系列で保存する。

連続段落の候補は7,596単位で、除去した引用・見出し・別記事をまたいで結合しない。EOSは未承認のまま。既存採用済みTRAIN/DEVとの完全一致・32文字shingle検査では一致0だが、すべての近重複や著者独立性を保証しない。封印TESTは開かない。

別の文章種として、大阪市の再利用条件を確認し生活手順の公式HTML8ページを実取得した（候補29,624tokens）。第三者資料、PDF・画像、外部コールセンター本文は採用しない。農林水産省の既存54回答は全文読解を完了し43回答8,058tokensを研究候補としたが、新規取得量には数えない。追加取得の一部カテゴリは403を記録し、拒否URLは再試行・回避しない。青空文庫7作品20,775tokensは取得したが、歴史的な文体・内容のため今回の現代日本語主資料では保留。

新研究の学習更新数・採用tokensは**0**。取得、権利確認、品質候補、正式採用を分け、条件が揃うまで学習を強行しない。既存モデル・公開サイト・Git履歴は変更しない。

実行・再開の要点：

- `RESUME_STATUS.json` と各取得STATUS/receiptを確認し、実行中プロセスの重複起動を避ける。
- `acquire_census.py` / `analyze_census.py`：元レスポンスSHA、全件byte復元、候補集計。
- `collect_feed_credits.py`：公開RSS出典取得。`recover_feed_metadata.py` は不正XMLから出典だけを別系列で回収。
- `build_prose_runs.py` / `audit_legacy_overlap.py`：連続性と既存採用原文との照合。
- `python -m unittest discover -s training/language/conversation-v2/modern-corpus -p 'test_*.py' -v`
- `verify_public.py` は公開メタデータの整合性検査。private原本の再取得・SHA復元をCIで実施したことにはしない。

未審査・隔離本文は `private/` に置きGit対象外。公開receiptからCookie等を除き、本文SHAは維持する。詳細な途中経過は `WORKING_PROGRESS.md`。まだ最終結果ではなく、処理と審査を継続する。
