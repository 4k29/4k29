# 再現・復旧

PLANは学習前commit64997fb4e111eb21fcbe256034ea3b8ecb19ac71、実行開始は3216cb6119e75e13f37ca1c73c7862f2a8d35711。完了実行receiptはrun43968663506、保持更新を再実行しない。RUN_GOやworkflow再試行で同じ研究を自動継続しない。

```sh
python training/language/conversation-v2/gv-prose-pilot/verify_data.py
python training/language/conversation-v2/gv-prose-pilot/analyze.py
python training/language/conversation-v2/gv-prose-pilot/score.py
python -m unittest discover -s training/language/conversation-v2/gv-prose-pilot -p 'test_*.py' -v
```

分析は保存済みJSON/JSONLだけを読み、model forward/optimizer0。score.pyは保存した個別判定を再集計するもので、意味評価を機械的に再証明するものではない。初期caption判断は旧PR108の同一生成と同じ基準を引き継ぐ。

完全stateは `artifacts/{B,C}-{4,7,14}/checkpoint.json` と同ディレクトリの分割片。初期MIX-579のmanifestとsourceSHAはCHECKPOINT_INDEXに記載。既存 `foundation-stage/runtime.py` の `loader.load_checkpoint(manifest, expected_sha)` が部分SHA/全SHAを検証し、sparse環境では同じcommitの `git show` から復元する。Torch2.14.1+cpu/NumPy2.3.5で読み、全state digest・cursor・Adam step・PLAN SHAをreceiptと照合する。新学習や自動replayは行わない。

Git-only検証は実行時に6保存点すべてで実施済み。第三者を含む原英語HTML全量は公開せず、SOURCE_RECEIPTSのURL/本文SHA/取得時刻で照合する。判定済み日本語本文・帰属だけをコーパスへ含めた。封印TESTは不要。
