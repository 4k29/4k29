# Round41 — correct-context CE only

実更新0。R40の相対文脈softplusを、同じ原文next utteranceのcorrect-context CEへ変更する単一条件比較。科学対照R40/参考R39、同じR28 full model/Adam20000/RNGから実10000更新を予定。語彙、main BPE40/30/30、全main抽出、同じTRAIN補助256組、係数0.1/every10/batch2、LR、seed、モデル、selector、生成、全gateは固定。補助はcanonical追加露出として別計数。wrong forwardは診断のみで損失に含めない。公開モデル/研究anchor R25を維持。未訓練時点で意味改善は主張しない。
