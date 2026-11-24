# Modern Japanese foundation-data candidate

GOAL.mdとconversation-v2/epoch1の結果を引き継ぐ、**データ・評価・学習前検証専用**の隔離作業。

- [報告・実量・Go/No-Go](REPORT.md)
- [原典と利用条件](SOURCES.md)、[資料別license](DATA-LICENSE.md)
- [パイプライン再現手順](pipeline/README.md)
- [評価契約と不足](evaluation/README.md)
- [次期設計/継続対新規/資源](research/RESOURCE_PLAN.md)

`archives/`は固定原典、`corpus/`は全原文/派生/NFC/hash/QA/splitを含むgzip候補。全23,351,258段落本文tokens、TRAIN候補20,262,193tokens。全資料はcandidate-not-admittedで、**全gzipをそのまま学習へ渡してはいけない**。新しい生成文章・モデル学習・Tokenizer fitはない。人手QAとCodexの入力案、DEVとpipeline-visible reserveを区別する。reserveは封印TESTではない。

元の原典と公式checksum、SHA、source-specific termsは保持している。raw Wiki XMLからの抽出はmwparserfromhell0.7.2（MIT、wheel SHA固定）。一時導入先は `/dev/shm/foundation-parser` で、既存環境/公開コードを変更しない。原典replayは `sources/replay_acquisition.py`、パース/正規化/dedup/splitは `pipeline/`。ネットワーク先が消えてもGit中のraw archivesを再利用できる。

実行時manifestには `/dev/shm/foundation-data-source` 等の絶対pathがある。新しい環境では保存済みrawを当該layoutへ戻すか、manifestのpathだけを別runとして明示変換し、全payload SHAが一致することを確認する。pathを変えたmanifest SHAを元runと同じとは記録しない。

`corpus/documents.jsonl.gz` の `keepForCandidateTraining` は重複処理上の候補flagで、license/人間原文/品質のadmissionではない。本文空のTRAIN82文書は入力例から除外する。全原文を保持するため、採用対象外の重複や保留payloadもarchive内にある。

`research/matched-schedule/`は本文/EOS/role dose・PADを照合した未認可の参照schedule。2048step/arm、同じ1,735,859targets/arm、真のnative EOS777。これは実学習済み回数ではない。実際はゼロ更新監査の4Fwd/Bwdのみで、モデル/Adam/RNG不変。PREFLIGHTの事前固定commitは5f0cd2b。次の学習計画はtrainingAuthorized=false。

検証：`python verify_foundation.py`（本ディレクトリから）で保存archive・30shard・最終split・BPE量・評価固定SHA・ゼロ更新・scheduleを確認する。`pipeline/test_pipeline.py` 7件、`evaluation/test_benchmark.py` 6件、`research/`内の契約テスト計9件を実行済み。全2048scheduleの独立token/PAD/EOS照合も実行した。正式な人間会話TESTや新モデルの能力改善を証明するものではない。

公開モデルの置換、旧評価の変更、有料GPU、大規模本学習、マージは行っていない。
