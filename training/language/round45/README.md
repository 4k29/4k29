# R45 — correct-context CE coefficient0.1→0.2だけの比較

実更新0、開始前監査済み・最終入力固定前。唯一の学習変更はcorrect-context CE係数0.1→0.2。R44と全10core files/35データfiles/主sampling RP40%+JMRD5%/1024pool/own BPE5455語彙40-30-30/他loss/model8x192/context256/LR/seed/初期R28 fullstate/10000dose/selector/厳格gateは同じ。R44terminalの延長ではない。

全189166行/90strataの確率、全行EOS mask/文字境界、1024組のsource/token/concat/donor、43契約、finite勾配、初期model/Adam20000/Python・Torch RNG復元と全DEV0.9718989571266189の完全一致を検証。静的実行ファイル35件とmjsの存在/構文も確認。勾配比0.5046487は初期の2組とCE3行の標本比較で、全複合loss/学習後の最適性ではない。係数探索はしない。

今後は実10000更新、0/200/1000/5000/selected/terminal fullstates、全loss/実counter/SHA、旧新168全文・新84全文の実読解、PyJS/raw比較を保存する。既知DEVで新TESTではなく、TRAIN64の7/57も両方TRAIN。公開モデル/サイト/R25anchorは維持。予定10000を完了扱いしない。
