# Round39 再現・復元

この保存済みrunは実10,000更新を完了している。再開・再実行して上書きしない。最良は9,000、最終は10,000で別の整合状態。選択modelに最終optimizerを混ぜない。

## 成果の検証・復元

リポジトリrootから：

```bash
python training/language/round39/execution/verify_final_artifacts.py --require-tracked
```

全ファイル/入力SHA・サイズ・追跡可能性、chunk連結の完全なbyte一致、model/Adam/RNG/counterを検証する。必要なrawが欠けている場合は追跡済みpartsから復元するため、対応するサイズの空き領域を用意する。既存rawが異なる場合は上書きしない。個別の復元例：

```bash
python training/language/round39/checkpoint_chunks.py restore training/language/round39/continue-10000/checkpoint.pt.chunks.json
python training/language/round39/checkpoint_chunks.py restore training/language/round39/continue-10000/best-aligned-checkpoint.pt.chunks.json
```

| 状態 | 今回の実step | Adam counter | 役割 |
|---|---:|---:|---|
| checkpoint-0 | 0 | 20000 | R28の整合初期状態 |
| retained200 | 200 | 20200 | 実保存中間状態 |
| retained1000 | 1000 | 21000 | 実保存・途中診断 |
| retained5000 | 5000 | 25000 | 実保存・中間NLL比較 |
| best-aligned | 9000 | 29000 | 共通DEV選択、重み系譜68000 |
| checkpoint/latest | 10000 | 30000 | 最終、重み系譜69000 |

各full checkpointにmodel・beststate・moments・Torch RNG・private Python RNG・実step/historyが含まれる。NumPy RNGは訓練に使用しない。selected-weights.pt/model.jsは9,000の推論用であり、full再開状態の代替ではない。全chunk manifestとartifact-manifestに完全SHAがある。

## 固定条件と唯一の介入

抽出確率をRealPersona0.25 + JMRD0.05にした。human0.30/その他0.70、BPE0.40/0.30/0.30は維持。source/genre/view内の各rowは一様な周辺確率を持ち、length64/128/256を条件とするbatch相関は元の方式を使う。条件により正例履歴・長さ・最終RNGはR38と変化する。この実験自身のsampler/EOS再現が一致すべき対象で、旧最終RNGとの同一性を要求しない。test_source_sampling.py/check_sampling.pyとsampler-replay.jsonを参照。

学習train.pyとbatching.py以外の全coreはR38とbyte一致。batching.pyの冒頭やtrainer設定に残る「same marginal row probabilities」は元のbucket因数分解の説明であり、R38の全row確率を維持したという意味ではない。新しいsource条件の周辺確率はpolicy/batching/sampling-marginalsで明示される。

全データ・validation・tokenizer・true-end mapはR38のbyteを再利用した。新たな取得/再tokenize/語彙fit/役割ラベル挿入はない。source-policy.jsonからR38原文・CC-BY-SA attribution/取得・重複監査へ辿れる。JMRD upstream TRAINのみ、valid/testは新取得していない。短い/近似重複なし・新sourceのcross-source speaker非重複は保証しない。localでimmutable大入力をhardlinkして容量を節約したため、それらをin-placeで書き換えてはいけない。Gitからの新checkoutは同じbyteを通常ファイルとして復元できる。

初期化は同じR28 latest full model/Adam20,000/Torch/private Python RNG。独自8x192/head4/FFN768/context256/dropout0.1/vocab5455/4,655,808parameters、batch8、FP32/CPU2、deterministic、compileなし、seed系譜2049、LR2.2499999999999998e-5/wd0.05/clip1。EOS補助0.3・元newline主CE除外・元分母/gold保持、teacherUL1・自己負例UL0.1/10更新/64tokens、true-boundary negative prefix8..32を維持した。共通DEV0/every500の最小値のみで選択し、日常生成で選択しない。

実環境はPython3.12.14、PyTorch2.14.1+cpu、NumPy2.3.5、Linux6.18.55/x86_64。preflight-runtime.jsonに環境・勾配・親state一致、initial-development-preflight.jsonに全初期DEV0.9718989571266189一致を記録。開始前39契約と189,166行のprefix/mask監査を実行した。source-manifest.jsonは388入力SHAの開始前snapshotで、実更新0というfreeze時の記録を10,000へ書き換えない。

