# DEV資料の監査

PR #128の固定18件、追加7件、caption32件は回帰診断として維持。新規評価の採点には使っていない。PR #128で隔離したWikivoyage「狭山市」版59491の一段落は別枠の既存隔離診断として保持した。

- `novel-continuous-study/NEW_PROSE_DEV.json` の6件と `foundation-absorption-study/PROSE_DEV.json` の12件は固定18件に含まれる。
- `foundation-stage/prose-dev.json` の12記事・24プロンプトは旧研究の露出済み探索DEVとして明記されている。今回指定の独立セットとして採用するには対象時点までのTRAINとの再照合、版・ライセンスの行別確認、第一文境界の再設定が必要であり、今回の学習不成立を受け評価を凍結しなかった。
- 目標10〜20件の新規DEVは未達。今回の追加推論にDEVや封印TESTを使わなかった。
