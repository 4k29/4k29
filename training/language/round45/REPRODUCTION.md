# R45の復元と実施範囲

実10000更新は完了済み。開始前commit5b82cd7d81ddf83b7ab0088bd7c9508edc49bd42で426入力を実更新0に凍結。policy.json/source-manifest.jsonに条件と全data/code SHA、execution/launch.jsonにUTC/command、run.shに固定CLIを保存。R44最終CI証拠もcontrol-final-ci.jsonに固定した。

保存成果の照合はrepo rootから次を実行する。

```bash
python training/language/round45/execution/verify_final_artifacts.py --require-tracked
```

raw checkpointやtrain.tokens.binがない場合は隣接*.chunks.jsonと各part/結合SHAを確認してlossless復元する。初期0/Adam20000、実200/20200、1000/21000、5000/25000、selected9500/29500、latest10000/30000の6 fullstatesを保存。selected-weights.pt/model.jsは比較用で今回不採用。R25anchor/publicへ置換していない。再開時にselected重みとlatest optimizerを混ぜない。

既存完了runを再訓練しない。再現学習が必要なら別clone/出力で成果を保護し、426入力SHAと初期R28 latest full model/Adam20000/RNG、全初期DEV一致を確認して固定CLIを使う。部分runのみ同一条件resumeとし、予定値でなくstep/Adam/traceで照合。R45は環境再接続でもtrainerが継続し、訓練再実行・余分なoptimizer更新0だった。

全10 core filesはR44とbytes同一、学習差はcontextPreference.coefficient0.1→0.2のみ。静的実行ファイル/mjsを含む事前検証、43契約、全行境界/mask、初期勾配/DEV/fullstateはexecutionの各preflightとログに保存。初期checkpoint作成前のread-only FileNotFoundはpostlaunch_initial_audit.pyの作成待ちで解決し学習に影響しなかった。

原典cacheは/workspace/daily-conversation-source-audit/human-only-raw。資料/取得commit/利用条件/speaker train-dev-test splitはR44と同じ固定資料。新しい原典の意味読解はしておらず、同一SHAの過去履歴の再利用と全source/token検証を区別。reserved TESTへモデル/tokenizerを適用せず、外部重み/tokenizer/生成API/教師生成正例/回答修正を使用しない。

reading-notes-as-executed.jsonとrecord_final_readings_as_executed.pyは実際に読んだ今回の生成SHA専用binderで、未来の出力の自動意味graderではない。同一全文/初文・今回1kの主判定も照合する。再計算は別出力へ保存し既存の生成/読解を不用意に上書きしない。全168無修正全文はALL_FOUR_STATE_GENERATIONS.md、token IDsは各generation JSON。数値範囲はfinal-numerical-verification.json、既知R10near-tie16/17を保持。

loss CSVはinstantaneous-training-loss-curve.csv/context-auxiliary-curve.csv/paired-ce-curve.csv。係数が異なる総training lossを旧新で直接比較しない。前二者はminibatch/aux2組の標本で全TRAIN平均ではない。TRAIN99/DEV99は非matched、TRAIN64の7/57も両方TRAIN。sampling-coverage-5000/10000.jsonはposthocの抽選使用量で、未抽選行=未見文でも追加dose有効の証明でもない。

容量確保のR43旧raw6状態はtracked lossless partsから完全復元可能。旧不変データ46コピーのhardlink共有では内容/全パス/履歴と426SHAを保持しR44/R45パスは置換しなかった。共有データを編集する際は先に独立copy/atomic replaceを行う。sparse旧prepared93filesの扱いと詳細はWORKSPACE_STORAGE.mdと各storage JSON。Git履歴や一意な状態は削除していない。
