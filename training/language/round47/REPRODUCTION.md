# R47 reproduction — actual0

policyのsequenceUnlikelihood.coefficientだけ変更。全10core/35資料はR46と同一。R28最新model/Adam20000/RNGの完全対応状態から、固定10000更新を予定。未実行を完了扱いしない。preflight/frozen input確認後にpersistent.shで開始し、既存partialだけ正確な--resumeを使う。完了済みの再学習は禁止。

CP0のoptimizer LRは親2.25e-5のまま完全一致し、実updateではR46と同じ4.5e-5が適用される。総lossは係数が変わり同単位の学習能力指標にならない。各loss/DEV/全生成を別に比較する。生生成の空白を含め改変しない。

データにはimmutable hardlinkがあるため直接上書きしない。新しい資料条件を行う別roundでは独立copyかatomic replaceを用いる。
