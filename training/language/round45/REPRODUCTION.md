# R45の事前設定と再現

実更新0。source-manifest.jsonで入力を学習前commitに固定する。R44 selected/terminalは科学対照、初期状態はR28 latest full model/Adam20000/Python・Torch RNG。同じ固定CLI、CPU2 FP32 deterministic、seed2049、LR2.2499999999999998e-5、8層192dim/context256、batch8/10000updatesを使用。policyのcontextPreference.coefficientだけ0.1→0.2で全10core filesはR44とbytes同一。

開始前にverify_single_condition.py、preflight_data.py、preflight_sampling_probabilities.py、preflight_eos_masks.py、preflight_prefix_policy.py、preflight_context.py、43 unittest、preflight_initial_validation.py、verify_runtime.py、preflight_new_source_gradients.pyを実行。freeze_pretraining.py後の最終manifestをruntimeで再検証してから起動する。R44最終HEADのCI証拠はexecution/control-final-ci.jsonに保存しlaunchで確認する。

完了/稼働中runを再実行しない。部分stateのみ同一条件のresumeを使用し、実step/Adamcounter/traceを照合。全checkpoint・optimizer・RNGのlossless partsを保存する。selected重みとlatest optimizerを混ぜない。補助学習はevery10/batch2/cyclic/eval/fork_rng、wrong文脈は診断のみ。

データ・vocab・原典利用条件/splitはR44と同じ。raw原典cacheは/workspace/daily-conversation-source-audit/human-only-raw。新しい原典の意味監査をしたとはせず、同一資料に対する既存の読解履歴をSHA付きで再利用する。source/token全件監査と意味の全件監査を区別する。新TEST/外部重み/生成API/教師生成正例/出力修正は使わない。

開始前に容量確保したR43旧raw6状態はGitのlossless partsから完全復元可能で一意な削除ではない。R44/R45/R28/R25/R11状態を保持。WORKSPACE_STORAGE.mdとexecution/reversible-disk-cleanup.json参照。
