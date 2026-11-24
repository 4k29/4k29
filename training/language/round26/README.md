# Round26 — 人間原文コーパス混合率0→10%だけ

科学的対照は実10000更新を完了したR25。R25は最良CE NLL0.9714220852387883、初文8/17・非長期ループ4/17・全文意味0/17。反復を負例にするだけでは主述・文間の意味が回復しなかったため、自然な説明文の分布不足を原文追加だけで検証する。

唯一の学習要因変更はwiki2019コーパスのmass0→0.1。既存8ジャンルをそれぞれ0.9倍し相対比を保つ。モデル8層dim192/hidden768/context256/5455独自語彙、独自BPE40/30/30、CE+teacherUL1.0とsequenceUL0.1every10、LR2.2499999999999998e-5、seed系譜2049、batch8/CPU2FP32、10000実更新/500更新CE検証を固定。訓練に使う6つのcoreファイルはR25とbyte同一。

同じRound11 latest整合model/AdamW/Torch/private Python RNGから開始する兄弟対照で、R25selected weightsにlatest momentsを混ぜない。R25から累積して更新した系譜とは記録しない。コーパス変更で実target数・padding bucket・sampler/dropout消費が変わるため、対照と最終exposure/RNGが等しいとは主張せず、各runを独立再生して監査する。

原文は../round24/next-candidate-drafts/wiki-addition/source-cache/quality-sources。153固定項目から2019以前の公開Wikipedia版を取得し、115TRAIN文書528単位307885文字を採用、16文書予約。canonical pageIDによるfold、raw版・履歴・contributors帰属・CC BY-SA3.0/4.0と後続版互換条項・現行規約を保存。機械翻訳標識、非公開本文、数式依存/空見出し等を補作せず除外。pre2020 community原文であり全入力方法を独立認証したものではない。以前のDEV失敗が広いコーパス族の動機で、各項目の採否をモデル得点で選別していない。

既存非TRAIN627文書・既存TRAIN・予約・新内部との64文字literal重複を監査し1単位除外。近似/短い重複不在は保証しない。raw TESTは重複監査のみでloss/生成/encodeに使わない。source-manifest.jsonにraw・ライセンス・抽出/prepareコードとデータSHAを結合する。抽出原文を書き換えて正解を補う処理や外部生成AIを使わない。

prepared dataは全旧TRAIN rows/documents/token prefix、validation、tokenizerを保持。追加1584viewsは原文UTF8一致とmasked target-onceを全件検証。旧原文の段落化・分割方式は変更しない。prepare_addition.pyで同じ旧dataから再生成可能。新528単位のTRAIN損失はpost-selection診断として分け、未見能力の証明には使わない。

実行 `bash training/language/round26/execution/run.sh`。未完了・非稼働時だけ`--resume`、同一identityのmodel/optimizer/RNG/rollout countersを復元。最新checkpointとselected weightsを別保存。チャットから独立したpersistent controllerが訓練・全機械検証・PR保存を行う。途中windowへ合成BOSを追加せず、真の先頭min32tokensをsequence負例生成に使う。生成tokenをCE正解にしない。

最小CE DEV NLLでstep選択、事前閾値0.9714220852387883。17書き出しは既存DEVで新TESTではない。旧新greedy full vocabulary/max192/trueEOS/Python1thread、全token/無加工全文保存、従来の全scope/group厳格ゲート不変。全文をassistantが読み独立盲検ではない。推論penalty/文章修正/検索/テンプレートなし。公開モデル/サイト変更なし。容量の比較は別R27で行う。

実10000更新完了。Wiki混合は初文回帰のため不採用。日常会話を含む実測と次の対照は[RESULTS.md](RESULTS.md)を参照。
