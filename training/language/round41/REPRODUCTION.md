# R41 再現

唯一の変更はcontext_preference.pyのlossをcorrect.mean()とすること。R40 NEXT_EXPERIMENT.mdの固定計画に対応。事前にpool/source/token/mask/finite勾配/RNG/初期DEVを確認し、freeze_pretraining.pyで入力を凍結してからpersistent.shで実行する。存在するcheckpointには--resume必須。完了10000を二重実行しない。補助呼出1000/2000組をmain露出と別記録。全評価は露出済DEVであり新TESTではない。最終意味評価は実生成全文を読んでから行う。
