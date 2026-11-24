# R44 RESULTS — 主会話samplingだけ25%→40%

実10000 optimizer更新を完了。会話DEV NLLとTRAIN文脈利得は改善したが、選択重みの日常全文は0/12のまま。最終重みには短い成立例が増えたものの、従来17/13/9 scopes・両ジャンルの厳格ゲートと固定実用条件を満たさず不採用。公開モデル・Webサイト・R25採用anchorは変更しない。

## 同一条件の旧新比較

旧R43 selected9000と新R44 selected9500はそれぞれ同じ共通DEV最小selectorで選ぶ。terminalは双方実10000。全群で同じ入力・own vocab全体のgreedy192・Python1thread・無修正生成。42 exposed DEV入力の4状態168全文を[全文集](execution/ALL_FOUR_STATE_GENERATIONS.md)に無省略保存し、token IDsは各JSONに残した。新84全文（83種類のprefix+全文）を実際に読んだ。独立blind人手・新TEST・独立168問題とはしない。

| 状態・群 | 全文意味成立 旧→新 | 長い反復 旧→新 |
| --- | --- | --- |
| selected 従来17 | 0/17 → 0/17 | 15 → 12 |
| selected 日常12 | 0/12 → 0/12 | 4 → 3 |
| selected 実会話8 | 3/8 → 2/8 | 1 → 1 |
| selected 別資料5 | 0/5 → 1/5 | 1 → 1 |
| terminal 従来17 | 0/17 → 1/17 | 13 → 13 |
| terminal 日常12 | 0/12 → 2/12 | 6 → 3 |
| terminal 実会話8 | 2/8 → 1/8 | 2 → 4 |
| terminal 別資料5 | 0/5 → 1/5 | 3 → 1 |

共通DEV selected 0.965295332706→0.969086854892、terminal 0.965686618163→0.969694565511と悪化。人間会話DEV99 selected 0.933586965137→0.917695397049、terminal 0.932672926525→0.918483160721と改善。ただし固定上限0.9107185711429243には届かない。共通DEVはaozora/bunka/env/jma/mdn/mic/statの7siteで人間会話を含まず、別の会話DEVをselectorへ途中導入していない。

従来17の初文成立/非loop/全文意味はselected旧6/2/0→新4/5/0、terminal旧7/4/0→新5/4/1。日常EOSはselected旧9→新10、terminal旧7→新9。短いEOSや非loopだけで意味成立を判定していない。

## 生成を実際に読んだ所見

新terminalでは「週末は久しぶりに友達と会う予定で、どこかへ行きたいと思います。」と、公園を迷う相手への「行ってみたいですね。」が短い自然な接続として成立。従来17にも法律に基づく取組を進める有限一文が1件成立した。いずれも長い文脈維持や汎用会話能力を示すものではない。法律文は重複する「基づく」を厳しく取れば0、公園への共感に代案を要求すれば日常は1/12となる感度を保存した。

選択重みでは「寝るのが寝るのが起きてるんですか？」「天気の毒が出来るので」等、短い出力でも語形・主述・対象が崩れる。terminalでは雨・寝ると寝る・引用発話のメタ説明が長く循環。実会話terminalの暑さ・味覚・複合相槌反復も増えた。選択重みの会話NLLはterminalより良いが、日常全文はterminalの方が多く、NLLだけの能力判定はできない。

selected別資料の謝意による自然な終結、nativeの「あなたは？」による好みの聞き返し、terminal別資料のスカイダイビングの説明を求める問いは最小の会話行為として数えた。未知名・架空設定・外部事実の不一致・cap・新情報欠如だけでは失格にしない。話者交替を厳しく要求する場合などの別解を項目別JSONに保存した。

夕食の「何か食べたいですか？」は今回の読解では普通の食事提案とも読めたが、R42terminalに同一prefix/全文の主判定0があるため0を維持し、自然な省略解釈は感度へ保存した。[訂正記録](execution/reading-consistency-correction.json)。旧selected42は凍結manifest・再生成raw core一致で履歴判定へrebind。旧terminal42はSHA検証済み履歴。同一全文の主判定とR39〜R44の同一初文6項目を照合し、基準を今回だけ緩めていない。

## 学習・保存・再現

唯一の学習変更は主RealPersona確率25%→40%。JMRD5%固定、非会話70%→55%を元genre相対比で縮小。batching.pyのsource mass literal1か所以外の9 core filesはR43とbytes同一、資料35files/189166rows・独自BPE5455語彙・分割40/30/30・pool1024・全loss係数・8層192dim/4heads/FFN768/context256/4655808params・batch8・CPU2FP32 deterministic・LR2.2499999999999998e-5/seed2049・10000dose・selector・全gateは固定。同じR28 latest full model/Adam20000/Python・Torch RNGからの兄弟比較で、R43terminalの追加延長ではない。

開始前commit32989336871deb15a3778076eed6b8b9a7b8d2b7で426入力を凍結し、SHA・全189166行boundary/mask・90strataの各row/周辺sampling確率・43契約・勾配・初期全DEV一致・Adam/RNG・計算環境を検証した。学習中にも全426SHA一致を再確認。計算時間9260.902秒、実10000/Adam30000、selected9500/Adam29500。初期・200・1000・5000・selected・terminalの6 fullstatesとlossless parts、selected-weights.pt/model.js、全SHA・optimizer/RNG・CSV曲線を保存。復元・照合は[REPRODUCTION.md](REPRODUCTION.md)。

