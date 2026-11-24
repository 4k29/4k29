# R44終了時の次案 — R44中は未訓練・実更新0

correct-context CE係数だけ0.1→0.2へ変更する。RP主配分増加で会話NLL/文脈利得は改善したが、selected日常全文0/12で短い語形/主述崩れが残ったため、元人間の正しい文脈と発話を学ぶ寄与の強度を検証する。誤文脈は診断のみとし、別モデルの正解や生成修正を使わない。

科学対照R44、同じR28 full model/Adam20000/Python・Torch RNGからの兄弟比較。R44terminalを延長しない。RP40%/JMRD5%、他genre比、pool1024、資料bytes/own BPE/40-30-30、CE以外の全loss、every10/batch2/cyclic/eval/fork_rng、model/context/LR/seed/実10000dose/selector/生成/全gateを維持。公開/R25anchorは維持し、NLLだけで採用しない。

all10 core codeが同じか検証しpolicy coefficientだけを変更する。補助gradient増加のfinite検証と実traceを記録する。初期/主draws/RNGの対照照合と、旧新selected/terminalの全168全文・会話99・TRAIN64の7/57とpool1024・PyJS/rawを比較。新資料/role tags/容量/追加dose/主配分を同時変更しない。R44終了時点ではこの次案の実更新0。
