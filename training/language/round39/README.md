# Round39 — 実10,000更新完了、会話NLLは改善・全文意味は未改善

R38と同じデータ・model・全目的・LR・seed・doseから、人間会話の抽出確率だけをRealPersona25%+JMRD5%（合計30%）へ変更した。実更新10,000、選択9,000/Adam29,000、最終10,000/Adam30,000。初期・200・1000・5000・選択・最終の整合model/optimizer/RNGを保存。

人間会話DEV NLLは **0.940388→0.934594**、選択の日常12の長期loopは6→4。しかし全文意味は **0/12** のまま、従来17の全文意味も1→0、共通DEV NLLも0.965013→0.965277と悪化。最終状態の日常loopは逆に4→6。新84全文を実読解し、Py/JSとraw/exportの全文一致は84/84。厳格/固定人間NLLゲートは不合格で**不採用**。R25研究anchor・公開モデル/サイトは変更していない。

- [結果・失敗分析・限界](RESULTS.md)
- [全168旧新・選択/最終の未加工全文](execution/ALL_FOUR_STATE_GENERATIONS.md)
- [最終判定](execution/final-assessment.json) / [数値一致](execution/final-numerical-verification.json)
- [再現手順](REPRODUCTION.md) / [全成果SHA](execution/artifact-manifest.json)
- [次の単一条件候補（未実行）](NEXT_EXPERIMENT.md)

全て露出済みDEVで、新TEST一般化の証明ではない。source5は1cast/3公開話者、DEV99に1組の重複がある。operatorの既存ポリシー表示範囲はRESULTS/inspection-scopeに記録し、実験モデルへのTEST入力・学習・採点とは区別する。途中mechanicalのpendingは当時のsnapshot、最終判定は上記JSONを正とする。
