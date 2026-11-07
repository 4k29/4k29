# caption-mix-v1：研究用基盤学習

未学習familyの短文から段落まで意味の通る日本語を生成できるかを測る。新しいcaptionは自然な短文の材料であり、画像理解・質問回答・複数ターンの教師ではない。

- `MIX_POLICY.json` / `DATASET_AUDIT.json` / `REBUILD_PROOF.json`: 実データ、配分、原文位置と再構築。
- `INITIAL_REFERENCES.json`: PR104終端の自作A/B重み、共有するRNG、過去の更新数。Adamは両者新規。
- `EXPERIMENT_PROTOCOL.json`: 未実行の旧案との差、比較/一巡予算、段落を重視した系列選択、停止条件。
- `EVALUATION.json`: 閲覧済み診断。新caption32件、MAFF12件、従来の原文評価とTRAIN診断。source誤字1件の隔離・置換は新出力を見る前に記録。
- `preflight.py`: モデル数値、可変paddingの同値性、勾配、資源。0更新検査。
- `train.py`: 初回4更新の後に別processで2→4を完全再現し、検証用追加2更新と保持更新を分ける。その後も全状態をatomic保存。
- `evaluate.py` / `panels.py` / `context.py` / `parity.py`: 固定生成、従来内容評価、文脈診断、限定Python/JS数値照合。元の公開/学習コードへ書かない。

本文・role・EOSを保持する。短文は行ごとに独立し、異なる文書を結合しない。可変paddingは旧256固定batchと乱数消費形状が異なるため、PR104との差をデータだけの因果証拠と呼ばない。本実験のA/Bではdata・形状・RNG・optimizer・予算が共通である。

実行した更新だけを記録する。数値preflightと初回再開検証が通るまで大きな学習へ進まない。正式採用、公開置換、マージ、有料資源、封印TESTは対象外。自然な短い補完だけでPhase1や内容応答の達成としない。
