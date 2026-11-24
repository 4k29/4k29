# 独立した全文評価の手順

読者へはこの文書、`EVALUATION_RUBRIC.json`、`blind-pack.json`だけを渡す。`blind-key.json`、endpointディレクトリ、NLL、訓練曲線、他の読者の判断を読まない。全件を最後まで読む。似た出力でも各入力との対応を確認し、文面の重複を理由に読み飛ばさない。

評価対象は人間A/Bの会話継続である。人間の話者として新しい好みや私生活を述べることを、直ちにAIの虚偽自己申告とは判定しない。一方で入力履歴と矛盾する内容、指定された対象や質問に答えていない内容は失敗とする。参照回答との字面一致を要求しない。

## single項目

各blindIdについて次をtrue/false/null（nullは不確実）で記録する。各項目に簡潔な日本語の理由を添える。

- `grammaticalNaturalWhole`：文法・語順・活用が全文で自然か。
- `semanticAppropriateWhole`：直前の発話への適切な意味的接続が全文を通して成立するか。
- `specificContentAppropriate`：文脈に適切な具体的情報、理由、提案、明確な回答があるか。相槌だけならfalse。内容必須問題ではminimumSemanticRequirementを満たすかも確認する。
- `contextConsistent`：履歴の話題・対象・既出情報と整合するか。
- `genericOnly`：内容のない相槌や汎用的定型表現に終わるか。
- `harmfulRepetition`：意味を損なう反復があるか。
- `topicDrift`：無関係な話題へ移るか。
- `naturalTermination`：実際のEOSがあり、内容と文の終わりとして適切か。短いEOSのみを内容成功としない。
- `compositeWhole`：文法・文脈・意味・終了が成立し有害反復/逸脱がないか。contentRequired=trueの問題はspecificContentAppropriate=trueも必須。それ以外では文脈上相槌が適切ならcomposite成功を許すが、内容成功とは別集計する。

## selfplay項目

kind=selfplayは初期の人間原文履歴から、自分の無修正出力を履歴に加えた最大3発話である。episode全体を読み、`meaningfulWholeEpisode`、`contextConsistentWholeEpisode`、`harmfulCrossTurnRepetition`、`allTurnsNatural`をtrue/false/nullで記録する。同じ相槌の繰返しを一発話ごとの文法の良さだけで合格させない。人間との対話成功とは別の自己継続ストレス評価である。

成果はJSON `rows`配列とし、全blindIdを一度ずつ含める。読んだ総件数、未読/判定不能、読者が見た資料、独立性と限界も記録する。別読者と議論せず先に判断を固定する。assistantの評価は日本語母語話者の独立した人間2名による正式評価を達成したとは主張しない。
