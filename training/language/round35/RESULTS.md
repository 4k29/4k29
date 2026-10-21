# Round35 結果 — 真の発話末尾へのEOS補助学習

実際のoptimizer更新**10000回**を1度完了。選択状態8000と最終状態10000の新しい84状態出力をすべて読んだ。うち2組は同じcore全文で、異なるcore出力は82件。同じ全文は同じ判定を維持した。**係数1.0は不採用**。停止・短い相槌には限定的な改善があるが、内容のある自然な日常会話を実証できず、共通/会話DEV NLLと従来17件の全文評価は悪化した。研究の採用anchorはRound25、公開モデル・サイトは変更していない。

[全168状態出力の無加工全文](execution/ALL_FOUR_STATE_GENERATIONS.md)、各manual/reading JSON、[数値照合](execution/final-output-verification.json)、[比較曲線](execution/paired-development.png)、[再現手順](REPRODUCTION.md)を保存。42固定入力×4状態であり168独立例ではない。旧モデルの全84件を今回新しく読み直したという主張でもない。

## 単一条件と実更新

Round34と同じaligned Round28 latestのmodel/Adam20000/Torch・privatePython RNG（weight lineage59000）から同じ10000更新を行う兄弟比較。唯一の学習変更は、human TRAINの真の発話末尾で元のunmasked targetがstandalone改行16の位置に、coefficient1.0のEOS2 CEを追加すること。和をbatchの**元のvalid target数**で割り、元の改行CEも残す。複合tokenに含まれる改行は対象外。R34の負例prefix境界条件は維持。

独自8層×192、heads4、FFN768、context256、語彙5455、4655808parameters、BPE40/30/30、human30%/旧genre70%、CPU2 FP32、batch8、seed系譜2049、LR2.2499999999999998e-5、wd.05、clip1、teacher4gramUL1、自己生成UL0.1/every10/greedy64/dropout train rescoring、推論greedy192と純CE checkpoint selectorは固定。追加model forwardや正例生成教師はない。

全10000の正例抽出、**15584824target tokens /54383388bytes**、最終Torch/Python RNGがR34と一致。EOS補助target161241か所、適用batch9163。対象数は独立したdraw replayと一致。自己生成負例1000回の初期prefixもすべてR34と一致し、全重み/momentsは有限。27 tests、147986全TRAIN行の独立mask検査、実モデル勾配、初期全DEV/model/Adam/RNG一致を学習前に確認し、388凍結入力のSHAも訓練中・訓練後に検証した。

latest full checkpoint SHA `1d36ee61325a7ca5a36bcc01feead680f598b267facc25d029b54c08e53e0e23`、Adam30000・lineage69000。selected8000 full checkpoint SHA `8dfe61a0900b109a4a02b26022bf9ca73305ef77f9f93d75dc1a9a47bfa4140d`、Adam28000・lineage67000。zero/actual200/1000/5000/selected8000/latest10000の6完全状態をlossless partsとSHAで保存。model.js/selected-weights.ptは推論用でありoptimizer再開用ではない。実学習時間9824.94秒。兄弟roundの更新を系譜へ足さない。

## 同一入力・同一生成条件の実測

| 指標 | R34 selected8000 | R35 selected8000 | R34 terminal10000 | R35 terminal10000 |
|---|---:|---:|---:|---:|
| 共通DEV CE NLL/byte | 0.967689158775 | 0.967821330452 | 0.968907478051 | 0.969065270309 |
| 従来17 初文合格 | 10 | 10 | 8 | 7 |
| 従来17 非長期loop・主判定 | 5 | 3 | 6 | 4 |
| 従来17 全文意味・主判定 | 2 | 0 | 1 | 0 |
| 日常12 全文意味・主判定 | 0 | 0 | 0 | 0 |
| 日常12 長期loop・主判定 | 10 | 8 | 11 | 10 |
| 日常12 EOS | 0 | 4 | 1 | 2 |
| native8 全文意味・最小会話行為含む | 0 | 3 | 0 | 0 |
| native8 長期loop・主判定 | 8 | 2 | 8 | 5 |
| native8 EOS | 0 | 7 | 0 | 5 |
| 固定source5 全文意味・最小会話行為含む | 0 | 1 | 0 | 1 |
| 固定source5 長期loop | 5 | 2 | 5 | 2 |
| 固定source5 EOS | 0 | 4 | 0 | 3 |

共通DEV初期値0.971898957127。R35選択NLLはR34より**+0.000132171677**で悪化。17/13/9の全scopeとnarrative/contemporary両群の厳格ゲートは、両新状態とも不合格。閾値は変更していない。新しいTEST結果はなく、反復して露出したDEVの1seed比較である。

native8のprimary3件は「そうなんですね！」「そうですね！」「そうですね。それはどんなものですか？」という短い相槌・確認質問。文脈に矛盾しない最小の会話行為として数えたが、固有内容の理解や会話発展を示さない。相槌を除く内容要求の感度では**1/8**、指示対象も厳格に要求すると**0/8**。source5の1件も「そうですね、おおー！」という驚きの相槌で、内容を要求すると**0/5**。同じ全文は両状態で同じ判定を維持した。source5は**1cast family・3公開ID**で、5独立集団ではない。これらを一般的な日常会話能力の成立とは認定しない。

日常12は短いEOSでも、まずはどこかにあるのかという不明な問い、AIが実験してみたいという格・接続の弱い返答、公園の問いと相槌の往復などで主判定0。挨拶を省略の多い希望表明として読む感度では1、雨の例を交渉対話として補う感度では2まであり得るが、primaryを変更せず保存した。日常loop8も有限な予報・食事・公園の扱いで7〜10、最終loop10は9〜11。反復の減少だけを意味改善にしない。

