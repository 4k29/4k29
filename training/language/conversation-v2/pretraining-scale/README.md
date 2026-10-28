# 日本語基盤・規模/初期状態比較

GOAL.mdを上位目標とし、PR102の結果から続く独立した探索的研究。外部の学習済みモデル、Tokenizer、生成API、サブエージェント、封印TEST、有料資源なし。公開モデル/サイトと旧採用ゲートは維持。

`PLAN.json`が更新前に固定したデータ・予算・3系列・選択規則。`corpus.jsonl.gz`は出典付きの研究採用原文、`schedule.json.gz`は1回読みの固定教師位置。JaQuAD抜粋へのEOSなし。短いWiki原段落にはPR102で確認した独立段落タスク境界だけを再利用。公開物はsource別CC BY-SA条件を保持する。元のcandidate/未審査標本作業ファイルはGit対象外。

採用は限定された研究用途。元の `../foundation-data/DATA-LICENSE.md`、`SOURCES.md`、source保存版を再利用。JaQuAD: So/Byun/Kang/Cho, SkelterLabsInc, revision05600ff310a0970823e70f82f428893b85c71ffe, CC BY-SA3.0。Wikibooks/Wikivoyage: Wikimedia20261001、各原文URL/revision/history/最後の寄稿者、CC BY-SA4.0。第三者引用・個人情報・品質不良を検出したfamilyは学習から隔離。全人間執筆・全事実の保証/全著者独立性/意味family完全独立は未証明。正式採用と研究学習のGoを区別する。

再現順: `prepare_candidates.py` → 固定標本全文読解/`admit.py` → `freeze.py` → `preflight.py` → `workflow.py`。現在は実学習開始済みなのでデータやPLANを再生成しない。`WORKFLOW_STATUS.json`と実ledger/receiptを確認してから、保存状態から明示的 `train.py --arm A --until 512 --resume`。完了receiptがあれば再実行を拒否。ambiguous intentは自動推測しない。

独立セッションsupervisorは有限A/B/C比較のみ実行する。最終的な系列選択は固定規則に従って保存し、選択した1系列のみ2966更新/2039651targetsの一回読みへ。途中出力を理由にLR、配分、採点ゲートを変更しない。

`python -m unittest discover -s training/language/conversation-v2/pretraining-scale -p 'test_*.py'`。
