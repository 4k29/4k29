# Round29 — human everyday-conversation sampling mass10%

## 完了済み実測

実10000更新・全17件と日常12件の全文読解・数値比較を完了。選択9500、共通NLL0.971422→0.969489、会話DEV NLL1.288001→0.994147。初文8→6/17、全文意味0→0/17、日常全文0/12。NLL改善には成功したが言語改善未達、設定不採用、採用対照R25を維持。公開model/site変更なし。[RESULTS.md](RESULTS.md)・[採用判定](execution/adoption.json)を参照。以下の起動/途中snapshot説明は履歴であり再学習しない。

Single factor: same8975 human TRAIN dialogues and all three token views asRound28, sampling mass30%→10%. Against the last adopted scientific controlRound25 this is0→10%, old genre masses×90%. Same alignedRound11 parent, optimizer/RNG, own8-layer192dim model, vocabulary, objectives, LR, seed, context256 and10000 actual updates. Round28 is not adopted or made the baseline. No turnEOS/role labels or inference changes.

Round28 humanDEV NLL improved27.94% but common NLL and daily loops regressed. Test whether a lower dose retains domain learning without those regressions. Original strict gates/Pareto and additional humanDEV/daily nonloop guards remain unchanged againstRound25. NLL improvement alone never means semantic success. Fixed17 and daily12 are exposedDEV, not freshTEST. No public/site promotion.

The identical copiedsource-policy.json describes historical admission/filtering atRound28 (including its30% mixture), not this run sampling; policy.json is the authoritative frozen10% configuration. Source manifest binds both. SameCC-BY-SA4.0 provenance, train/dev/test hygiene and raw-only reserved hashes are reused; no newly acquired/test-encoded source.

Training and automatic mechanical evaluation run under execution/persistent.sh; actual retained steps only are reported. Full human-readable judgments require actually reading every raw output, never guessed by automation.

## 実行開始と最初の保存

全初期DEVが親と完全一致した後、2026-10-18T01:05:33Zにdetached controllerを起動。実100更新の整合checkpointとoptimizer/RNG・ログをexecution/retained-progress-100へ保存した。これは途中の固定snapshotであり、学習は10000更新へ継続する。最新の実数はcheckpoint.ptおよびexecution/train.logを確認する。最終評価・採用判定は未完了。

## 評価参照文の表示記録

評価rubric確認時にcompactな旧Round10 policyのTEST参照文の一部がツール出力へ表示された。execution/evaluation-reference-exposure.jsonに記録。モデルへのTEST入力・token化・生成・loss測定は行っておらず、学習fold/重み/selectorを変更しない。この旧参照文を今後の人によるblind/unseen評価とは扱わない。新しい人間会話reservedTESTは未アクセス。
