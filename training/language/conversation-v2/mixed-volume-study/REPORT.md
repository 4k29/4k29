# 多ジャンル混合・未使用教師位置の追加学習（環境切断時点）
 
## 状態と結論

**実験は未完了。実行環境が unavailable となり、累計80万・100万targetsの保存と全文評価には到達を確認できていない。能力改善の結論は出せない。**

PR108 MIX-579から新しいrun ID `mixed-volume-v1`で継続した。最後に外部出力で確認した追加保持更新は128回・131,072targets（累計721,216）。切断後の進行・optimizer呼出し総数・プロセスの終了状態は未確認。Gitへpush済みの復旧可能な新規完全checkpointは4更新・4,096targets（累計594,240）。「計画401更新」を完了数としない。

予定の80万／100万評価、追加学習後のcaption／段落／内容応答／自己履歴の成績は**未測定**。PR108の21/32・0/5等を今回の学習後の成績へ転記しない。正式採用・公開置換No-Goを維持するが、仮説の失敗判定ではなく未完了として扱う。

## 完了した事前監査

- 採用済み7sourceのみ。新規コーパス取得0、追加epoch0、外部モデル/Tokenizer/API・サブエージェント・有料資源0。
- 旧590,144原典教師位置をIDとLF変換前の原典位置で照合。新たな409,856教師位置との重複0。合計1,000,000位置のscheduleを推論・更新前に固定した。
- JMA採用済みTRAINは15,581targets。旧使用8,851、LF1後の未使用の原料上限6,730。このうち6,149を分割・重複等の条件下で選択できた。残る全位置の品質を無条件に保証する値ではない。
- 追加教師は非LF本文398,650、LF1,240、EOS7,333、role2,633。任意の窓にEOSを追加せず、別文書を連結しない。RealPersonaは人間A/Bのまま。
- 原文の連続順・byte復元・teacher shift/loss mask・既知DEV/話者/画像family除外を既存監査と同じ方針で検証した。Wikiの人間単独執筆・地理semantic family・未知著者の限界を解決済みとは主張しない。
- PLANの49入力SHAを更新前に固定。初期model/Adam/RNGはMIX-579、SHA `fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7`。Adam step6940を継承。旧579更新は再実行していない。
- 独自11.23M、BPE3997、context256、LF1、通常causal CE、LR1e-5、clip1.0、全語彙greedyを維持。
- 追加scheduleは401更新。205更新で追加209,856＝累計800,000、401更新で追加409,856＝累計1,000,000の計画。等target予算bucket内を固定hash順で配置し、長さ順のまま前半短文・後半長文に偏ることを避けた。各sourceの最終累計比率は40/15/7.5/6/1.5/20/10%。中間だけのsource比率は必ず別集計する。
- 捨て状態で2更新保存→別process復元→3更新目が完全一致。model/Adam状態非共有、初期状態の非破壊を確認。`PREFLIGHT.json`と`REPLAY_PROOF.json`。
- 最初の4保持更新は全loss/gradient有限、clip4/4。sourceや本文の教師数はUPDATESに実数保存。
 
## 原文配分（完了量ではなく固定予算）

|source|PR108使用済|今回追加予定|累計予定|
|---|---:|---:|---:|
|環境省白書|236,058|163,942|400,000|
|JaQuAD|88,522|61,478|150,000|
|Wikibooks|44,261|30,739|75,000|
|Wikivoyage|35,409|24,591|60,000|
|JMA|8,851|6,149|15,000|
|STAIR|118,029|81,971|200,000|
|RealPersona|59,014|40,986|100,000|
|合計|590,144|409,856|1,000,000|

再利用原文であり、新規独立取得量として加算しない。モデルには過去の他実験の学習歴もあるため、追加位置をモデルにとって完全に未知とは呼ばない。

## 更新数と保存の確定範囲

Gitの`7b230f851d2c2532e9d0524e01539690344d19f2`時点のledgerはintent/completedとも8件＝保持4＋捨てoriginal3＋検証replay1。保持4の実targetsは4,096。完全checkpointの全体SHAは `c5d722cae1bc2b30a9b5640bec7de2ed871dd676d9e7888b92163053f892b7f3`、5個のlossless chunkをpushした。

