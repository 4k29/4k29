# Mixed volume study — Draft PR109

結果は[REPORT](REPORT.md)、数値は[TABLES](TABLES.md)、次の一条件は[NEXT_STRATEGY](NEXT_STRATEGY.md)。追加401保持更新・409,856targets、累計1Mで完了。追加epochなし、正式採用No-Go。

## 証拠

PLAN/PLAN.sha256、SOURCE_AUDIT、PREFIX_POSITIONS、POSITION_MAP、schedule、TEACHER_AUDITが事前固定した入力と原典教師位置の対応。UPDATESは実405呼出しをintent/completedで記録。捨て3・検証replay1・保持401・切断復旧replay0を分ける。RECOVERY_AUDITは切断後に205更新を回収して正確に再開した証拠。

artifacts/VOLUME-{4,205,401}はmodel/Adam/全RNG/sampler/cursor/trace/PLAN/SHAを含むlossless全状態。GIT_RESTORE-{4,205,401}でローカルcheckpointやalternatesなしのremote-only Git再構成と全状態integrityを検証済み。初期は親PR108のMIX-579を参照し、旧579更新を再実行しない。

各evaluation JSONに全prefix/token/raw bytes/停止理由/無修正text。主要129件と自己履歴を読解し、余分な20件はraw保存のみ。READING/REVIEW_CARDS/SCREEN/REUSEで読解と機械的な必要条件違反、同一出力の再利用を区別する。record_readingは読解後の記録器であり汎用的な自動意味採点器ではない。

## 復旧

新しい空き領域へfiltered sparse cloneし、研究ブランチを参照する。元/workspaceの一時Git cacheや/tmpだけに依存しない。リポジトリrootから例：

```sh
python training/language/conversation-v2/mixed-volume-study/restore_checkpoint.py --revision origin/research/mixed-volume-extension --cursor 401 --output /tmp/VOLUME-401-restored.pt
```

各chunk→全体SHAの照合、atomic出力を行い、既存ファイルへ上書きしない。終端SHA `001522713b3a7adc1f3c419dd259a1f99a4cdedc86957f27b442ad2a93320a41`。初期MIX-579の復元は[PR108の手順](../mixed-retention-study/README.md)。信頼した自身の検証済みstateだけをtorch.loadする。

完了したrunのcursor401を巻き戻して再更新しない。ledger/checkpoint不一致や不確実intentはfail-closedで回復監査が必要。

## 再集計（optimizer/forward0）

```sh
python -m unittest discover -s training/language/conversation-v2/mixed-volume-study -p test_contract.py
python training/language/conversation-v2/mixed-volume-study/ci_audit.py
python training/language/conversation-v2/mixed-volume-study/final_audit.py
python training/language/conversation-v2/mixed-volume-study/summarize.py
python training/language/conversation-v2/mixed-volume-study/verify_results.py
```

再集計には親PR108の既存評価・Tokenizer等を同じSHAで用意する。sparse checkoutが既存依存・旧設定/評価ファイルを省略しうるので、実行前に49固定入力と元依存を確認する。新版原文を再取得して混ぜない。CIは重いstateを大量checkoutせず、4テスト・固定artifact/ledger・旧prefixとの重複0/完了405呼出し・cold復元receiptの整合だけを確認する。

## 保存領域と復旧経緯

REPORT-INTERRUPTION、RESUME_STATUS-before-recovery、各operational receiptを保持。元repo背景差分によるpromisor cache取得の対策はPERSISTENT_SPACE_RECOVERY、LOCAL_DIFF_GUARD、PAGE_CACHE_ADVICEを参照。正式重み・Git refs/historyは不変。巨大weight exportのbinary指定は元repo .git/info/attributesだけのローカル表示設定で、追加前の内容も保存してあり戻せる。packディレクトリの一時保護modeは終了時に元へ戻す。

/tmpのGit object alternatesは環境消失で失効しうるため、次回は新規sparse cloneとGit archiveを優先する。状態やcacheの一時copyだけを永続保存保証にしない。
