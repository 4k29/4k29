# R46終了時の次案 — この案の実更新0

科学対照R46、R28最新fullstateの同じmodel/Adam20000/Python・Torch RNGから開始する兄弟試験。正式採用R25/公開モデルは維持し、R46を研究用対照として使う。

sequenceUnlikelihood.coefficientだけ0.1→0.2。LR0.000045、correct-context CE0.1、主RP40%/JMRD5%/資料35files/pool1024、horizon64/negative window64、他全loss、8層192/context256、own BPE40/30/30、batch8/CPU2 FP32/seed2049、実10000dose、selector/greedy192/厳格gateを固定する。model/data/容量/境界/追加doseを同時に変えない。

R46は会話NLLと短い応答で改善したが、selected日常loopは3→4で、正例NLLだけでは反復が解けない。負例損失の勾配は有限で診断上全停止していないため、その重みを一条件で検証する。R45の正文脈CE増は別目的で不採用。R30のhorizon64→128は既に失敗したため、同じ上限延長を自動的な解決としない。今回380/1000が上限64だった事実も保存する。

係数は勾配を見る前に固定し探索しない。変更したcomposite lossの総値を直接学習能力として比較せず、非加重CE/各loss・固定DEV・全168生成と新84実読解・PyJS/raw一致を別に比較する。初期moments/RNG/fullDEV一致、全log/trace/実counter、1000/5000診断、共通DEV最小選択を維持。旧新main targets/bytes/RNGは一致を要求し、生成負例が異なることは別記。未見TESTの成功や一般化は主張しない。
