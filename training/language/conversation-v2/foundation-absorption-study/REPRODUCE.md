# 再現と安全な状態確認

学習実行: https://github.com/4k29/4k29/actions/runs/43548860475
結果固定head: `8f053a2d1e762839dcd8b472860128bd33edbb3c`。その後のcommitは分析・軽量検証のみ。

1. 対象branchの新しい隔離checkoutを作り、この研究・PLANに列挙された依存ファイルを取得する。封印TESTは不要。
2. `python -B training/language/conversation-v2/foundation-absorption-study/verify_inputs.py` は既存tokenizer実装のみで6検査。
3. `python -B .../analyze_results.py` は保存済み結果の集計とmain agentの判定記録を再シリアライズする。判定自体を自動で意味評価するスクリプトではない。
4. `python -B .../verify_results.py` は5検査、`write_report.py` はTABLES生成。これらはTorch/modelをimportせず、optimizer/forward0。
5. `CHECKPOINT_INDEX.json` の7保存点は各COLD receiptのsource_commitに固定。remote-only bare Git（alternatesなし）へ該当commitをfetchし、manifest列挙順で `git show COMMIT:PATH/part-NNN.bin` を連結。各chunk bytes/SHA256と連結bytes/SHA256を照合してから、隔離環境で自分のcheckpointを復元する。pickleは信頼済みcommitの自作stateに限定する。
6. 全状態にはmodel、Adam、global/private RNG、sampler/cursor、trace、PLANと親のintegrityがある。SFT開始は親modelからfresh Adam/RNG規約で決定的に再構成し、PREFLIGHTの初期hashで照合する。

**完了済みengineを再実行してはいけない。** `GO.json` は初回run attempt・更新ledger未存在・親commitを検証する。再開は保存点のcursor/trace/ledgerが一致する場合に限り、新しい計画とrun IDで行う。自動replayや追加epochはない。今回再計算3呼出しは捨て検証の別process一致確認に限定。

model実測はPython3.12.16、Torch2.14.1+cpu、NumPy2.3.5、CPU4、threads2、GPUなし。完全な数値一致を他のBLAS/Torch/CPUへ無条件に保証しない。同一実行環境で3系列の更新後再開完全一致を確認済み。A-baseの同一SHA/入力/デコードの既存167生成とsource NLLは再利用しており、過去CPU環境との差が残る。SFTの新A対照は今回実際に再学習した。

追加専用CIは入力6検査＋結果5検査のみ。モデルを再学習・再評価せず、CI_RECEIPTにoptimizer/forward0を保存する。
