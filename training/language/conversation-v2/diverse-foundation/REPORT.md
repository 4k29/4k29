# 多様な日本語原文からの事前学習（実行中）

旧PR103の約205万tokensに既存RealPersona TRAIN約246万tokensと公式JMAの審査済みFAQ約1.5万tokensを加え、**4,518,175独立本文tokens /4,871,648一回読みtargets**を固定。新規原文のネット取得と旧原文の再利用を区別する。10M独立tokensは未達。JMRD公式TRAINは既存と同一SHAで再取得したが、既知の第三者コピー等のmovie-family隔離と固定標本の品質判定により最終学習へは0件。KokoroChat/ETCの本文は未取得・未採用。

8データ契約テスト、causal/teacher shift/finite gradients/PAD/Adam非共有/atomic/stale pendingの数値事前検証に合格。3つの異なる短い人間原文の識別可能prefixから末尾EOSまで、freshモデルが64更新で完全再現。これは335独立本文tokensの暗記診断であり一般化ではない。mainの重みへ流用しない。

共通1983更新/1,500,394targetsのA旧3470model＋zeroAdamとB ownfresh＋zeroAdamを実行中。Aは共通予算を完了し、別プロセス更新2→4のmodel/Adam/RNG/cursor/trace完全一致に合格。実呼出し1985＝保持1983＋検証2。旧原文NLLは6.5722→4.6470だが、全文生成は日付/数字/語句ループが増えている。厳格全文の手動判定とB比較は継続中。NLL低下を成功にしない。

最新の完了位置はLIVE_STATUS/receipt/updates ledgerで確認する。PLANは予定値、receiptは実績。B比較後に固定規則で選択し、選択armの未処理原文を一回読む残りへ進む。中断や再計算があれば失敗ログ/ledgerへ区別して残す。正式モデル採用・公開置換はNo-Goのまま。封印TEST/独立母語話者評価は実施していない。

原文出典、許諾と制限はRIGHTS.md、品質標本/保留はQUALITY_REVIEW、処理token/終端/長さ/話者はCORPUS_AUDIT、再現と復旧はREADMEを参照。原文/生成のキー衝突による初回評価保存失敗は本比較更新前で、旧PLAN/コードとFAILURESに保存し、生成文を修正せず保存形式だけ直した。実行後に最終集計と全文読解を追記する。
