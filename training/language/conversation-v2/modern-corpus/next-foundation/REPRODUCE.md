# 固定条件と再開

最初に `PLAN.json` の全入力SHAを照合する。計画は `f3f8f64` で登録したもので、結果を見て変更しない。`drive_common.py` は有限の共通予算と評価を実行するオーケストレータであり、モデル条件・意味採点・系列選択を自動調整しない。

この実験のBはPR104で独自乱数初期化から学習した系列の終端を継続する。今回新しく未学習モデルへ戻す実験ではない。両者とも新規AdamWを使用し、共通のdropout RNG、補助Python/NumPy RNG、scheduleを保存する。追加targetsが同じでも累積学習履歴は異なる。

実行中なら別workerを起動しない。`DRIVER_STATUS.json` とOSの実プロセス、`private/next-run/{A,B}/updates.jsonl` のcompleted行、最新checkpointのSHAを照合する。LIVE_STATUSは128更新ごとの保存済み位置で、直近の完了済みoptimizer呼出しと一致しない時間がある。

初回は `preflight.py` に合格した後、各armの `train.py --arm A --until 4` 相当を実行する。初回worker自身が別processで2→4を再現し、追加2更新をresume-validationとして記録する。すでに実施済みなので、この成果物から再開する際にやり直さない。

通常の継続は `train.py --arm B --until 1997 --resume` の形式で行う。arm、予算、保存位置はPLANに従う。完了receiptがある区切りは再実行しない。未完了intentとcompletedの不一致を推測で修復してはならない。

`artifacts/<arm>-<step>/checkpoint.json` と32MiB以下のchunkは、model、Adam、全RNG、sampler、trace、進行位置を含む全状態である。chunkの作業コピーが存在しない場合も、既存 `diverse-foundation/restore_checkpoint.py` とcheckpoint loaderはコミット済みGit blobから復元する。正式checkpointと旧Git履歴は削除しない。

別環境で再開する場合はmanifestから `private/next-run/<arm>/checkpoint.pt` へbyte-exactに復元し、対応する公開 `receipts/*updates.jsonl.gz` を同ディレクトリの `updates.jsonl` へ展開する。元の非公開journalが残っている場合は上書きしない。展開したjournalの完了更新とcheckpoint cursor、traceを照合する。`latest-checkpoint.json`、receipt、復旧検証結果も対応するものを保持する。RNGはcheckpointに含まれる。学習corpusとscheduleはこのディレクトリの固定版を用いる。

`summarize_journal.py` は実際にcompletedされたoptimizer呼出しを集計するだけで、学習を開始しない。保持、resume-validation、recovery-replayを分け、独立原文量と物理処理targetsを混同しない。live中の末尾未完行は完了更新へ数えない。

生成は `evaluate.py --arm A --step 1997`、内容評価は `panels.py --model A-1997`、文脈診断は `context.py --arm A-1997` の形式。evaluate.pyは対応する `checkpoint-01997.pt` とreceiptを読むので、raw作業コピーを整理済みの場合は先にmanifestからその名前へ復元する。生成出力の既存ファイルを上書きしない。旧/新DEVはすべて探索的な閲覧済み診断であり、封印TESTでも独立母語話者評価でもない。captionの短い補完と、意味を展開する段落、具体的な応答を区別する。

再開前の空き容量は実測する。workerの600MiB reserveに加え、atomic保存中の一時全状態とGit archive作成のピークを考慮する。作業chunkを整理できるのは、コミット・remote送信・全chunkと全体SHA照合・Gitからの全状態復元一致を確認した場合に限る。整理の証拠はreceiptsへ保存する。
