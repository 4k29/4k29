# Round22 — 人間原文のカバレッジだけを増やす対照

Round21はUL係数0.3でNLL・反復が悪化し全文意味0/17。通常CEのRound19を科学的対照とし、同じRound11最新model/AdamW/Torch/private Python RNGから開始してTRAIN原文だけを追加する。Round21から更新を延長した実験とは区別する。

最終採用は45単位23,961文字（JMA38単位20,908文字、MAFF7単位3,053文字）。原文の見出し・段落を保持し参考資料より前で閉じ、元のRound3 chainsと同じ単位化・元doc ID/startLineの分割seedを使用。全旧TRAINのtoken prefix/index/unit、validation、独自語彙5455を保持。40/30/30・ジャンルmass・8層192次元・context256・LR2.2499999999999998e-5・seed系譜2049・batch8・CPU2 FP32は固定。データ追加で長さと実exposureの軌跡は変わるため、同じ更新数だけで純粋な意味効果や統計的優位性とは言わない。

収集前のpolicyと不成立/品質修正の4attemptを保存。採用下限30単位15,000文字2sites、単位160..1536文字・日本語率50%・2文以上は変更せず、モデル更新や生成を見る前にURL発見範囲と見出し保持を修正した。現行source HTML、出典・著者・加工・公共データ利用規約snapshotとSHAを保持。第三者画像や資料は使わず、本文を書き換えない。予約文書7件はencode/evaluateしない。旧非TRAIN原文627文書と追加の既存予約原文・新予約文書への64文字重複を機械監査し、旧TRAINと新TRAIN相互重複も除外した。TEST本文を重複監査だけに読み、loss/生成/選択には使わない。近似・言い換え重複なしの保証はしない。

要求は実10,000更新、検証500ごと。通常CE weighted DEV NLL/byteで選択し、事前閾値0.972624845997683と比較。従来の全scope/groupの厳格な言語ゲートを変更しない。17件は露出済みDEVで新TESTではない。外部weights/tokenizer/生成API/教師文章を使用せず、公開モデル・サイトを変更しない。

実行 `bash training/language/round22/execution/run.sh`。未完了だけ`--resume`、稼働中・完了済みを重複実行しない。persistent.shがチャットと独立して学習・機械評価・実counterと重み/optimizer/RNGのPR保存を行い、意味判定は全文読解後に追加する。準備段階の実験更新0を完了とは扱わない。

実施結果: **10,000/10,000更新完了**、optimizer counter20,000。採用9,500更新時NLL **0.9714611700632592**（Round19最良0.972624845997683を改善）。全文意味は旧新とも0/17で言語ゲート不合格。結果は[RESULTS.md](RESULTS.md)、旧新17件の無加工全文は[execution/FULL_GENERATIONS.md](execution/FULL_GENERATIONS.md)。checkpoint.ptに最新model/optimizer/RNG、selected-weights.ptに採用FP32を保存。完了済みrunを重複実行しない。