## 独立した新しい再現run

完成済み成果を保ち、別checkout/worktreeを使う。まず上記検証で全frozen inputをmaterialize/検証する。そのコピーだけのgenerated continue-10000、train.log、launch/monitor等の実行記録を退避する。元のrunや兄弟roundを削除しない。core/policy/source-manifest/凍結された入力とreceiptは変更しない。完成treeにfreeze_pretraining.pyを再実行して別の入力closureを作ってはいけない。

記録環境と同じ条件で、runtime/初期DEVの再検証後、別コピーで：

```bash
bash training/language/round39/execution/persistent.sh
```

controllerが学習・best全状態保存・監視・機械評価・PR保存を行う。history用のlaunch_as_executed.py/capture_milestones_as_executed.py/prepare_trial.pyは当時の実行記録で、絶対workspace pathを含む。完了成果の上でそのまま再実行しない。実際の再現では現在のコピーの相対run/persistent入口を使い、必要なら同じ200/1000/5000全状態captureをそのコピーで設定する。

未完了かつ稼働していない状態だけ `bash training/language/round39/execution/run.sh --resume` が許される。full model/Adam/RNGと保存stepを復元し、履歴を整合する。10,000完了はguardが拒否する。controller/training lockが重複workerを防ぐ。新規の独立再現は実際に10,000回stepを実行する。sampler replay・検証・復元は追加更新0。

SHAのbitexact保証は**保存済みpartsの復元**についてである。新たな物理的runのfull checkpointにはelapsedなどの実行metadataが異なるため、ファイルSHAまで同一とは主張しない。記録条件のtensor/生成/損失/trace/counterを比較し、hardware/kernel差は別途報告する。

## 評価の再確認

```bash
python training/language/round39/execution/read_full_group.py selected daily12 0 6
python training/language/round39/execution/read_full_group.py terminal original17 0 6
```

範囲を変えれば元17/日常12/native8/source5の全prefix/全文を表示する。実読解は各SHA-pinned *_as_executed.pyとmanual/readingsに記録。これらは保存済みの判断を検証する記録で、新モデルの自動採点器ではない。confirm_all_new_readings.pyは84新state出力/77prefix全文組の対応と同一出力の判断を、verify_first_sentence_consistency.pyは同一初文の成分点を検証する。assemble_raw_four_states.pyは168全文と旧raw identityを束縛し、意味を採点しない。verify_final_numerics.pyが84全列Py/JS/raw-exportとreference誤差・旧R10既知分岐を検証する。

greedy192/full vocabulary、Python1thread、同一42入力を固定。最良と最終は別評価であり、終点の良い例を理由にselectorを変更しない。旧R38選択42のcoreが完全一致した場合だけ旧判定を再利用する。旧最終は歴史的SHA参照で今回の新盲検評価ではない。新84は実際に全文を読み、7同一prefix/全文の判断一致を確認した。

人間DEV99は元の会話serialization、context256/新target192/直前最大64、終端EOS込み・元newline込みのcanonical NLL。TRAIN99は同じ既存RealPersona subsetで、JMRDや全混合TRAIN平均ではない。legacy planの一部sourceManifest metadataは元のRealPersona subsetを指し、現在のcombined token/index/source SHAと範囲を区別する。legacy saturation診断の旧比較はR25であり、R38とのsource効果とは解釈しない。exportの2026-10-08 version文字列は継承されたarchitecture tagで、実際の選択step・SHA・training metadataが正である。

1000/5000の途中診断はraw FP32 Pythonだけで、途中JS/export一致を主張しない。新TESTではなく、weight選択に使わない。元の17/13/9/group厳格ゲート、人間DEV<=0.9107185711429243/日常全文>=0/非loop>=4はそのまま。相槌・EOS・NLLだけで意味成功や新話者一般化にしない。source5は1cast/3公開ID、DEV99に1重複pair、採点者はassistantで盲検独立人間ではない。

Operator inspection scope：途中で既存minified R10 generation-policyを広く表示し、tool出力はtruncatedだった。予約節が含まれ得るためoperatorが全予約文字列を未見だったとは主張しない。実験モデルへのTEST入力・tokenize/loss/生成・新probe選択・訓練混入はしていない。operator-policy-inspection-scope.jsonに記録し、以後はacceptance/rubric keyだけを抽出した。新TEST結果という主張はしない。
