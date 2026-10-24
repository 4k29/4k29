# R42 — auxiliary pool eligibility only

実更新0、監査中。3漢字必須条件のみ撤廃し、元の2漢字候補1616組のSHA順先頭256を選択。候補SHAとR41旧256組の完全再構築を検証した。正例文書190、元poolと同じ正例30、TRAIN診断64との同一発話7。64組は未見評価ではなく7/57を分けて記録する。先頭16正例を全文読解、全256を原典/token/境界・勾配で機械検証。全正例の意味監査済みとはしない。

モデル・own BPE/main40/30/30・source25/5・CE/係数0.1/every10/batch2・初期R28model/Adam20000/RNG・実10000dose・selector・全gateを保持する一条件比較。全10 core learning filesがR41と同じbytes。自然な日本語の改善は未測定。公開/R25anchor維持。
