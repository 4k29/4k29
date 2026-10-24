# R45 — correct-context CE coefficient0.1→0.2だけの比較

実学習継続中。初期0と実200更新のfull model/Adam/RNGを保存・監査済み。予定10000更新と最終意味評価は未完了。唯一の学習変更はcorrect-context CE係数0.1→0.2。R44と全10core files/35データfiles/主sampling RP40%+JMRD5%/1024pool/own BPE5455語彙40-30-30/他loss/model8x192/context256/LR/seed/初期R28 fullstate/10000dose/selector/厳格gateは同じ。R44terminalの延長ではない。

全189166行/90strataの確率、全行EOS mask/文字境界、1024組のsource/token/concat/donor、43契約、finite勾配、初期model/Adam20000/Python・Torch RNG復元と全DEV0.9718989571266189の完全一致を検証。静的実行ファイル35件とmjsの存在/構文も確認。勾配比0.5046487は初期の2組とCE3行の標本比較で、全複合loss/学習後の最適性ではない。係数探索はしない。

今後は実10000更新、0/200/1000/5000/selected/terminal fullstates、全loss/実counter/SHA、旧新168全文・新84全文の実読解、PyJS/raw比較を保存する。既知DEVで新TESTではなく、TRAIN64の7/57も両方TRAIN。公開モデル/サイト/R25anchorは維持。予定10000を完了扱いしない。

426入力を実更新0のcommit5b82cd7d81ddf83b7ab0088bd7c9508edc49bd42で凍結。実200更新では主target318964/bytes1106433とPython・Torch RNGが旧R44同時点に完全一致し、全重み/momentsはfinite。auxは20calls/40pairs、Adam20200。重み差は能力改善とはしない。初期checkpointはR28 model/Adam20000/RNGと一致、設定係数0.2を確認。初期snapshot作成前のread-only照合はFileNotFoundとなったが、作成後のwaiter照合はPASSし、訓練の再実行や追加optimizer更新はない。
