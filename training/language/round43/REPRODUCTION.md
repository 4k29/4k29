# R43 再現・復元

実10000更新完了。完了runを再開/再訓練しない。まず全入力・成果・lossless parts・6 full model/Adam/RNG・actual counters・読解/数値/Git追跡を検証する。

```bash
python training/language/round43/execution/verify_final_artifacts.py --require-tracked
```

raw欠損時は追跡済みadjacent chunks.jsonから個別/連結SHAを確認してbyte一致復元する。例:

```bash
python training/language/round43/checkpoint_chunks.py restore training/language/round43/continue-10000/checkpoint.pt.chunks.json
```

latest10000/Adam30000、selected9000/Adam29000。6 full SHAはRESULTS.md/artifact-manifest.json。選択重みをlatest momentsへ混ぜていない。元の起動は `bash training/language/round43/execution/persistent.sh`。controller/trainer両lockと完了拒否guardを備える。部分checkpointを調べた場合だけ同一条件の`--resume`を使う。今回はresume/破棄更新なし。

独立再実験はzero-update commit `96e2ff3da65503181db5c1a5f91408d01fa5fed0` の別checkout/worktreeで行い、417入力の欠損rawを各追跡partsから復元し全SHAを照合する。現在の成果を消さない。元pretraining commitの中間評価numeric listにはコピー元41/42が残るため、実施した読み取り専用修正も適用する。最終commitの `diagnose_paired_1000_daily_corrected.py` と `wait_interim_corrected.py`、`interim-evaluator-correction.json` を参照し、1000/5000 read-only診断は修正版waiterを使う。訓練/生成条件/元417 inputsを変えず、旧waiterと重複実行しない。この修正は1000評価前・確認済み900更新時点に実施した。

Python3.12.14/PyTorch2.14.1+cpu/NumPy2.3.5、train CPU2 FP32 deterministic/seed2049、inference Python1thread、compileFalse。serialized checkpoint/JS metadataはelapsed等でSHAが変わり得るため、再訓練のtensor/RNG/実counterと再生成prefix/text/token/EOS/UTF8 coreを区別して照合する。異なるhardware/libraryでbit一致する保証ではない。

訓練はGit内prepared token/index・own tokenizer・元発話境界map・固定poolを使用。原典再監査/human99の再計算はprospective-daily-sourceのpinned commit/sourcePath/SHA/licenseに対応するTRAIN/development raw JSONが必要。実行cacheは`/workspace/daily-conversation-source-audit/human-only-raw`。外部cache依存を省略せず、再取得も元SHAとTRAIN/development範囲を確認しreserved TESTへtokenizer/modelを適用しない。

```bash
python training/language/round43/execution/daily_human_likelihood.py --model training/language/round43/continue-10000/model.js --out /tmp/r43-replayed-human.json --raw-cache /workspace/daily-conversation-source-audit/human-only-raw
```

固定42prefix、own full vocabulary greedy192/no repair。original17、daily12、native8、source5のselected/terminalと旧モデルの計168全文を保存。新84/77 unique full-prefix-text pairsは実読解、独立77問やblind人手とはしない。old selected42は凍結manifest+再生成core一致を検証、old terminal42は履歴。as_executed読解記録器は保存済みgeneration SHA専用で、将来モデルの自動semantic graderではない。新しい全文は実際に読み直す必要がある。R10固定gateの17/13/9・narrative/expository両群を保持。既知DEVで新TESTではない。1000は旧と完全同一の生成を実測、5000はloss/contextのみで追加自由生成なし。

保存はrawとpartsを対応付け、ignoredな旧展開コピーだけ個別/連結/元SHAと追跡を確認後に整理した。unique状態と現入力は削除していない。初期/200/1000の厳密tensor identity、1290の実露出切替、5000/10000の主sampler/RNG一致を確認する。Git自動GC packingを停止しlocal gc.auto=0/gc.autoPackLimit=0にしたのは保存領域/CPU保護で、訓練を中断していない。
