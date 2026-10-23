# R40 再現と監査

科学比較R39、初期化R28 latest aligned checkpoint（Adam20000）、採用anchor R25。R39 terminalの単純延長ではない。唯一の学習変更は、固定TRAIN原文256組によるcontext-preference補助目的（0.1/every10/batch2/softplus/zero margin）。正しい文脈と同長の別文脈で、同じ元の人間発話の平均token NLLを比較する。別文脈で絶対に不自然というbinary正解は付けない。

元のmain CEのデータ・語彙・40/30/30抽出・source25/5・全既存目的係数・モデル・LR・seed・10000dose・selectorはR39と同一。補助目的はcanonical BPEの追加forwardであり、**全目的を合わせた追加target exposureが40/30/30になるという主張はしない**。mainと補助のexposureを分離し、context-preference.jsonlへ全1000呼出/2000組とtarget数を記録する。evalモードで勾配を計算し、fork_rng/model modeを戻すので、main抽出とdropout RNGの対照一致を最終確認する。

## 実行前

`execution/context_diagnostic.py prepare`は固定64組のTRAIN診断のみ。学習前とR39selectedを同じ組で評価済みで、0更新・TESTアクセスなし。補助poolは`prepare-auxiliary`の1616候補を`refine_pool_as_executed.py`で学習前に256へ絞った実施記録。原文の64組を読んだ監査と、全256の機械検証の範囲を区別する。これらは将来の全pool意味保証や新TESTではない。現存poolを上書きしない。

`test_*.py`、`preflight_data.py`、`preflight_prefix_policy.py`、`preflight_eos_masks.py`、`preflight_context.py`、`preflight_initial_validation.py`でデータ、勾配、RNG、初期状態を検証。設定/コード/入力を`freeze_pretraining.py`で凍結し、`verify_runtime.py`でSHAと既存目的を検証してから開始する。

## 学習と再開

`bash training/language/round40/execution/persistent.sh`は重複lock付き。10,000回の実optimizer更新を要求し、CPU2/FP32で実行。checkpointはmodel/optimizer/Torch RNG/private Python RNG/実step/補助呼出数/生のrollout履歴へ対応する。100ごとの保存と500ごとの既定DEV検証、selected full-state保存、200/1000/5000 full-state保存。途中状態を再開する場合のみ同じコマンドへ`--resume`を付け、稼働中・完了済みを二重実行しない。context traceは保持stepに合わせ、未保持分を別ファイルへ退避する。

## 評価

同一42入力・greedy192・Python1thread・全語彙で科学対照R39と新selected/terminalを比較。全168状態出力を保存し、新84全文は実際に読んで意味、係り、語順、接続、反復、逸脱を判定する。既存DEV、日常12、native8、source5は新TESTではない。全scope/group言語gateと固定humanDEV bound0.9107185711429243/daily whole0/nonloop4を維持。Py/JS、rawFP32/exportの新84全文一致も確認し、既知R10 near-tie分岐は隠さない。補助損失やcontext gainのみで採用しない。公開モデル/サイトは変更しない。

## 保存領域

`execution/reversible-disk-cleanup.json`はR37/R38の無視対象raw state復元コピーのみ削除した記録。全chunkのGit追跡・各SHA・連結SHA・raw SHAを削除前に検証した。unique model/optimizer/RNGは消していない。必要なrawは対応する追跡済みchunks.jsonから`checkpoint_chunks.py restore`で同一bytesへ復元できる。R39凍結成果は変更しない。
