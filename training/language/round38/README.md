# Round38 — 実10,000更新と全文評価完了

人間のJMRD公式TRAIN会話4,575件を追加する1条件を検証した。共通DEV NLL/byteはRound37の0.967709から0.965013へ改善したが、日常12件の全文意味は最良・終了状態とも0件、人間の日常会話DEV NLLは0.933018→0.940388へ悪化。従来の厳格ゲートは不合格で、標準採用・公開モデル変更は行わない。

[結果・原因分析](RESULTS.md)、[再現・完全checkpointの復元](REPRODUCTION.md)、[旧新4状態168出力の全文](execution/ALL_FOUR_STATE_GENERATIONS.md)、[最終判定](execution/final-assessment.json)、[次の単独条件の提案（未実行）](NEXT_EXPERIMENT.md)。新モデル84状態出力は実読解済み（79種類のprefix/全文組）。露出DEVの診断であり新TESTではない。

独自8層×192・語彙5455・BPE40/30/30、R28 full model/Adam20000/RNG初期状態、全損失・LR・seed・human全体30%・10,000更新・selector・推論条件・固定ゲートを維持した。学習coreはR37とbyte同一。追加原文だけを既存samplerへ入れたため、旧RealPersonaの相対抽出割合は約30%から20%へ下がった。データ抽出とRNGは本実験自身のcheckpointに対して正確に再現し、旧モデルと同一の最終RNGであるとは主張しない。

最良9500（Adam29500）と終了10000（Adam30000）、初期・途中200/1000/5000の完全な重み・moments・RNGはSHA付きlossless partsに保存。新84/84のPy/JS・raw/export全文一致を確認し、既知R10 near-tie分岐も保持する。過去のmechanical pending記録は当時の状態で、最終状態はfinal-assessment.jsonを参照。研究anchorR25・公開サイトは維持する。
