# R43終了時点の次案 — R43中は未訓練・実更新0

主RP sampling比率だけ25%→40%へ変更する。JMRD5%を固定し、非会話70%→55%を元のgenre相対比のまま縮小。日常全文0/12のまま、予報/行政/文学の語と文体が会話へ侵入し、稀なaux正例のpool拡大だけでは主分布を変えられなかったため、日常会話の主露出を増やす効果を分離する。

R43を科学対照に、同じR28 full model/Adam20000/RNGからの兄弟比較。資料/own BPE/vocab/40-30-30、pool1024、全loss係数、モデル容量/context/LR/seed/10000dose/DEV selector/生成/全gateは固定する。新資料・意味filter・文書均等化・role tags・係数探索・容量・追加doseを混ぜない。

sampling確率に伴う主draws・target量・Eos露出・RNG trajectoryの変化はその一条件に含む。旧と同じmain exposure/final RNGは要求/主張せず、各run固有のsampler replayと初期state一致で検証する。data SHAは同じ、実際のgenre/view/target数を保存する。fixed TRAIN64の7/57とhuman99・原17/日常12/実会話8/別資料5の旧新selected/terminal全文で検証し、NLLだけで採用しない。R43不採用terminalを単純延長しない。
