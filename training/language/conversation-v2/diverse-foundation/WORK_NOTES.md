# 再開用作業メモ（作業中・成果の完了宣言ではない）

- 単体メイン、サブエージェント禁止。独立branch `research/diverse-japanese-foundation`、Draft PR104。base PR103 `46fcd97a...`、旧成果/R25/R46維持。
- corpus 4,518,175 body tokens = PR103 2,045,786 + RP TRAIN2,456,893 +新JMA15,496。10M未達。one-pass4,871,648targets/6459updates。ROLE3/4は人間A/B、EOSは真の発話/section終端、JaQuAD偽EOS0。
- 固定PLANは変更不可（数値モデル/runner/dataSHA固定）。共通1983updates/1,500,394targets各arm完了。A旧3470重み+zeroAdam、Bfresh41029+zeroAdam。同じdropout RNG/schedule/自作BPE3997/context256。
- 全文読解A common old24=1,new9=0,JMA12=1,train4=0; B common0/0/1/0。段落展開両0。固定規則A選択（SELECTION）。NLL優位や最小補完を汎用能力としない。
- A midpoint4232/3,200,477targets完了。oldNLL4.33647, new9NLL4.23608, JMA4.57177。全文49件読解 old1/new0/JMA1/TRAIN0、段落0、反復40/45。MIDPOINT_REVIEWは固定残りだけ継続Go、追加epoch/SFTなし。
- 現在A terminal6459へPopen継続中。`LIVE_STATUS.json`、receipt/ledgerが実数。`continue-primary-terminal.log`、`continuation-A-6459.log`。実行系は別プロセス2→4の全状態完全一致、各arm追加実呼出し2。health独立64updates/335bodytokens、識別prefix3件すべて完全再現（一般化ではない）。
- FRESH_COMPLETION_PROTOCOLをA終端結果前に事前登録。Aが言語ゲート失敗ならBの未処理1984..6459を同じschedule/LRで一回だけ完了する追加診断。元のA選択は書換えない。B common1.5Mだけではfreshを否定しない。開始前free>=1.5e9。追加4476updates/3,371,254targets、epoch追加なし。B rawは整理済みなのでrestore_checkpoint.pyでarchive-01983から戻す。
- 両arm fullならmain retained12918、actual+resume4+health64=12986。Aだけfullならmain retained8442、actual8510。実数はstatus.py/verify.pyから再集計、予定を完了としない。
- 空きはLIVE/dfで確認。旧lower-layerのsparse省略は物理空きを増やさなかった。今回のGit照合済み新archive作業chunkと重複rawの省略で回収できる。全Git原本保持。gc.auto/maintenance.autoをlocalで無効にし巨大自動packを避ける。
- health/archive、A/B archive-01983のpart*.binはGit登録後に作業コピーのみ省略（skip-worktree+sparse）。whole manifests残存。restore_checkpoint.pyはmissing chunkをGit HEADから読みSHA一致でatomic復元。health全stateをGitのみからbyte/tensor一致で復元実証済み。
- A archive-04232は保存済み・Gitへpush中/済。checkpoint-04232.ptの重複hardlinkは削除しrolling A/checkpoint.ptは維持。次はmid chunksをHEADと照合して省略し空きを回収。末尾もarchive→Git保存→作業chunk省略。全checkpointを失わない。必要ならfull .ptはarchive SHA確認後だけ整理。
- 原典→corpus→scheduleを別siblingで再構築しbyte一致（REBUILD_PROOF）。cached acquisition時刻の書換えを修正。変更したのはprepare/acquire等、学習済みtoken/runnerは変更なし。
- JMRD再取得は旧と同じSHA4c8abd...の公式TRAINのみ、valid/TEST未取得。259映画familyのコピー疑い+最後のfamily品質保留でTRAIN0。raw49MBはlossless gzipへ圧縮しローカル非公開。未審査candidate中間もGit対象外・作業copy整理済。公開品質標本のJMRD本文はSHA/理由だけへ置換。初回pushが取消と競合した来歴はFAILURES、元初期commitはlocal-audit ref保存、リモート旧objectの完全消去は未保証。既存PR103以前の履歴は変更していない。
- MAFF将来候補54ページ10,471tokens、proxy50/9,515、固定8全文読解6有用/2事実保留。現TRAIN追加0。青空文庫は権利/metadataだけ、作品本文0。候補量を451万tokensへ混算しない。

