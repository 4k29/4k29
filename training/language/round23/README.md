# Round23 — repeated-fourgram completion UL only

Round22でNLL0.9714611700632592へ改善した一方、全文意味0/17、反復4gram率64.07%となった。Round20/21の直前token全体へのULはNLL/全文意味を改善しなかった。今回は対象を絞り、次tokenが過去の4gramを再現する候補だけにCE+0.1ULを適用する。現在の入力suffix3tokenと一致する過去trigramに続いたtokenを、直前64の既観測completion位置から集め、一意化・特殊token除外・正解除外し、-log(1-p)を有効target数で平均する。p上限1-1e-6。未来入力・未来正解・自己生成/他モデル教師を参照しない。正しい反復がgoldなら抑制しない。teacher forcingの限界や別の語句への逃避は残り得る。

科学的対照Round22と同じ全prepared TRAIN/validation/tokenizer・同じRound11最新model/AdamW/Torch/private Python RNGからの兄弟対照。8層192次元/4655808parameter・context256・5455語彙・40/30/30・ジャンルmass・LR2.2499999999999998e-5・batch8・CPU2 FP32・seed系譜2049・10000更新・500更新検証は固定。新規収集/再分割は今回行わず、Round22人間原文の出典・ライセンス・原HTML・既存重複監査をSHA参照する。変えるのは学習目的だけ。推論は従来greedy full-vocabulary/max192/trueEOSを固定し、文章修正や推論時反復penaltyで評価を飾らない。

通常CE DEV NLL/byteでcheckpoint選択、事前成功閾値0.9714611700632592。従来言語ゲートを維持。既存17書き出しは露出済みDEVで新TESTではない。TEST encode/loss/生成は行わず、公開モデル/サイトを変更しない。外部weights/tokenizer/生成API/教師文章なし。

実行: `bash training/language/round23/execution/run.sh`。未完了で稼働プロセスがない場合だけ`--resume`。完了/稼働中runを二重実行しない。checkpointは最新model/optimizer/RNG/実counterを原子的に保存し、採用beststateとは区別する。persistent.shがチャットと独立に実学習・機械評価・PR保存を進め、意味判定は全出力読解後に追加する。準備段階の実験更新0を完了数にしない。

実施結果: 実10,000/10,000更新、optimizer counter20,000。最良NLL0.9714555771476026（採用9,500更新）。全17生成はRound22と全文・token同一、全文意味0/17、言語ゲート不合格。[結果](RESULTS.md)と[全文](execution/FULL_GENERATIONS.md)を参照。
