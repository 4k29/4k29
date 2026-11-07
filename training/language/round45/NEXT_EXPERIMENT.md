# R45終了時の次案 — この案の実更新0

R44を科学対照に学習率だけ2倍、2.2499999999999998e-5→4.4999999999999996e-5へ事前固定する。R45の係数0.2は日常反復を悪化させ、NLL/文脈利得の小改善が全文へ移らなかったため不採用とし、対照R44の係数0.1を維持する。R16〜R45で同じLRが続いており、RP40%条件下でのLR最適性は未検証。容量や単純な追加doseより先に一条件の感度を測る。

同じR28 full model/Adam20000 tensors・step/Python・Torch RNGから開始。optimizer param-group LRだけ変更し、他moments/groupsを混ぜない。初期forward/全DEVは変わらないことを確認し、実0 checkpointのLR例外も明示する。R44/R45terminalを延長しない。

資料35files/own5455 BPE40-30-30/主RP40%+JMRD5%/pool1024/CE係数0.1/他全loss/8層192dim/context256/seed/実10000dose/selector/greedy生成/厳格gateを固定。R45を直接対照にcoefとLRの二条件を変える試験ではなく、R44に対してLRだけ異なる兄弟比較。R45は既存失敗参照として保存する。新資料/role表現/容量/追加doseを同時導入しない。

LRは勾配/結果を見て探索しない。finite状態とclip/実counter・RNG/target exposureを検証し、旧新selected/terminal全168全文・新84実読解・humanDEV99・TRAIN64の7/57・pool1024・PyJS/rawを比較。悪化/数値分岐も隠さず、NLLだけで採用せず、公開モデル/R25anchorは維持する。
