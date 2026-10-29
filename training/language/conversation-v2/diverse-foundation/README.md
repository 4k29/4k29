# 多様な日本語原文からのfresh事前学習

GOAL.mdとPR92–103を継承する隔離研究。サブエージェント・外部学習済み資産・有料資源・封印TEST・公開置換・マージは使用しない。

`RESUME_STATUS.json`と`LIVE_STATUS.json`、`run/*/updates.jsonl`が現在位置。予定と完了を混同しない。最終結果はREPORT.mdへ保存する。今回の独立本文は4,518,175tokens、全一回読みは4,871,648targets。10M独立tokensは**未達**。原文を反復して10Mと記録しない。

## 入力と比較

11,225,280パラメータ、独自BPE3997、context256を維持。原文は旧PR103で承認したままの境界。RealPersonaは既存TRAINの人間A/B role3/4と各発話EOSを維持し、assistant役割へ変更しない。原典の人間体験をAIの体験の教師としない。JMAは元の質問と全回答段落を一つのFAQ sectionタスクとし、その実際のsection終端をEOSとする。JaQuAD抜粋と256位置へ偽EOSを足さない。

A：旧medium3470重み＋新規Adam。B：同じ独自構造をseed41029でfresh初期化＋新規Adam。両者は同じtraining RNG、全causal CE、LR、データ順、教師位置、追加targets。PR103 B/Cと同様に初期model履歴だけを比較する。Aの過去の約2.82Mtargetsを消したことにしない。同じ追加学習量は同じ総学習量ではない。

共通1983更新＝1,500,394targetsを比較する。固定全文ゲートの成功数が同じならNLLだけで旧重みへ固定せず、今回のfresh学習の問いに答えるためBを優先。選択系列は新しい原文位置を一回ずつ読む残りだけを学習する。midpoint4232、terminal6459。成功・停止・応答学習へ進む条件はPLAN.jsonに固定。NLLやEOSだけの改善は成功ではない。

各条件の更新2→4を別プロセスで再実行し、全model/Adam/RNG/sampler cursor/traceのdigest一致を検証。検証の追加2更新と保持更新は別計上。3つの異なる短文の識別可能なprefixからの続きを暗記する補助診断は本学習と別の隔離重みであり、未知文章への一般化ではない。

## 再現

既存PR103とmedium3470を取得したcheckoutを使用する。PyTorch/NumPyは数値計算にのみ使用。独自Tokenizerを外部資産で置き換えない。

1. `python training/language/conversation-v2/diverse-foundation/acquire.py`：15ページの公式JMA FAQをcache付き・低頻度で取得。原典snapshotはsources/とACQUISITIONへ保存。
2. JMRDはRIGHTS.mdのpinned公式TRAIN URLを取得しSHA `4c8abd2e8913a7f2bc208052e8934f3af937c72636b573ea2dbfb83ec6945eaa`を確認、`sources/jmrd-train.raw.json`にローカル保存する。旧取得内容と同一なので新規独立量へ加算しない。knowledge等を含むrawはGit対象外。最終TRAINは審査により全JMRDを隔離しているため、保存済みcorpusによる学習・検証にはrawは不要。
3. `prepare.py`→保存済みQUALITY_SAMPLE/QUALITY_REVIEW→`admit.py`→`freeze.py`。**完了済みPLAN・corpusを上書きしない**。再構築は別作業コピーで行いSHAを比較する。原典再取得版が変わった場合は新研究条件として扱う。
4. `python -m unittest discover -s training/language/conversation-v2/diverse-foundation -p 'test_*.py' -v`
5. `preflight.py`→`health.py`（完了済みを再学習しない）→`workflow.py`。workerは明示的`--resume`以外で既存ledgerを再実行しない。
6. 比較後は全文を読んで固定規則に従いSELECTION.jsonを作り、選択armを`train.py --arm B --until 4232 --resume`のように次の固定地点へ進める。Bの採用を事前の能力成功とは扱わない。

## 復旧と保存

未完pendingは完成済みcheckpoint.ptを置き換えない。intentsとcompletedが一致しなければ実更新数を推測せず停止する。最後の完成checkpointから先にcompletedだけが存在する場合、recovery-replayとして既存traceに照合し、実呼出しを別に数える。初期2更新の特殊保存after2.ptしかない場合は、そのSHA/trajectory/ledgerを検証してから作業用checkpoint.ptへatomic復旧し、更新2以降を同様に再開する。確認不能なintentを削除してなかったことにしない。

全状態はarchive.pyで32MiB以下にlossless分割し、wholeSHA・全状態digestの読み戻し確認後だけraw作業コピーを整理。Git履歴・正式R25/R46と元checkpointを保持する。STORAGE.jsonは旧encoded TRAINの作業コピーのSHA確認済みsparse省略。今回のoverlayでは物理空きの大幅増加は観測されず、削除対象サイズを回収済み容量としない。実際の開始空き約3GiBとcheckpoint保存予算で実行する。

## 評価の限界

旧24、新9、新JMA12、TRAIN probes4を全語彙greedyで比較し、raw token列/bytes/停止理由/無修正全文を保存。既存の内容24/資料23/限定36/反転12/自己履歴4episodeも保持。すべて研究DEVで、封印TESTや独立人間評価ではない。新JMAは3ページfamilyの分離であり全著者・広いtopic独立性の証明ではない。原典にも時点依存の運用情報や単純化された説明があり、参照文を無条件の事実正解としない。未確認の人間評価を実施済みと記録しない。

全文の意味成立・反復・EOS・文脈適合を別判定。短い正しい文末補完と、段落の展開能力と、内容応答を区別する。PR103との違いはデータ、Adam初期状態、shuffle等を含むため、横断比較を純粋なデータ要因効果とは呼ばない。
