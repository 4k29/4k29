# Round27 — FFN容量だけの比較

実用ジャンルは日常会話。Round26は共通/会話DEV NLLが改善しても初文8→6でWiki混合を不採用とした。最後に採用したRound25を科学的対照とし、約束した第3候補「容量」だけを検証する。人間会話TRAIN追加は別roundとし、本roundには混ぜない。

変更はFFN hidden768→1536だけ。パラメータ4655808→7021248、8層/埋め込み192/4head/context256/独自語彙5455は固定。同じ準備済みTRAIN/DEV/独自BPE40/30/30、teacherUL1.0+sequenceUL0.1every10、LR2.2499999999999998e-5、seed2049、batch8、CPU2threadFP32、実10000optimizer更新、500更新ごとの従来DEV CE選択を維持する。

Round25と同じRound11 latestからmodel/AdamW/Torch RNG/private Python RNGを整合初期化する兄弟対照。旧座標の重みとmomentsはbitexact保持。追加incomingは独自seed2049/std0.02、outgoingと追加bias/momentsは0で初期関数を保持。追加incomingの初回勾配0はzero-outgoingによる想定通りで、outgoingは非零、2回目以降incomingも学習することをtoy試験で確認。AdamW tensor counter10000を継承し、新座標だけ独立したbias補正年齢ではない。旧座標初期系譜49000、新座標0を区別する。

actual model/moment/RNG/勾配/source preflightを完了（experimental updates0）。16件の容量・厳密resume・chunk・損失/rollout試験が合格。初期共通DEV差は最初のoptimizer更新前に5e-7以内を要求する。固定Pareto採用基準、17/13/9とジャンル別の従来厳格言語ゲートは変更しない。全出力を無加工保存し全文を読む。日常12件と人間DEV99も同じ条件・同じ原文で比較し、露出DEVとして扱う。TESTを開けず、NLLだけで会話能力を認定しない。

起動はexecution/persistent.sh。独立controllerが実学習、機械評価、checkpointの40MiB SHA付き分割、PR保存を継続する。raw full checkpointは100MiBを超えるためgit除外し、完全なmodel/optimizer/RNGを含むlossless partsを保存する。selectedとlatestを混ぜない。実完了数はcheckpointとexecution/train.logで確認し、準備を完了学習と記録しない。公開モデル・Webサイトは変更しない。

実10000更新と全文読解を完了。共通NLLは僅かに低下するが、日常会話は0/12で会話NLLは微悪化。任意のNLL-only採用は行わず、次の対照はRound25。詳細はRESULTS.md。