従来17ではR34の短く閉じていたENV05/MDN02が新selectedでは再び未閉鎖の法引用や「文字列を返します」の反復になる。terminalも旧STAT00の短い説明がPWA/サーバーの反復へ移り、全文意味0。未知名、創作、API事実の真偽だけでは失格にせず、主述・係り・内部意味・接続で判断した。末尾の軽微な生成上限切れは別に扱い、EOSによる不自然な早期終了を上限のせいにしない。解釈感度はoriginal-review-sensitivity.jsonと各readingに保存。

## EOSの作用と競合

TRAIN自己生成のhuman296回ではEOS終了**58→277**、即時EOS**1→4**、生成tokens15714→4588、反復負例位置9217→1448。固定DEVと異なる抽出prefixの訓練用64token診断であり、言語合格の証拠ではない。EOSによって自己生成負例の分布も変わるため、直接のEOS勾配と媒介効果をこの1条件から分離しない。

matched5000のTRAIN12行だけを使う事後診断では、補助対象67か所のEOS平均確率**0.032817→0.369663**、argmax0→37。元の正解NLLも0.892809→1.328342へ上がり、競合する改行/EOS教師の影響を示す。改行を含まない内容token1840か所でもEOS平均確率**0.001823→0.012167**、argmax3→45となった。これは過剰な終了傾向の懸念を示すが、45例すべてが不自然な代替終了だと証明はしない。詳細はEOS_LOCATION_DIAGNOSTIC.md。小さな相関したTRAIN subsetで一般化や意味を判定しない。

会話DEV99 NLLは**0.905768835509→0.910718571143**、R35terminal0.907144186733。固定TRAIN99は**0.869650598885→0.875082176939**、terminal0.870253833792。gapは0.03611824→0.03563639→0.03689035。EOS追加でtrain/dev両方の純CEが上がることは、単純な過学習の証拠ではなく競合目的の影響とも整合する。TRAIN99は全TRAIN平均でも全target既見の証明でもなく、DEVと長さ・話題が揃っていない。DEV99には完全重複1組がある。

## 原因の切り分け

- 容量: R27のFFN拡大で日常全文は改善せず、今回も容量を変えていない。一般的な幅・深さ不足は未否定だが、今回のEOS/NLL tradeoffを容量不足だけで説明しない。
- データ: R28/R29の人間会話30%/10%でも尤度改善と日常意味は別だった。今回も原文・抽出は同一で、停止だけを変えても内容生成の弱さが残る。新データを混ぜて作用を曖昧にしない。JMRDは人間原文候補の資料・licenseのみ確認し、対話データは未取得・未採用。READMEで露出した03042は将来採用時に除外する。既存CC-BY-SA原文の利用条件・分割を維持。
- 分割と境界: 全TRAINの正解・UTF8復元とmaskが正しい。補助対象はstandalone改行のみでview間比率が異なる。token化を変えず真の末尾を教える効果は測れたが、BPE一般の最適性を証明したわけではない。
- LR/optimizer: 初期model/moments/RNG、実counter、有限性とpaired抽出一致を確認。NLL波形はR34と類似し、8千回後の上昇も共有する。状態混在やoptimizer未更新の証拠はないが、LR最適性は未検証。
- context: 固定42入力は全て192tokenを生成できる余地があり、この評価の制限はcontext256より生成上限192が先。R34のcontext説明の補足を保存した。上限前の意味崩壊や短いEOS失敗はcontext延長だけで説明できない。
- 学習不足/過学習: さらに回数だけを増やすのでなく、EOS競合の強さを次に分離する。TRAIN/DEV99の両CE悪化とgapだけで過学習を断定しない。正例のraw target-byte coverageは同一親・抽出証明によりR33/R34と同じ58.1692%→82.6867%であり、意味や文脈のカバー率ではない。
- 推論誤差: 新selected42/42・terminal42/42でPy/JS全文、raw FP32/7桁export全文が一致。測定した意味失敗はこの数値差では説明されない。参考logit最大差1.1444091796875e-5、tol2e-4は不変。旧R10 near-tie16/17分岐は保持し、普遍的一致とはしない。旧export Py/JSは42件を現runtimeで再生成したが、旧raw FP32との比較は追加25件のみで元17は未再実行。旧terminalは凍結済み履歴資料。
- 評価: 露出DEV・1seed・assistant実読解で独立盲検ではない。短い相槌の成立と内容理解を区別し、すべての全文・理由・感度を残した。周期100更新のtraining lossは全てseqUL更新で、全更新平均ではない。旧saturationはR25比較、旧canonical gapはhumanを含む全TRAINではない。これらを科学比較R34や一般化評価と混同しない。

## 検証・採否・次

main pipeline exit0、追加source/terminal/TRAIN-gap評価も完了。新しい数値分岐やallowlist修復は不要だった。旧R34の修復履歴は旧資料として残す。Node962/962、既存公開回帰2580/2580を確認したが、実験言語ゲートの成功とはしない。全84新出力を実際に読み、旧selectedは全core同一の証明後に過去の読解を再利用した。

科学比較元R34、採用anchorR25の双方に対するprimary Paretoは不成立で不採用。公開挙動は維持する。次は**EOS補助係数だけ1.0→0.3**を1ラウンドとして、同じaligned Round28開始状態・10000更新・data/正解/prefix/LR/seed/BPE/他目的/selector/推論を固定する。末尾での終了傾向を残し、内容位置のEOS上昇と純CE競合が弱まるかを測る。R35内で複数係数を試しておらず、次の実更新もR35の完了数へ足さない。内容が改善しなければ係数探索を盲目的に続けず、原文・会話構造の仮説へ進む。
