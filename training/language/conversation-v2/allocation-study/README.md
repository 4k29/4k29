# 既存TRAINの再配分研究

[結果と開始判断](REPORT.md) / [固定実験条件](EXPERIMENT.json) / [最終集計](SUMMARY.json)。状態変更の実行許可はfalse、正式採用・本学習No-Go。

リポジトリroot、オフライン検証:

```sh
python training/language/conversation-v2/allocation-study/verify.py
python -m unittest discover -s training/language/conversation-v2/allocation-study -p 'test_*.py' -v
```

`prepare.py` は既存TRAINのSHAを確認してscheduleを再構成し、少量のatomic書込を試験する。`numerical_audit.py` はPyTorchと既存完全checkpoint（sparse省略部分はGitからSHA付き復元）を用い、更新禁止で4バッチの勾配確認と実checkpoint2世代保存・復旧を行う。後者には約272MBの一時保存余裕が必要。環境依存の資源測定値や所要時間は変わるため、既存結果へ無断上書きせず別checkoutで再実行する。

`run_comparison.py` は現計画のgateで終了し、更新もoutput作成もしない。状態変更後の再開・ledger・言語評価が未検証であり、自己判断で許可flagを変えて実行しない。14更新/armは実行数ではなく条件付きscheduleの規模。旧案と現案の勾配監査計8バッチ、optimizer更新計0。

原文標本の新しい転載はせずID/SHA/抽象理由を保存した。RPは既存CC BY-SA4、JMultiWOZは元response-data/sourcesの固定版とlicenseを継承。40会話読解済みでもDB事実の裏付けは保留。旧23DEVと全件隔離は不変。モデル能力向上・独立人間評価を達成したと主張しない。
