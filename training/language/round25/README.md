# Round25 — 自己生成中の反復だけを追加の負例にする

R24は実10000更新、最良CE NLL0.9714231061588403、初文7/17、非長期ループ4/17、全文意味0/17。反復率は64.855%で改善しなかった。teacher forcingの履歴だけでは自己生成した反復状態を学習しない仮説を検証する。

単独変更: CE+1.0 teacher-forced causal fourgram ULに、0.1 self-generated sequence ULを10更新ごとに追加。最初にdrawした真のTRAIN行の先頭min32tokenから、自身の現在weightsでgreedy full vocabulary/最大64token/trueEOS生成。過去64completion中に既出の4gramを完成する生成tokenだけを負例として-log(1-p)で抑え、全生成位置で平均、p上限1-1e-6。生成文章を正解CE教師にしない。追加損失とCEを合算してoptimizer.stepは1回だけ。10000実更新/1000rollout予定、実数をcheckpointと全training-rollouts.jsonlで記録。生成・負例位置数はhuman原文exposureと分ける。

R24と同じaligned Round11 latest model/AdamW/Torch/private Python RNGから始める兄弟対照。8層dim192/hidden768/context256/vocab5455、BPE40/30/30、データ全bytes・ジャンルmass・LR2.2499999999999998e-5・batch8・CPU2FP32・seed系譜2049・500更新CE検証を固定する。R24selected weightsにlatest optimizerを混ぜない。R24後の累積10000更新とは記録しない。追加rolloutのfork_rngでCE dropoutのglobal RNGを消費せず、model modeも戻す。

実行: `bash training/language/round25/execution/run.sh`。未完了・非稼働時だけ`--resume`で整合checkpointから再開。100更新atomic checkpointにはweights/moments/RNG/実counterとrollout累計を保存。未保持stepのrolloutは再開時にarchiveし、保持trace欠落や累計不一致は拒否する。完了済みrunを二重実行しない。persistent.shはチャット接続と独立に学習→機械評価→PR保存を実行する。

最小CE DEV NLLだけでcheckpoint選択、閾値0.9714231061588403。旧新17同入力greedy max192/trueEOS/Python1thread、全token・無加工全文を保存し、全文を読んで厳格な初文/非ループ/全文意味ゲートを維持。露出済みDEVを新TESTと混同しない。自己生成損失は訓練のみで、推論penalty/出力修正なし。外部weights/tokenizer/API/他モデル教師なし。新しい原文と容量の変更は別ラウンド。公開モデル/サイト変更なし。
