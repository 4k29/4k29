# Round17 — 現代日本語TRAINの段落完結性対照

実10,000更新を完了。採用追加step9500、共通開発NLL0.973998407（Round16最良0.974345326から約0.036%改善）、全文意味0/17、Python/JS17/17。自然な全文生成の改善は未実証。詳細は[RESULTS.md](RESULTS.md)、無修正全文は[execution/FULL_GENERATIONS.md](execution/FULL_GENERATIONS.md)。

Round16と同じRound11最新重み・optimizer・RNGから実10,000更新を行う兄弟対照。変更は現代ジャンルTRAIN内の段落選別のみ。青空文庫、ジャンル比、40/30/30分割、語彙、8層192次元、終端LR、検証と厳格な言語ゲートを保持する。原文を改変せず、既存利用条件とfoldを維持する。句点等2個以上・末尾文終端・日本語文字50%以上という機械的条件は意味の自然さを保証しない。新規原文・ジャンル多様性の追加とは扱わない。

実行: `bash training/language/round17/execution/run.sh`。未完了のみ`--resume`。完了数はcheckpointの実counterで確認する。公開モデルは変更しない。
