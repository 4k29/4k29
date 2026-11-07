# Round24 — 4gram反復抑制係数だけ0.1→1.0

Round23は実10000更新で最良NLL0.9714555771476026と僅かな改善のみ、17生成の全文/tokenはRound22と全件同じ、全文意味0/17。固定Round11初期weightsでTRAIN16batchを別プロセスで測ったUL/CE勾配norm中央値0.0253994366、係数0.1では0.254%。今回は係数だけ1.0（初期中央値2.54%）へ増やし、抑制不足仮説を検証する。初期診断は後半・自己生成への保証ではなく、係数不足を原因確定しない。

科学的対照Round23と同じ全prepared data・自作8層192次元/context256/5455語彙/40-30-30/ジャンルmass/LR2.2499999999999998e-5/batch8/CPU2FP32/seed系譜2049/10000更新/500更新検証。同じRound11最新model/AdamW/Torch/private Python RNGを復元する兄弟対照で、Round23からの単純延長ではない。

CE+1.0×causal repeated-fourgram completion UL。位置tの入力suffix3tokenと同じ過去trigramの次tokenを、直前64既観測completion位置から抽出、一意化・特殊ID<6除外・現在gold除外・masked target除外。-log(1-p)候補和/有効target数、p上限1-1e-6。未来入力/未来正解/自己生成教師/他モデル教師なし。正解原文を書き換えない。新規取得・再分割なし、Round22由来原文・出典・利用条件・予約7文書・重複監査をSHA参照する。

通常CE DEV NLLで選択、事前閾値0.9714555771476026。生成の見た目でstep選択しない。greedy full-vocabulary/max192/trueEOS/Python1thread、文章修正や推論penaltyなし。従来厳格な全scope/group言語ゲートを変更しない。17件は既存DEVで新TESTではない。外部weights/tokenizer/API/生成教師なし、TEST encode/loss/生成なし、公開モデル/サイト変更なし。

実行`bash training/language/round24/execution/run.sh`。未完了かつ稼働プロセスなしの場合のみ`--resume`。完了/稼働中を二重実行しない。原子的checkpointに最新model/optimizer/RNG/実counterを保存、採用FP32を別保存。persistent.shがチャット接続と独立に学習・機械評価・PR保存を行い、意味採点は全文読解後に追加。準備段階の実験更新0を完了としない。
