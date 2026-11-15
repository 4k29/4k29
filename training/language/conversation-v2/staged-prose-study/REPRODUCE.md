# 再現と再開

既存ブランチPR117の成果物を維持した状態で、この研究フォルダを追加する。外部モデル、Torch、ネットワーク、新規取得は不要。

```sh
python training/language/conversation-v2/staged-prose-study/prepare.py
python -m unittest discover -s training/language/conversation-v2/staged-prose-study -p 'test_*.py' -v
```

prepareは公開済みの追加55本文と旧12本文、PR116の固定コーパス/scheduleのみから同予算準備を再作成する。未採用private poolがある場合だけ追加55件のID/token一致も検査する。private本文全量を公開する必要はない。

追加選択自体は `READING.json` のID・本文SHA・採否を使用し、既存取得キャッシュ内の同一IDを照合する。人手判断をコードで自動再現できたとは呼ばない。既存抽出・段落境界・近重複検査はPR117のコードと固定SHAを再利用する。

学習は未実行。PLAN.training_GO=falseを保つ。新しい研究条件を固定し数値・容量・完全state復元を検証する前にoptimizerを呼ばない。再開時に過去の実行済み更新を探す必要はなく、実ledgerは0。新しいモデルcheckpointはない。
