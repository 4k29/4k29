# R45 — correct-context CE coefficient0.1→0.2だけの比較

実学習継続中。初期0と実200・1000更新のfull model/Adam/RNGを保存・監査済み。予定10000更新と最終意味評価は未完了。唯一の学習変更はcorrect-context CE係数0.1→0.2。R44と全10core files/35データfiles/主sampling RP40%+JMRD5%/1024pool/own BPE5455語彙40-30-30/他loss/model8x192/context256/LR/seed/初期R28 fullstate/10000dose/selector/厳格gateは同じ。R44terminalの延長ではない。

全189166行/90strataの確率、全行EOS mask/文字境界、1024組のsource/token/concat/donor、43契約、finite勾配、初期model/Adam20000/Python・Torch RNG復元と全DEV0.9718989571266189の完全一致を検証。静的実行ファイル35件とmjsの存在/構文も確認。勾配比0.5046487は初期の2組とCE3行の標本比較で、全複合loss/学習後の最適性ではない。係数探索はしない。

今後は実10000更新、0/200/1000/5000/selected/terminal fullstates、全loss/実counter/SHA、旧新168全文・新84全文の実読解、PyJS/raw比較を保存する。既知DEVで新TESTではなく、TRAIN64の7/57も両方TRAIN。公開モデル/サイト/R25anchorは維持。予定10000を完了扱いしない。

426入力を実更新0のcommit5b82cd7d81ddf83b7ab0088bd7c9508edc49bd42で凍結。実200更新では主target318964/bytes1106433とPython・Torch RNGが旧R44同時点に完全一致し、全重み/momentsはfinite。auxは20calls/40pairs、Adam20200。重み差は能力改善とはしない。初期checkpointはR28 model/Adam20000/RNGと一致、設定係数0.2を確認。初期snapshot作成前のread-only照合はFileNotFoundとなったが、作成後のwaiter照合はPASSし、訓練の再実行や追加optimizer更新はない。

学習中の容量対策として、同一Git blob/SHAの旧不変データ46ファイルの作業コピーをhardlinkで共有し約828MBの重複を減らした。内容・全パス・履歴を保持し、R44/R45のパスは置換せず、426入力SHAも再検証済み。execution/archived-data-hardlink-dedup.json参照。今後その共有データを編集する場合は先に独立コピーを作る。

実1000更新/Adam21000のfullstateも保存・finite監査済み。主target1592603/bytes5538546、Python・Torch RNGはR44同時点と完全一致、aux100calls/200pairs。会話DEV NLLは旧0.9388160688890173→新0.9386172212921948と微改善、共通DEVは旧0.970905335028921→新0.971037463800883と悪化。日常12全文の主意味成立0→1、長い反復5→4、EOS8→8。公園への二文の共感は厳しい雨への代案/反復解釈で0となり、この小標本の改善は頑健ではない。全文と全項目の読解・感度はexecution/paired-daily-generation-1000/に保存。新TESTでもselector評価でもなく、学習条件変更は0。

固定TRAIN64のpool内7件は正解NLL3.538245→3.494544、文脈利得0.170506→0.182538。他57件は3.522341→3.521201、利得0.085904→0.085979と小幅。7件はいずれもpool先頭0〜6で1000時点に一度ずつauxで学習済み。両区分ともTRAINであり、未見一般化や全体の意味改善を証明しない。総training lossは係数が変わるため直接の旧新改善指標にしない。