主targetは旧15578400→新15720338、bytes54368222→54747251、最終Python/Torch RNGは異なる。R44独自sampler replay/EOS露出counterと一致し、旧と同一とは主張しない。auxは1000calls/2000pairs、46537正解target/93074両文脈score/266752両入力tokens/1024distinct。self-negativeは1000rollouts/31721生成tokens/11254negative位置。追加のthrowaway optimizer更新はしていない。曲線は100更新ごとの1 minibatch損失・aux2組/10更新・全共通DEV/500更新を区別し、全TRAIN平均とはしない。

## 文脈診断と評価限界

固定TRAIN64のselected文脈利得0.10325473→0.11944759、正利得48→50組。pool内7件0.18862132→0.20107194、他57件0.09277111→0.10942355。両方TRAINで未見ではない。pool1024全体も0.18210369→0.19603087。terminal64平均は0.10364735→0.11366474でも正利得組数48→47で、全件改善ではない。

会話TRAIN99標本NLLは0.90618463→0.88794772、DEVとの差0.02740234→0.02974767。標本の内容/長さ/話題はDEVとmatchedでなく、全TRAIN平均でも全target既学習の保証でもない。DEV99は重複1組を含む。pool元発話・16例の過去読解履歴はSHAで再利用し、新しい意味監査を実施したとはしない。1024全source/token検証と1024全文意味監査は別。

全て既知DEVで単一seed/greedy・評価者依存の省略解釈という制約がある。R39の過去operator-wide policy表示によるexposure incidentを履歴に残す。reserved TESTへモデル/tokenizerを適用せず、新しいblind TEST成功は主張しない。legacy sequence-saturationのoldはR25anchor9500、legacy gapはR11canonical/R12cached標本であり今回の対照/全TRAINではない。

## 数値・実行不備の開示

新84件はPy/JS・raw FP32/7decimal exportとも84全文一致。最大reference logit差はPy/JS 1.33514404297e-05、raw/export 1.90734863281e-05、固定許容2e-4未満。標本referenceで全step/全hardware保証ではない。旧selectedの今回JS42/raw25、旧original17raw未再実行、旧terminal数値は履歴。既知R10 near-tie16/17とSHA117e5f69480f8856262090b46825efb9a2333732791c88e9a8b7484a8e406769を保持。

最初のpost-training pipelineは診断用diagnose_parity.mjsのコピー漏れでexit1。実行ファイルclosureの事前確認が不十分だった。学習は完了しており、R43同一bytesのread-only helperを追加し失敗点以降だけ再開。terminal waiterもprimary未完了でassertしたため、primaryが揃ってからread-onlyで回復した。訓練・frozen426入力・生成条件・重みは変更せず、追加optimizer更新0。元pipeline.log/mechanical-statusと失敗記録を残し、evaluation-recovery-complete.jsonで最終の全出力確認を別記した。凍結interim-planの旧R40表記も訂正記録を別保存し、実際の対照R43はコード/生成/CP SHAで確認した。

Node962/962・既存public43問2580応答の検証を実施した。既存public成功は実験モデルの言語合格ではない。ローカル容量のためR29〜R38の今回非依存93 prepared tracked filesをsparse working treeで省いたがGit/remote履歴は保持。詳細はWORKSPACE_STORAGE.md。

## 原因の切り分けと次案

1. 容量: 小型多ジャンルの制約は候補だが固定容量なので因果未分離。直ちに拡大しない。
2. データ: 会話配分増加は会話NLL/文脈利得に効き、共通DEVには代償が出た。元資料の量/品質とジャンル配分を混同せず、新資料の効果は未検証。
3. 分割: boundary/mask全行監査済みでも語形崩れが残る。固定BPEの因果は未分離で、vocab変更を混ぜない。
4. LR/optimizer: finite状態/実counter/初期一致を確認し発散の根拠はない。補助損失の強度やLR最適性は未検証。
5. context: 短い一文も崩れるので256上限だけでは説明できない。長い反復/話題維持と短文構造を分ける。
6. 学習量/過学習: 99標本gapは僅かに拡大するが全TRAIN過学習の証明ではない。selectedのNLLとterminalの短い意味成立が逆転し、単純追加doseでは判断できない。
7. 推論: 同じDecoderと今回84一致から、今回の全文破綻をPy/JS分岐で説明する根拠はない。既知近接argmax問題は別途残る。
8. 評価: 共通selectorに人間会話がない目的とのずれ、既知DEV、小標本、非blind判定、話者/省略解釈が制約。terminalを都合よく採用せず固定selectorを守った。

次はcorrect-context CE係数だけ0.1→0.2の比較を提案する。会話配分で文脈利得が上がっても生成接続が弱いため、同じ元人間の文脈/正解文の学習寄与を増やす効果を分離する。R44を科学対照に同じR28 fullstateからの兄弟比較とし、RP40%/JMRD5%・pool1024・資料・全他loss・model/LR/seed/10000dose/selector/生成/gateを固定。R44terminalを延長せず、新資料・role tags・容量・主配分変更を同時に混ぜない。係数増加による過適応/反復増加も同じ診断で調べる。
