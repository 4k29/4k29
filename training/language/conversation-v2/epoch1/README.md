# conversation-v2 first epoch

GOAL.md/親STRATEGY.mdを引き継ぐ隔離実験。最初のTRAIN1epochの学習・固定評価・独立全文読解・再現性監査を実行した。**内容のある自然な対話は未達、正式採用なし。**

- 結果と失敗/復旧の制約：[RESULTS.md](RESULTS.md)
- 次期方針：[NEXT_STRATEGY.md](NEXT_STRATEGY.md)
- データ/ライセンス/資源：[DATA_NEXT.md](DATA_NEXT.md)
- 原典の実査：[jaquad-candidate/README.md](jaquad-candidate/README.md)（未採用、今回のTRAIN不変）
- 全文：[evaluation/](evaluation/)、固定後の独立ラベル：blind-reading-primary.json / secondary.json
- 工学監査：engineering-final-audit.json、training-audit.json
- 最終統合監査：verification.json

事前固定commit：c801a1f（学習/評価）、129ea60（数値整合）、b52b58d（保存名だけの再開修正）、6decd75（未保存92実更新の明示復旧）、317da30（read-only終端評価監視）。対応するPLAN/amendmentにはコード・原文・Tokenizer・checkpoint・panelのSHAがある。元の学習計画/コードは変更せず、復旧wrapperの限定変更を別記録とした。

学習コードcontinue_train.pyは既存512状態を継承する。実際の復旧はRECOVERY_AMENDMENT.json/recover_train.py/run_recovery.py。これらは当時の既存ledger/状態へ厳密に結び付けて重複実行を拒否するため、現在の作業場所でそのまま再実行するコマンドではない。再現学習は別checkout/output・新しい明示予算で、記録済みSHA/状態/順序/実数を維持して行う。自動追加epochは許可していない。

終端stateは `medium/archive/checkpoint.pt.chunks.json` と `small/archive/checkpoint.pt.chunks.json`。Gitに全partを収録し、作業コピーは容量のためsparseで省略している。この環境の空き容量でsparse解除しないこと。十分な保存領域のcheckoutでは既存 `training/language/round46/checkpoint_chunks.py restore <manifest>` でraw checkpointを復元できる。モデル/Adam/Torch RNG/private RNG/order/cursor/全historyをtrajectoryに含む。raw weightsの外部取得や公開モデルへの置換は不要。

既存checkpointの読取専用評価はEVAL_PLAN.jsonとevaluate_epoch.py、数値整合はPARITY_PLAN.jsonとparity_epoch.py。どちらもSHA一致と新規outputを要求し、出力上書き/モデル更新はしない。全56件greedy192、4episodeを同条件で評価する。新しいAI prompt APIは未検証で、人間A/Bのrolesをuser/assistantへ無条件に読み替えない。

検証：`python -m unittest discover -s training/language/conversation-v2/epoch1 -p 'test_*.py'`（18件）。`verify_epoch1.py` はGit中のchunk bytes、事前固定SHA、実更新・token量、全文評価・ラベルを確認する。`verify_jaquad_candidate.py --fetch` は固定TRAIN shardのみ取得して未採用sampleを復元検証する。

封印TEST、新しい本格追加学習、公開サイト反映、マージ、有料GPUは今回実行していない。正式な母語話者評価・相談/条件付き依頼/指示追従/独立TESTは未整備として残している。
