# 全token CE / 返答部分CE：データ審査とmask契約

今回の成果は、原文280返答の個別審査と、同じ入力からA/B教師位置を作る準備・テスト。**実学習はNo-Go、optimizer0、モデルforward0、モデル生成0。**

- REPORT.md / TABLES.md：実数、判断、限界、未実施事項
- PRE_AUDIT_PROTOCOL.json：冒頭TRAIN192/DEV24の固定条件
- SUPPLEMENT_PROTOCOL.json / SUPPLEMENT_SELECTION.json：後半TRAIN64の予測前固定
- REVIEW.json / SUPPLEMENT_REVIEW.json：全原文読解の個別判定（単独assistant非盲検）
- CANDIDATE_SPANS.json：条件付きTRAIN196/DEV19のみ。入出力token・元文書位置・A/B mask・出典/帰属を保持。実更新の採用許可はfalse
- PREPARATION_SCHEDULE.json：一巡49batchの非実行準備、保持更新0。学習済みscheduleではない
- DATA_SUMMARY.json / CONTRIBUTIONS.json：学習したtargetsではなく準備した教師位置数
- SOURCE_INTEGRITY.json：既存3入力のpinned Git blob / SHA256照合
- LEAKAGE_AUDIT.json：既存TRAIN全体との照合。意味familyの独立性の完全証明ではない
- masks.py / test_masks.py：mask・teacher shift・padding・合成logitsの勾配検査。**実モデルの勾配・Attention・Adam・再開検証は未実施**

RealPersonaの人間A/B role3/4をassistant/userへ変更していない。参照回答は人間の一例であって、AIの経歴・事実・唯一の正解ではない。条件付き候補にも独立した母語話者評価はない。

## 再現

元データは新規取得せず、PR110 pinned commit10684c367bab44ed6f02133251d95984bfbe1bb3の既存data/を使う。Source SHAはSELECTION_METADATA/SOURCE_INTEGRITYを照合。審査候補の本文・可逆tokenを含むprivate中間物はGitへ追加しない。

空きのある**非公開の作業ディレクトリ**に、当フォルダの*.py、PRE_AUDIT_PROTOCOL.json、SUPPLEMENT_PROTOCOL.jsonをコピーする。出力はscript配置先に書かれる。CE_V2_ROOTを元conversation-v2の絶対pathへ設定し、次の順序で実行する。

```sh
python -B audit_data.py
python -B review_labels.py
python -B audit_supplement.py
python -B review_supplement.py
python -B finalize_audit.py
python -B leakage_audit.py
python -B contributions.py
python -B -m unittest discover -s . -p test_masks.py
```

review_*.pyは保存したメインassistantの判定を再適用するもので、新しい人間評価・自動意味判定ではない。既存公開artifactだけのテストには再取得・private中間物・学習は不要。

```sh
python -B -m unittest discover -s training/language/conversation-v2/response-ce-study -p test_masks.py
```

合成logits検査だけPyTorchが必要。学習済み外部モデル/Tokenizer、生成APIは使わない。源資料のCC BY-SA4帰属・原典SHA・既存の撤回/除外方針を継承し、独自の包括的な再利用許諾へ置換しない。保留44TRAIN/4DEVの本文・tokenは新しい公開パックに含めていない。新規コーパス取得、封印TEST、公開モデル/サイト変更、マージなし。

## 大きい監査JSONの保存形式

CANDIDATE_SPANS/REVIEW/SELECTION_METADATA/SUPPLEMENT_REVIEWは、gzip＋base64でlossless保存している。PACKED_INDEX.jsonに元UTF-8 byte数と元/gzipのSHA256を保存した。元のJSON名は論理ファイル名。テスト前に次を一度実行する。異なる既存証拠を上書きしない。

```sh
python -B training/language/conversation-v2/response-ce-study/unpack_results.py
```

展開後の同名JSONはGitignore対象。保留本文を含むLOCAL_*と全選択tokenのprivate中間物SELECTION.jsonも公開対象外。
