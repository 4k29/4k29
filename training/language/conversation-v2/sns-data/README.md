# SNS・人間会話データ研究

[統合結果・Go/No-Go](REPORT.md) · [権利12ソース比較](rights/README.md) · [取得/再現手順](pipeline/README.md) · [全文品質監査](quality/REPORT.md) · [次期方針](research/STRATEGY.md)

ライブSNSの学習許諾は確認できず、投稿取得0。代替としてMRMPC960会話/100,680発話と、OASST2原版日本語788メッセージを取得した。権利・privacy隔離後の公開候補はMRMPC751会話/617,753独立本文tokens、OASST282枝/42,334独立本文tokens。**正式採用0、学習更新0、本学習No-Go。** 既存モデル・サイト・採用基準は変更しない。

`raw/` は公開用の最小化後パックであり全取得原文ではない。MRMPCの209会話は本文なしtombstone、OASSTの16tree/186メッセージは除外済み。隔離本文はGitに含めない。共有prefixを新規独立tokensへ加算しない。ライセンスが明確でも、人間執筆・意味的応答・個人情報不在が自動保証されるわけではない。

Python3.12標準ライブラリと既存自作BPEのみを使う。外部の学習済みTokenizer、LLM重み、生成APIは使用しない。取得再実行はpipelineの手順で権利再確認→取得→必須privacy処理→build。隔離前rawをcommitしない。公開元の削除/拒否/権利変更時は古いSHA復元より新しい権利条件を優先する。

リポジトリrootからの検証（ネットワーク不要）:

```sh
python training/language/conversation-v2/sns-data/verify.py
for suite in governance pipeline quality research; do
  python -m unittest discover -s "training/language/conversation-v2/sns-data/$suite" -p 'test_*.py' -v
done
```

28契約テスト、全公開本文のBPE byte復元、全960元ファイルのGit blob一致、最終派生データのbyte一致再構築、別担当の全件構造/BPE監査、既存RP/公開DEVとの重複検査を実行。MANIFEST.jsonで成果物SHAを固定する。モデル学習・中断再開・新しい日本語生成能力を検証した結果ではない。

`.github/workflows/sns-data-audit.yml` でオフライン契約テストと固定成果物検証を実行する。既存公開サイトCIも維持する。