その後、同じrunは少なくとも保持128まで進んだ。直近の外部stdout確認値：

- 追加cursor128、追加targets131,072、累計721,216。
- 完全checkpoint保存SHA `ce1dce240eb93e69b9875c70957f6e18bdd164db9df0b4bff195e6213d58d009`（当時のscratch latest、Gitへのpush未確認）。
- 当該process経過106.201秒、step128 loss4.086193、clip前norm2.318211、clipped=true。
- 実optimizer呼出しは少なくとも132回＝保持128＋検証4。正確な最終回数は環境のfsync ledgerを回収するまで未確定。このprocessは205更新で止まる設計で、401までの次段階は開始していない。

中間・終端の完了・保存・cold Git復元・評価を達成済みとは記録しない。最初の4更新だけでも改善成功と認めない。

## 実行環境と問題

CPU quota2・RAM8GiB・GPUなし。PyTorch2.14.1+cpu、2threads。preflight時/tmp約4.08GiB、永続領域約455MiBの空きを確認した。最初の4保持更新のprocess時間4.138秒、最大RSS1,076,484KiB。全体学習時間とは異なる。

再開時に前回/tmpと/dev/shmは消失していたため、新しいfiltered sparse cloneとGit上のMIX-579から復旧した。既存Git履歴・正式重みを削除しない。最初の再利用コピーで旧model.js等を過剰にコピーしたが、原本とSHA照合した新しい作業コピーだけ整理し、元ファイルは保持した。`WORKSPACE_COPY_CLEANUP.json`参照。

新規4更新のcold Git検証は、初回fetchがpush完了より先行したことと、独立bare検証repoのpromisor設定が一時的な-c指定だけだったことによってメタデータ読取りが失敗した。合計3試行、optimizer/forward0。設定を永続化しmanifestのGit読取りは成功したが、全chunk再構成・torchによる新規4更新状態のcold検証は未完了。Git-only検証に合格したとしない。初期MIX-579の全状態復元とpreflightの別process再開一致は別途完了済み。

その後exec-server transport disconnected、さらに`No usable execution environment is available`となった。管理statusがrunningを返しても、実際のコマンド実行は利用できず、復旧を確認できなかった。切断がOOMかサービス障害かは未確定。これをモデルの数値不具合とは断定しない。終了・強制停止を確認できないプロセスを「安全停止済み」とも主張しない。

## テスト・CI

4つの軽量テストと凍結artifact/教師位置監査に合格。専用CI [run42723604775](https://github.com/4k29/4k29/actions/runs/42723604775) はcommit `7b230f8`でsuccess。GitHub connectorからjob/stepsのsuccessを再確認した。これは事前監査と保存済み4更新ledgerの整合を検査した結果で、80万/100万の学習や全文生成成功の検証ではない。

無関係static-profile run42723613061は取消要求を送り、合格とはしない。環境切断後の追加は本報告・再開メタデータのみで、凍結学習コードや過去PR108を変更しない。

## 再開条件と次の研究

まず同じ実行環境の/workspace側fsync ledgerと/tmp側最新checkpointを回収し、全体SHA/integrity、model/Adam/全RNG、sampler/cursor、trace、PLAN/schedule SHAとintent/completedを照合する。保存済みコードと49入力SHAはGitにある。

**Git保存4更新へ無断で巻き戻して再実行しない。** 128以降の実更新は未確認であり、同じ教師位置の再学習・不確実呼出しの隠蔽を避ける。ledgerがcheckpointより先行、またはintentが不確実なら既存guardどおり停止して回復監査を行う。環境の状態が失われていた場合は、このrunを不完全として保持し、replayの扱いを事前に定義した別の回復計画が必要。

次に行うことは新しい仮説の追加ではなく、**この固定401更新実験の状態回収と、重複を避けた正確な継続**。80万・100万で固定全文評価を実施できるまで、学習率・容量・context・データ品質の優先順位を新しい結果から選べない。PR108時点の原因候補を維持し、追加epochへ進まない。

公開モデル・サイト、正式R25/R46、厳格ゲート、封印TEST、PR108の結果は変更せず、PR109はDraftのままでマージしていない。
