# 再現と原文の隔離

この研究は学習開始No-Go。optimizer呼出し・モデルforward・新checkpointはすべて0。原文とtoken列を公開Gitに保存しない。

## 公開成果物だけの検証

`python unpack_metadata.py`、`python verify_evidence.py`、`python test_study.py`を実行する。テストは標準ライブラリと既存の独自Tokenizerのみを用い、原文取得もモデル構築も行わない。CIでは会話v2の場所を`CE_V2_ROOT`に指定する。

圧縮パックの中身はID、family、SHA、件数、審査フラグ等のメタデータのみ。原文、返答本文、学習token列、モデル重みは入れていない。gzip/base64を本文再配布の回避手段として使っていない。

## 一時隔離での再取得・監査

原配布元の条件を確認した非商用のローカル調査に限り、`python acquire.py --quarantine-only`で固定revision/SHAのファイルをPRIVATE/へ取得できる。この操作は学習利用や公開再配布の許可を与えない。いちからの原配布申請・受領は代行しておらず、鏡像と原配布物の一致も未確認。原配布元の申請経路と出典はSOURCE_REGISTRY.jsonに保存した。

`CE_V2_ROOT=/path/to/repo/training/language/conversation-v2`を設定し、以下の順で実行する。

先に公開メタデータを`unpack_metadata.py`で展開する。凍結したfamily/分割を再生成せず、再計算した連結成分と既存割当の同一性を検証する。

1. `build_candidates.py`：strictなレコード単位解析、重複除去、質問family分割、独自BPE/context監査。無効JSONレコードを修復しない。
2. `select_review.py`：固定seed/層別/一family一件で107件を選択する。PRIVATE/REVIEW_CARDS.jsonは原文を含むため公開しない。
3. `annotate_review.py`：保存済みの主エージェント読解判定を再適用する。意味品質を自動的に認定する分類器ではない。
4. `audit_overlap.py`と`audit_split_near.py`：既存TRAIN参照と新TRAIN/DEVの語彙的近重複を照合する。対象は明示されたTRAIN参照ファイルのみで、封印TESTを開かない。
5. `build_dev.py`：選択済みDEVの必要情報・判定根拠をPRIVATE/DEV_DRAFT.jsonへ固定し、公開可能なSHA/設計だけDEV_DESIGN.jsonへ出す。

PRIVATE/は作業環境のRAM上の一時隔離であり、永続保存先ではない。環境消失後の原文維持は保証しない。取得先revisionとSHAによる再取得手順を残すが、公開Gitへの原文保存で代替しない。

## 学習を開始しない条件

いちからの原申請フォームにモデル公開禁止の追加記載があり、利用できる非公開の永続保存先がないことも確認した。公開repositoryのActions artifactを非公開ストレージとみなさない。instruction_jaはMITの著作権表示をTHIRD_PARTY_NOTICES.txtに保持するが、人間執筆の日本語原文とは呼ばず、上流モデル回答→機械翻訳→人手修正の資料として管理する。上流TEST参照117件は候補から外した。

PR112の実モデル検証・完全復旧実績は引き継ぐが、本研究で再実行した証拠とは数えない。新しい訓練runnerや学習GOは用意していない。既存の正式モデル、サイト、過去の研究、checkpoint、厳格ゲートを変更しない。
