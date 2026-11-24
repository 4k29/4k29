# R44 — 主会話sampling 25%→40%だけの比較

実10000更新完了。会話DEV NLLは改善したが、selected日常全文0/12・従来0/17、terminal日常2/12・従来1/17。厳格ゲート/固定実用条件は未通過で不採用。公開モデル・サイト・R25anchorは維持。

[結果と原因分析](RESULTS.md) / [旧新4状態168全文](execution/ALL_FOUR_STATE_GENERATIONS.md) / [再現・checkpoint復元](REPRODUCTION.md) / [次の一条件](NEXT_EXPERIMENT.md)。新84全文を実際に読み、83種類のprefix+全文を整合照合。Py/JSとraw/exportは84全文一致。旧R10 near-tie16/17を隠さない。

学習後に診断用mjsのコピー漏れが判明し、評価だけ再開した。元失敗ログを保存し、最終完了はexecution/evaluation-recovery-complete.jsonとfinal-assessment.jsonで確認する。学習の追加実行や途中条件変更はない。
