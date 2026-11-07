# 次の単一条件候補 — 未実装・実更新0

R41ではcorrect-context CEで人間DEV99とTRAIN64の正しい文脈NLLは改善したが、日常全文0/12、native最小行為3→2、source1→0で、意味の改善は実証されなかった。補助poolのcorrect NLLは3.56842→3.21587と強く適応し、診断64の3.48820→3.47148への移行は小さい。局所適応と整合するが、全TRAIN過学習や文脈不使用とは断定しない。

次は**補助poolの「正しいprefixと元の次発話に共通する3漢字以上のspanを必須とする」eligibility条件だけを外す**比較を優先する。この制約はR40の対照文脈のために導入され、R41の正例CEには同じ必要性がない。稀な内容語・限定話題へ偏った原文より、広い日常語・語順への追加正例学習が移るかを検証する。

同じ既存RP TRAIN原本、候補集合/塩付きSHA順序、256組、元のprefix/target token長制約、真の2発話prefix・完全な元発話・連結検証、donor規則、canonical分割、係数0.1/every10/batch2/cyclic、eval/fork_rng、wrong診断のみ、全main条件、LR・seed・初期R28 full state・実10000更新・selector・生成・全gateを保持する。漢字条件を外す結果として文書/語彙/長さの構成が変わる効果はpool変更に含めるが、別のdocument balancingや意味filterを同時に追加しない。model scoreによる候補選択や係数gridもしない。

正例の拡大は生の原文と元の誤字を修正した品質改善ではない。新poolのTRAIN/source SHA・元発話・BPE/mask・勾配・RNGを学習前に検証し、読解した範囲と機械検証の範囲を分ける。未見能力はgap/NLLだけで認定せず、固定42入力・旧新selected/terminal・全全文・全厳格gateで評価する。

科学対照R41と同じR28 model/Adam20000/RNGからの兄弟比較とする。不採用R41terminalを単純延長しない。新資料取得、全体source比率、poolサイズ/文書均等化、EOS target追加、BPE比率、モデル容量、LR、dose、selector変更は別条件として混ぜない。今回この候補はまだ実装/訓練していない。
