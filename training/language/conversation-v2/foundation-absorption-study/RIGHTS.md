# 既存許諾・品質審査の継承範囲

新規コーパスのネット取得0。PR115 head `003666efa4331397b59a6b0d5256772c9f28d073` から既存の研究用原文を再取得した。候補全量や未審査の新Wiki資料を一括採用していない。

- JaQuAD/Wikipedia：既存PR103/104の限定研究採用分。CC BY-SA3.0、各recordの原ページURL・dataset revisionとlicenseを継承。元のWikipedia個別改訂・人間/ボット著者の完全確定はできず、純粋な人手執筆と主張しない。原文引用・年表・指摘された問題familyは今回追加保留。
- Wikibooks：既存PR104採用済みのうち、最終改訂が2022年より前のsubsetのみ。CC BY-SA4.0、各recordに版ID・history URL・最終寄稿情報を保存。pre2022は人間執筆の完全証明ではない。遺伝子説明の疑義があった章、推測的入試記述、過剰な力分類の断言を除外した。
- 環境省白書：PR106で採用された連続原文のsubset。原典URL・年度・段落・SHA・PDL1.0/CC BY4互換・加工表示を継承。第三者コラム・引用・図表等は元の除外条件を維持。年度差の近重複3件も追加保留。現在の制度事実として保証しない。
- STAIR：PR105/106の採用可能な未使用注釈pool、CC BY4.0。元注釈IDと画像familyを保持。MIX579とPR105で未選択の注釈であり、一部画像は既知。文末EOSは注釈の終了であり段落ではない。画像の正確性や個別作業者の独立性は今回再判定していない。
- RealPersona：既存TRAINの役割・発話順・匿名話者・真の発話末EOSを維持。既存の出典・利用条件を各record.provenanceから継承。人間A/Bをassistantの実体や個人体験へ変換しない。今回の会話は保持用で、基盤段落原文とは別集計。健康・診断等の個人的記述は追加で保留。

Wikimediaの帰属・継承条件、STAIRの帰属、政府の利用条件と非推奨表示、RealPersonaの元条件は既存 `diverse-foundation/RIGHTS.md`、`modern-corpus/next-foundation/LICENSE_NOTICE.md`、`mixed-retention-study/LICENSE_NOTICE.md`、各recordのprovenanceを参照。この追加研究stateは正式モデルや無条件の商用モデルへの承認ではない。人間執筆性・全事実・第三者権利を包括保証したとは扱わない。モデルの公開禁止があるichikara等を追加していない。

公開するのは今回採用した原文と公開可能な監査メタデータ。保留した原文本文や健康情報を圧縮・base64等で再配布しない。LF1化・選択・token化は研究処理であり、政府・原著者が作成または推奨したモデルではない。

FAQはPR115最終372TRAINと固定DEV19のみを参照する。393/385旧系列は使用しない。FAQの質問・回答そのものは基盤TRAINへ混入させず、原典family/文字列/近重複を確認する。MAFFはsource-held-out、今回TRAIN0。封印TESTは開かない。
