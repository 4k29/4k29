# Round48事前検証 — No-Go、本学習0更新

事前登録commit `a12cefc`、測定前のコード・Stage1固定commit `be8b77f`。科学対照R46、正式anchorR25。Round48本学習、モデル置換、マージ、公開環境変更は行っていない。

## 1. 原典話者と実返答関係

TRAIN原典13,550文書、373,321発話をSHAと本文・全3view tokenから検証。RealPersona260,902対、JMRD98,869対の全隣接対は、同じ文書の別話者の原順序の発話。speaker欠損/宣言外/同話者隣接は0。明示的reply-toは両資料に存在しないため、全件の意味的返答を認証しない。

事前固定の各12対/計24対をrootと独立Evaluation Analystが全文読解。各担当では両資料11/12、両方で接続を確認した保守的集計はRP11/12・JMRD10/12で、事前基準10/12以上を通過。曖昧例・不十分な返答・読解差は残し、TRAINの意味filterや標本差替えは行わなかった。独立人間評価ではない。

話者確認後も対象率は変わらない。全189,166rows中、候補119,491、真にCEが変化する119,213。固定80,000drawの再生では候補35,223、実変更35,134（43.9175%）、89候補は元と同じ重み。変更本文位置6,935,989のうち759,083に正重み、6,176,906は0となる。重み総量・元denominator・BOS/EOS・newline除外は維持。

全index最大位置倍率249倍、再生列最大223倍。原発話順序は保持。RPの時刻にはNaT296発話があり、parse可能な隣接260,553対に後退801/同時刻3がある。時刻順への並替え・除外はしなかった。両資料の既存TRAIN分割とCC-BY-SA-4.0/出典を保持し、DEV/TESTは開かなかった。

## 2. 実モデルのゼロ更新勾配監査

R47 CP0のmodel/Adam/Torch RNG/private Python RNGとR46 CP0の対応状態が完全一致することを確認し、同じR46条件（LR4.5e-5、sequence UL0.1、context CE0.1）を使用。元の433固定入力に変更/欠損は0。

通常64batch、事前固定の高倍率6batch、非会話/文字途中開始human/完全な発話対なしhumanのfallback3batchを実行。パネル内optimizer更新は0。同じ入力・dropout RNG・既存補助lossを比較した。

| 測定 | 対照 | 新条件 |
|---|---:|---:|
| 通常batch平均全parameter勾配norm | 3.454974 | 6.644594 |
| 通常batchのgradient vector population variance | 13.312090 | 48.316731 |
| clip norm1を超える通常batch率 | 100% | 100% |
| 通常batch平均main CE勾配norm | 3.389413 | 6.606287 |

通常batchのnorm比は中央値1.9414/p95=3.0892/最大4.3480。vector variance比3.6295は事前上限16以下、clipping率の増加0ppも上限25pp以下だった。

しかし通常nominal39でnorm比4.347996、高倍率nominal71で4.041017となり、事前に固定した許容区間[0.25,4]を超えたため不合格。対応する旧新勾配cosineは0.213/0.235。前者は2tokenへ124倍、後者は1tokenへ243倍の配分を含む。最大倍率だけがnorm変化を決めるとは限らない。

全loss/勾配は有限、欠損勾配0。独立した直接weighted CEとのscalar/logit勾配照合も全件合格（scalar最大絶対差7.152557e-7、事前atol1e-7/rtol1e-6）。数学的な質量保存だけでは勾配の大きさ・方向・分散は保存されなかった。

既存補助lossの値とparameter勾配は旧新で完全一致したが、主CE増大で相対normは低下。通常のscheduled6batchでcontext CEの平均norm/全体normは0.3891→0.2549、sequence ULは0.2190→0.1578。これらは足して100%になる寄与率ではない。clippingは方向差を戻さず、両群100%なので発生率だけの診断は飽和している。

このscreenは事前に選んだ運用上の判定であり、4倍が理論的発散境界という意味ではない。開始checkpointの固定パネルの結果で、長期発散、日本語能力悪化、容量不足を証明しない。

## 3. fallbackと実際の保存・再開

全73batchで無効化switchのloss・parameter勾配・RNG一致を検証。実fallback3種でも旧実装と完全一致した。

隔離した検証状態に対して、baseline/新条件それぞれ連続4更新と、2更新→実ディスク保存→model/Adam再作成・再読込→2更新を比較。補助lossの発火を含むnominal schedule9..12を使ったが、完了更新数は各経路1..4と別記。実optimizer更新は4×2経路×2条件=16回。Adam counterは両条件とも最終20,004。

model、Adam全tensor/counter、Torch RNG、private Python RNG、抽出row、配分記録、補助trace、lossがbitwise一致。検証用中間checkpointは隔離temporaryから実際に読み込み、終了後に破棄。SHA/byte数と最終state digestを保存し、検証重みを研究モデルへ昇格していない。Round48本学習は0更新のまま。

これは4更新経路の再現性確認であり、将来の本学習trainer/pipeline全体や全hardwareの保証ではない。今回、日本語生成やPython/JavaScriptモデル評価を新規実行していない。過去R47の84列一致と既知R10近接tie分岐はそのまま維持する。

## 4. 判定と次の研究

最終No-Go。再現性・実装不変条件は通過したが、全量集中方式は事前norm screenを通常/高倍率各1batchで超えた。閾値、倍率cap、短文filter、denominator、資料、samplingをその場で変えて通すことはしていない。再開試験の合格で勾配screenの不合格を打ち消さない。

次は本案のcapや係数を機械的に調整せず、固定checkpointでの文脈利用と自己回帰生成の差を診断する計画を優先する。同じ人間原文の返答を真正/別/除去した文脈で比較し、内容語予測と無修正生成を、source/view/返答長を固定して測る。これはまだ実行していない。

その診断後に、同じ小TRAIN集合への適合可能性と未見familyを分け、容量一軸、資料分布一軸、学習目的/配分一軸を別々に比較する計画を維持する。R27のFFN拡大失敗だけで容量不足を否定せず、tiny-set暗記も一般化とは扱わない。既存の17/13/9厳格ゲート、Pareto、R44実用guard、selector、R25anchorは変更しない。

## 最小コード変更と再現

追加は本preflight directoryに限定。既存学習コード・data・公開model/siteは変更していない。prototypeに追加した直接loss APIのmask検証は無効入力拒否だけで、有効入力の配分規則は不変。測定前レビューで補助勾配の比較対象を絶対値/digestへ修正し、相対比の自然な変化を誤って失敗扱いしないようにした。独立scalar参照と実human fallbackも測定前に追加した。

18件の合成/契約テスト合格。実model検証はSHA固定stage1 receiptを要求し、各scriptのCLI --helpを参照。gradient_audit.pyのexit2は今回のscreen不合格を表す正常な結果で、resume_audit.pyはその不合格を継承したまま再現性だけ確認する。assess_preflight.pyで固定条件からdecision.jsonを再計算できる。再開試験の再実行は検証用でもoptimizer更新を伴うため、単なる読取確認のつもりで実行しないこと。
