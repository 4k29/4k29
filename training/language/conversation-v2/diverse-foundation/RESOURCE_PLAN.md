# 実測資源と次期学習の見積もり

無料CPU quota2 / RAM8GiB / GPU0。A/Bの実学習driver時間から見積もる。停止中の壁時計や人間の確認時間はdriver時間と別。次の量の独立コーパスが確保されたという意味ではない。

|教師targets|CPU2 driver時間の幅|30%余裕込み|概算dense 6NT FLOPs|
|---|---:|---:|---:|
|10,000,000|2.44–3.13時間|3.17–4.07時間|6.74e+14|
|30,000,000|7.32–9.39時間|9.52–12.21時間|2.02e+15|
|100,000,000|24.41–31.31時間|31.73–40.71時間|6.74e+15|

この幅は同じ11.23M/context256/CPU2での概算。モデル拡大、context延長、推論・追加評価の時間は別。GPU速度・GPU時間は未測定で、無料で利用可能なGPUも確認されていない。有料資源は使わない。

|構成|パラメータ|0更新forward/backward最大RSS|Adam moments未割当分|FP32 model+Adam一世代|
|---|---:|---:|---:|
|dim320/context256|11,225,280|630.4MiB|85.6MiB|128.5MiB|
|dim320/context512|11,307,200|914.7MiB|86.3MiB|129.4MiB|
|dim320/context1024|11,471,040|1482.3MiB|87.5MiB|131.3MiB|
|dim512/context256|27,397,632|829.2MiB|209.0MiB|313.5MiB|
|dim704/context256|50,647,872|1051.0MiB|386.4MiB|579.6MiB|

RSSは単発の乱数モデルforward/backwardだけであり、optimizer更新も能力測定も0。Torch/corpus/activationがありパラメータだけでRAMは決まらない。並行worker・cold開始による非単調な速度をモデル学習速度の比較に使わない。GPU用には同一batchの実測が必要で、16GiB級を計画候補としても適合や速度を保証しない。

大きい候補50.65Mでは全状態一世代約608MB（十進）、3保存点で約1.82GB、atomic pendingとrolling、Git objectsと作業コピーがさらに必要。現在の空きで容量拡大をそのまま開始しない。追加10–20GiB以上の作業余裕を確保し、原文・encoded corpus・lossless archive・Git保持・atomic世代を含む実予算を固定する。圧縮率やsparse省略量を実空きと混同しない。30M以上の原文を処理するにはストリーム化・indexed scheduleも別途実測する。

まず採用可能な現代日本語原文を10M→30Mへ拡張し、11M基準の学習・自由生成の実測を行う。容量27.40Mやcontext512は別の比較とし、データ・Tokenizerと同時に変更しない。
