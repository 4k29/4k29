# conversation-v2

GOAL.mdに向け、自然な日本語と日常会話を優先する独立モデル系列。既存roundを置換せず、データ/Tokenizer/境界の基盤を再設計し、新系列内では幅だけを比較した。実験済み範囲と未実施計画を区別する。

- [方針と段階計画](STRATEGY.md)
- [今回の結果](RESULTS.md)
- [データ戦略と利用条件](DATA_STRATEGY.md)
- [モデル・計算資源](resource-comparison.json)、[独立モデル分析](model-research.md)
- [評価設計](evaluation-design.md)、[事前固定設定](PLAN.json)

## 実際に完了したこと

原典監査、新TRAIN/DEV話者分割、TRAINのみで新独自BPEを学習、PAD/EOS/文書境界監査、2モデルのゼロ更新勾配/資源監査、各512保持更新＋2再開replay、固定DEV評価、独立assistant全文評価、限定Python/JS数値一致およびTokenizer531入力一致。公開モデル/サイト/既存訓練推論コードは不変更、マージなし。

`pilot/{small,medium}/checkpoint.pt.chunks.json`は終端512の完全state（model/Adam/RNG/sampler/order/history）。`weights-256.pt.chunks.json`は未使用の事前固定資源milestoneのmodel-onlyで、resume用ではない。今回は両512完了なのでterminal=比較endpoint512。正式な採用重みではない。

実optimizer.stepは1028、保持更新は各512、replayは各2。旧64組診断の400とは別の新タスク予算である。学習時間568.77秒、各retained415321target positions、同じ2048窓を一回ずつ、約0.148window epoch。予定512を実数に置き換えて記録するような処理はしていない。

## 再現

最終PLAN SHA256：`c457f7510965e7dbe72475eb4b93c2441b6d9a541bdf7ed26db4c79714f6aaa8`。
新データmanifest SHA256：`93580cdc994d09816306e529a4ec76a90a6b6771e346358b4a9dd12c72b126c1`。
Tokenizer SHA256：`6d079e4ba0a954ae32ad34a35ddd15384eb48b8eceaf3f3529a66e4266b1da06`。

必要環境はPython3.12.14、PyTorch2.14.1+cpu、NumPy、CPU2thread、FP32。実環境はenvironment.json。別hardware/softwareでbitwise一致を無条件に保証しない。外部の重み/Tokenizer/APIは不要。

**評価の再実行**は、まず次の既存lossless helperで使うstateだけを復元する（再学習しない）。

```sh
python training/language/round46/checkpoint_chunks.py restore training/language/conversation-v2/pilot/medium/checkpoint.pt.chunks.json
```

次に`evaluate.py --plan PLAN --plan-sha256 SHA --model medium --checkpoint RESTORED --checkpoint-sha256 SHA --expected-updates 512 --output NEW_DIRECTORY`。各パスはrepository相対、出力はconversation-v2内の**新規**ディレクトリ。正確なstate SHAはcheckpoint-archives.json、コマンド実装はrun_pilot.py/evaluate.py。既存結果を上書きしない。

**学習全体の再実行**は、原成果物を保持した別checkoutで事前登録commit `ab557f2`を使う。このcommitにはデータ/Tokenizer/評価入力とコードがあり、学習ledger/launch/終端stateはまだない。十分な作業領域と新しい計算予算を確保した場合だけ`python training/language/conversation-v2/run_pilot.py`で再実行する。元の現在作業ディレクトリではlaunch receiptが重複実行を拒否する。今回の1028実更新予算は消費済みであり、再現手順は追加学習の自動許可ではない。

**データ生成全体の再実行**には既存の原典RealPersona TRAIN cacheも必要。原典8975のID/SHAはdata/split.json、URL/pinned commit/licenseは各docs.jsonlとATTRIBUTION.md。build_data.pyは現成果物を上書きしない。既存TOKENIZERを継承せずsplit→新fitの順に実行する。原文/発話内改行/ordinal/話者を保持し、NFKCは重複family検査だけで本文を書き換えない。

## 検証

```sh
python training/language/conversation-v2/verify.py --sources --manifest --tracked
```

原典cacheのないmachineでは`--sources`を外して保存artifactとfrozen code/dataを確認できる。raw checkpointの再構築を行わずchunk SHAを検証する。manifestは自己参照を避け、manifest自身と最終verification.jsonを除く。dataset原典/全窓の詳細監査はaudit_integrity.pyとintegrity.json、tokenizer fit/sample/leak監査はdata/内のreceipts参照。

preflight初回のmediumは標準FP32 gradient-norm集約の誤差で停止した。許容差は緩和せず、新系列両方のclippingをFP64 global-norm→同一係数のFP32勾配へ統一し、再検証した。初回ログ・旧code SHA・clipping-correction.jsonを保存。旧productionコードのclippingを変更したわけではない。

Python/JS model数値検証は先頭3prefix/各最大4tokenだけ。全192生成の全面一致・新UIの動作保証ではない。Tokenizer検証はencodeのみ。旧prompt APIのNFKC/lowercase/turn5形式をそのままv2へ適用できるとは検証していない。R10等の既知near-tie分岐報告は隠さず維持する。

## 次段階の予算境界

現在512用cosine scheduleは既にminLR3e-5で終了している。`uniqueUpdates`だけ増やすとLRが跳ねるため、「同設定の継続」ではない。次に一通りの原典coverageを得るなら、別stageでterminal Adam/RNG/orderを継承し、terminal LR維持などを事前固定する。現在予算を延長しない。

`next_stage/rebase_roles.py`は人間A/Bの切出しprefixを最初のrole3へ一貫して対応させる**未使用**helper。全32原典でbody/EOS保持を含む3テストを通したが、本pilotのmodel推論や採点には適用していない。意味を持つuser/AI roleを交換するAPIではない。新契約で比較する場合は現512と将来endpointの両方を同じ契約で評価し、過去の点数を書き換えない。

両モデルの最初の1epoch完了は残り学習約54分＋評価、60–90分程度の別CPU予算と保存headroomを見込む。最終batchで次epochを混ぜないなら2窓の小batchを明示する必要がある。1epochでも約282万targetsで十分な基盤学習とは呼ばない。数億tokensの基盤学習には適法な現代日本語原文の拡充、GPU実機計測と保存領域を先に確保する。今回、GPU/有料資源/追加の次実験は開始していない。

現在のtrainerはCPU reference。CUDA/AMP・大規模sharded前処理・native長contextの本学習は未実装/未検証であり、GPUを用意するだけでこのpilotをそのまま本学習へ進められると保証しない。