## 残り

1. A terminal receipt+evaluation49件を確認・全文読解し記録。actual optimizer数、loss/clip/時間/RAMを集計。
2. language未達ならFRESH_COMPLETION_PROTOCOLどおりB remainingをone-pass完了。source code/PLANを変更しない。B current .pt欠落→restore_checkpoint.py B/archive-01983/checkpoint.json B/checkpoint.pt、train.py --arm B --until4232 --resume、固定mid eval/読解、then6459。元PLANのmid snapshotは4232で自動生成。secondaryは元選択とは別の探索診断。
3. 各mid/terminalはarchive.py raw folder（--removeはsnapshotだけならrolling currentを保持）。Git登録・commit後、各32MiBchunkをGit blobと照合しworkingのみskip-worktreeで省略。原本/Git historyを削除しない。余裕600MiB維持。
4. terminal labelsについて evaluate_panels.py --model A-6459/B-6459（native24、provided23、grounded36、context12、self-history4）。prefix/promptもJSON保存。3turn未完なら偽EOS/正解履歴差替え禁止。出力全文を読む。基盤未達なら応答SFTなし。
5. diagnose.py --arm <label> --label <label>、context.py --freeze後 --arm initialA/<terminal>、parity_terminal.py --models <terminal labels>（3prefix×4token limited JS）。source metadata/NaN/実行失敗はログ保存し修正結果と区別。サンプリング補助sample_aux.py --model <label>は固定8prefix/T1/top_p1/seed51029、greedy採点と別。
6. render.py（sampling loop追加可）、plot.py、匿名盲検評価用package（実際の独立母語話者評価なしを明記）。TRAIN_PROBE_EXPOSUREでcommon/mid probeが実更新済みか確認。TRAIN splitだけで暗記診断成功/失敗としない。
7. REPORT/NEXT_STRATEGY/resource estimates/SUMMARYを実測に基づいて完成。予測精度≠自由生成、初期既往学習差、未達10M、全人間執筆/著者独立性未証明等も明記。正式R25/17/13/9/Pareto/public採用No-Go維持。
8. 最終status.py、8契約testとverify.py。verify.pyはstdlibでfrozenSHA/全archive byte streams/全raw生成/ledger実数を検証（Git fallback）。最終MANIFEST generatorはまだ未実装。Git ls-files対象だけ、自己/circular outputとmutable live filesは除く。
9. 全worker完了→最終Git commit/push、Draft PR104本文をREST gh api PATCH JSONで更新、現headの専用CI/root CIを確認。rootcheckout約20分、finalheadを待つ。マージ・公開置換・paid resourcesはなし。

## 最終実績

A/Bはともに6459保持更新/4,871,648targetsの一巡完了。補助health64と更新後再開検証4を含め実optimizer呼出し12,986、実処理9,768,244targets。コーパスは4,518,175本文位置で、新規取得の採用JMAは15,496のみ。原文位置の周回は0。全49×8モデル時点に加え旧応答panel、補助sampling/日常文/health/context-edgeのrawを保存。主・終端とも段落展開は0、内容24/資料23/限定36/自己履歴は0。主ゲート未達なので応答追加学習なし。独立人間評価0、未採点の90件packageのみ。正式採用/公開置換No-Go。

ローカル旧root全体は935pass/27ENOENT（省略した作業コピー）。3つの影響test fileをGit/SHA一時復元して通した後、別testで多数の旧checkpointが必要となり850MiB容量guardで停止した。失敗・復元履歴は保持。残りの独立18コマンドは通過。ローカル全体を通過したとしない。GitHub clean checkoutの最終head結果をPR104 Checksで確認する。新研究の13テストはskipなし通過、全7状態/836 raw生成を照合。
