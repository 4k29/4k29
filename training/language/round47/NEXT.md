# 次の一条件

R47は不採用。次は研究対照R46（UL0.1）へ戻し、主CEの人間会話内の返答位置配分だけを変更する兄弟実験を候補とする。R47との単一条件差ではないためR47を科学対照とは呼ばない。R28同一初期fullstate/seed/doseから開始し、R46比較でdata/sampling/LR/UL/contextCE/model/selector/gatesを保つ。

旧active content CEのrow質量を保ち、真の直前発話と完全な返答を含む既存windowだけで返答contentへ集中。旧EOS位置/補助とnewline除外は保持、eligibleなしは厳密な旧CE。真の発話隣接・BPE/文字境界・文書末尾・crop/prefixmask・勾配・global denominator・RNG非消費を検証後に事前固定する。これはまだ訓練済みの成果ではない。
