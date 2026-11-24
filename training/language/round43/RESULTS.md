# Round 43 結果 — 実10000更新完了、pool拡大は不採用

補助poolサイズだけ256→1024として実10000 optimizer更新を実行した。共通DEV最小のselected9000/Adam29000とterminal10000/Adam30000を別々に評価。共通DEV NLLは改善したが、日常全文意味0/12・従来全文意味0/17のまま。selectedの人間DEV NLLは僅かに悪化し、terminalの日常反復は増えた。厳格17/13/9 scopes・両ジャンル・実用床/Pareto条件を緩めず不採用。公開モデル/サイト/R25採用anchorは変更していない。

## 旧新・選択時点・最終時点

|指標|R42 selected9000|R43 selected9000|R42 terminal10000|R43 terminal10000|
|---|---:|---:|---:|---:|
|共通DEV NLL/UTF8 byte|0.9654554390|0.9652953327|0.9657874075|0.9656866182|
|人間会話DEV99 NLL/byte|0.9335080179|0.9335869651|0.9330825802|0.9326729265|
|従来17初文合格|6|6|7|7|
|従来17非loop|2|2|2|4|
|従来17全文意味成立|0|0|0|0|
|日常12全文意味/最小会話行為|0|0|0|0|
|日常12長い反復|4|4|4|6|
|日常12EOS|8|9|8|7|
|実会話8全文意味/最小会話行為|2|3|2|2|
|実会話8長い反復|2|1|2|2|
|実会話8EOS|8|8|7|7|
|別資料5全文意味/最小会話行為|0|0|0|0|
|別資料5長い反復|1|1|2|3|
|別資料5EOS|4|4|3|2|

実会話のselected2→3は、好み共有/同意/既出の行為への短い推薦という最小行為。具体的な対象名を明示した参照・新情報は0。推薦の解釈を厳しくすると2/8となり、安定した能力改善とは主張しない。terminalは2/8で増えない。日常の文と文を自然につなぐ能力・長い意味保持・未見への一般化は実証できなかった。

共通DEVは固定3分割を重み付けしたsegmentation診断で、自然文の確率そのものではない。全historyのsiteはaozora/bunka/env/jma/mdn/mic/statで、人間会話を含まない。別の会話DEV99はselectorに使っていない（diagnostic-scope-map.json）。selectedの共通DEV改善は0.0001601063、会話DEVは0.0000789473悪化。terminal会話DEVは改善するが、日常loop4→6・source loop2→3・EOS減少を伴う。NLLだけで採用しない。fixed humanDEV上限0.9107185711429243と日常の床、旧対照/anchor Paretoを維持。scientific control Paretoは共通DEV/原17集計についてtrueだが、厳格gate・実用guardはfalse。

## 唯一の学習条件変更と実際の露出

R42と同じ元1616個の2漢字以上共有candidate・元donor・塩付きSHA順を使い、同じ先頭256を先頭1024へ拡大した。旧256は新poolの完全prefix。3漢字必須条件はR42と同様なし、2漢字候補制約は残る。正例文書190→403、donor文書67。文書均等化・意味filter・モデルscoreによる再選択・新資料・係数gridは使わない。候補構成/長さ/各正例の反復回数の変化はpool-size効果に含む。

全10 core learning filesとmain35ファイルはR42とbytes同一。初期R28 full model/Adam20000/private Python・Torch RNGからの兄弟比較で、R42terminalを追加延長していない。own8層192dim/4heads/FFN768/context256/4,655,808params、既存own BPE5455語彙、main BPE40/30/30、RP25%+JMRD5%、CPU2 FP32 deterministic、seed2049、LR2.2499999999999998e-5、batch8、wd.05、clip1、CE.1/every10/batch2/cyclic/eval/fork_rng、wrong文脈は診断のみを維持。teacher UL1/selfnegative UL.1/EOSaux.3/competing newline mainCE除外と元denominatorも保持。selectorは共通DEV0/毎500の最小、生成はown full vocabulary greedy192/Python1thread/無修正。

総auxは双方1000calls/2000pairsで、旧256組は各7〜8回、新1024組は各1〜2回。新46,537正解targettokens、93,074両文脈scoretokens、266,752両入力tokensを実traceで照合（旧47,057/94,114/266,940）。main15,578,400正解tokens/54,368,222bytesは旧と完全一致し、最終private Python/Torch RNGも一致。view行比はcanonical0.4000375/glyph0.299025/random0.3009375。aux canonical追加露出とmain露出を混同しない。自己negativeは新モデル自身の1000rollouts/38,948生成tokens/14,569negative位置で旧とは異なる。

開始前予測どおり、最初1280更新は旧256prefixを同じ順で読む。実200/1000のmodel・全Adam moments・RNGの完全一致、500の全DEV/各loss/露出一致、step10〜1280の全128aux trace一致を実測。最初の異なる正例は1290で、新pool rank256/257（旧rank0/1）を実際に使った。1000時点の24生成coreは旧と一致し、主判定0/12・loop4・EOS9、人間DEV0.9435959363も同値。早期の改善を捏造していない。

実5000では1000個の異なる新pool正例を読んだ段階（1024個全ての初回露出は5120更新まで）。main露出/RNG一致を確認し、人間DEV0.9413361017→0.9408762226と小幅改善、TRAIN64gap0.10107156→0.09572915で改善しなかった。5000の自由生成は固定計画に含めず実施していない。中間値で設定・selectorを変えず実10000を完了。学習elapsed9888.82秒、resume/破棄更新なし。100瞬間batch loss/21全DEV点/1000aux eventとloss CSV、全自己negative traceを保存。瞬間lossを全TRAIN平均と呼ばない。

## 原典・勾配・実行の監査

主35ファイル、全189166行境界/mask、全1024原典SHA/元発話/再tokenize/concat/donor/available-anchor除外を開始前検証した。追加分の先頭16（rank256〜271）のprefix/target全文を実際に読んだ。旧先頭16はR42の履歴と同じ旧256行の完全一致を保持。新pool全1024とwrong donorの全意味監査をしたとはしない。新16には公園・子育て・休日・夜型・スポーツ・睡眠・語学・入浴・配信作品・仕事・記念日・弁当・夫との外出・冷房・野菜・洋楽が含まれる。原文の誤字/省略/主観/未検証の事実を修正せず、読後の再選択をしていない。

43 Python契約テストPASS、初期全DEV0.9718989571266189はR28と全view/siteが厳密一致。初期model/Adam/RNG一致。first2 aux gradient norm12.6916630308、参照3-row human CE5.0298998707、係数.1の重み付き比.2523243674は旧と同じ。係数は測定前固定で一batchを全pool/全composite校正としない。全値finite、eval/fork_rng/mode復元・zero optimizer updateを検証。

コピーしたpool-size契約の期待値256を意図した1024へ修正し43件PASS、原典勾配preflightのmanifestより前の呼出し失敗も開始前に正しい順で再実行した。開始後には中間評価スクリプトのliteralモデル番号41/42と期待ファイル42/43の不一致を発見。1000評価の前（確認済み900更新時点）に読み取り専用companionを作り42/43へ修正した。元417凍結入力は変更せず、旧read-only waiterだけ停止して修正版へ置換し、SHA/時刻/修正内容をinterim-evaluator-correction.jsonへ保存。訓練コード・重み・optimizer・生成条件・selectorは変更していない。再現には修正版を用いる。

ディスク確保では、Git追跡partsの個別/連結/原raw SHAを検証した旧R41のignored raw展開コピーだけを除去し、現入力/unique stateを保持。Git履歴/objectsを保ったbounded lossless packingの32バッチを検証し、重複looseコピーだけ整理した。push後に自動起動した大規模Git GCのpackingを止め、local auto GCを無効化。訓練へsignalを送っていない。全6役割のfull model/Adam/RNGとlossless partsを残した。

## TRAIN診断と未見評価の区別

固定TRAIN64と現poolの同一発話はR42と同じ7件、その他57件に分ける。両群ともTRAIN/source overlapで、57件もheldoutではない。新pool拡大で診断対象を再選択せず、membershipは両モデルとも現R43pool基準。各群の正例反復量も旧と新で異なる。

|selected TRAIN診断|R42 correct NLL|R43 correct NLL|R42 context gap|R43 context gap|
|---|---:|---:|---:|---:|
|全64|3.42664828|3.45671138|0.11357256|0.10325473|
|現pool同一7|3.11422212|3.42595114|0.27536430|0.18862132|
|その他TRAIN57|3.46501640|3.46048895|0.09370340|0.09277111|
|同一の現R43pool1024|3.34756616|3.34180725|0.18335448|0.18210369|

7件は8回相当→2回相当へ反復が減り局所NLLが悪化し、57件への移行は小さい。1024全体の同一target比較でもNLL改善は小さくgapは改善しない。旧R42自身の狭い256pool NLLと新1024pool NLLを異なるtargetsのまま比較しない。4state全診断と7/57内訳を保存した。gapやTRAINのNLLだけで自由生成・一般化を認定しない。

別speaker foldの既存人間DEV99にはexact duplicate pair1件がある。TRAIN99/DEV99は話題/長さも一致せず、TRAIN99はexpanded全TRAIN平均ではない。selected TRAIN99 NLL0.9060703953→0.9061846299、DEV0.9335080179→0.9335869651。gap縮小はTRAIN側悪化も含むので改善と呼ばない。terminal TRAIN99は0.9045894911→0.9040980349、DEV0.9330825802→0.9326729265だが反復/意味は改善せず、追加doseだけを選ぶ根拠にしない。

## 全文・失敗・判定の感度

[旧新4state全168全文](execution/ALL_FOUR_STATE_GENERATIONS.md)を無省略/無修正で保存。token IDsは各JSONに保持。新84全文を実際に読み、77種類のprefix/full textについて同一判定を照合したが独立77問題とはしない。旧selected42は凍結R42 manifestと再生成raw coreの一致を確認後に履歴判定へrebind。旧terminal42はSHA検証済み履歴。R39〜R43のliteral prefix+最初の句点までが同じ初文の6componentsは同一に保持。独立したblind人手評価ではない。

会話では天気の毒・天井の話・時間を作るなど、語は出ても質問対象と主述が成立しない。週末が予報、公園が行政的整備へ逸れる。terminalは日曜日/そうかの長い反復が増えた。説明文の非loopが増えても、数値/対象/修飾先の崩れと話題逸脱が残る。未知固有名・創作・外部事実の真偽・cap・新情報欠如だけで失格にしない。短いEOSだけで成功/非loopにしない。

selected実会話3件はバイクのレストアという既出行為へのおすすめです、女優への私も好き、パスタへのおいしいですね。普通の対象省略を認めた最小行為で、具体的な説明の獲得ではない。推薦を相手が既に実施している行為への弱い返答と厳しく読むと3→2、ストックの層の曖昧な具体化要求を認めると3→4。terminalは2のまま。選択日常の夕食確認と寝るのかなという自問は文法自体は成立するがopeningとの接続をprimaryでは不足とした。普通の省略を認める各whole1・両方whole2の代替を明示した。疑問文や早くという語の欠如だけを失敗理由にしない。

ループ感度も別記。selectedの有限な天気質問列を非loopに寄せればdaily loop4→3、短い今日はstutter/公園重複を広く数えれば4→6。nativeの三連続おいしいですねは旧同一全文に合わせprimaryloopだが短い強調なら非loopへ寄せる感度。terminal原17の有限アジア4回+気候proseはprimary非loopだが広い循環なら13→14、短いSVG循環を非loopに寄せれば13→12。terminal nativeの有限四つの相槌を非loopに寄せるなら2→1。selected sourceの有限世代所有句は旧R40/R42と同型のprimary非loopだが広く数えれば1→2。sourceの推薦/追加場所の省略を許せばwhole0→2。別資料5はONE cast family/公開仮名3話者で5独立ジャンルではない。出力を直して採点していない。

## 数値と実施チェック

新84全sequenceでPython/JavaScriptとraw FP32/7decimal exportのprefix/token/EOS/UTF8/full textが一致。max reference logit差はPy/JS1.33514404296875e-5、raw/export2.193450927734375e-5、固定許容2e-4未満。logit比較はreference標本で全step/全hardware保証ではない。旧selectedの今回JS42/raw25、旧original17raw未再実行、旧terminal数値は履歴という範囲を明示。R10既知near-tie16/17とSHA117e5f69480f8856262090b46825efb9a2333732791c88e9a8b7484a8e406769を保持し隠さない。

43 Python契約、Node962/962、既存public43問2580応答2580/2580、docs/app.js構文確認を実施。既存public評価は実験モデルの言語合格を意味しない。sequence-saturationのoldはR25anchor9500、legacy train-development-gapはR11canonical/R12cached選択行で今回の科学対照/全TRAIN平均ではない。modelVersionの静的旧日付文字列ではなく、actual step・SHA・UTC launch/結果で状態を特定する。reserved TESTへモデル/tokenizerを適用していない。R39の過去operator-wide policy表示によるexposure incidentは履歴に残り、blind TEST成功を主張しない。

## 原因の切り分けと次の一条件

1. 容量不足: 4.66Mモデルで多ジャンルを保持する制約は候補だが、今回容量固定で因果は未分離。直ちに大規模化しない。
2. データ量/ジャンル: 文書403へ広げても日常0。主学習は非会話70%、予報/行政/文学の語と文体が日常へ侵入する。稀な補助正例の拡大だけでは主分布を変えない。日常会話の主露出不足が次の検証候補。
3. 分割/文字境界: own BPE/40-30-30・全mask/連結/原典を検証、破損の証拠はない。語片と活用崩れは残り、分割設計そのものは未分離。
4. LR/optimizer: 初期・RNG・moments・finite勾配/実counterを確認。数値破綻の根拠なし。LR最適性や補助gradient強度の最適性は未検証で同時変更しない。
5. context長: 256制約と長い生成の劣化は候補だが、短い会話prefixから対象/主述が崩れるので長さだけでは説明できない。
6. 不足学習/過学習: pool1〜2回への希釈で7件の局所適応は弱まるが非pool57の移行は小さい。terminal会話NLL改善と反復悪化が併存するため、単純な追加doseや全TRAIN過学習と断定しない。
7. 推論誤差: 新84でraw/export/PyJS全文一致し、主失敗を丸め誤差では説明できない。既知R10分岐/全hardware非保証は残す。
8. 評価欠陥: 共通selectorが人間会話を含まないという目的とのずれも候補。ただしhumanNLLの低いterminalで反復が増えるため、会話NLL selectorだけでは意味を保証しない。既知DEVへの反復・小標本・主観的省略判定・TRAIN64重複・単一seed/greedy。感度と同一全文/初文整合を保存したが独立人手・未見全般への有意な改善は未実証。

次は**RP主サンプリング比率だけ25%→40%**、JMRD5%固定、非会話70%→55%を既存ジャンル相対比のまま縮小する比較を推奨する。資料・vocab・pool1024・全loss係数・model/LR/seed/初期R28 model/Adam/RNG・10000dose・selector/生成/全gateは保持。新資料/品質filter/役割tag/容量/係数/追加doseを同時に変えない。確率変更に伴う主draws/target量/EOS露出/RNG trajectoryの変化はそのfactorに含み、旧と同じ主露出/RNGとは主張しない。各runの独立sampler replayで自己一致を検証する。この案はR43終了時点で未訓練、R43中の実更新0で、別ラウンドにする。

## 保存したfull状態とSHA

actual countersとmodel/Adam/private Python・Torch RNGが揃った6役割をlossless partsで保存。serialized metadata SHAとtensor一致を区別する。
- initial0: `283f3d464373eafd3fe5ec80d53915124c48ff5eede756d77ed9641e05375be7`
- actual200: `25590bbe6b2dd3dac4d997c59d3c73cf1e99273378a7554ea5b0e5219e0b9117`
- actual1000: `a35d49cf498fdbb26fd8c70decf58014a5cf82534a50c146263ab010c3dca979`
- actual5000: `b9949fe592375ef4f47f3014eb6181bf0550acbd5ea549793a5c3212e53e9a79`
- selected9000: `a5996ecfe5323c74b66ae64a2620c269a0e301ae980293e1528052bdaffafa88`
- latest10000: `3002354b23cee169975d576ca83018e78ab9d363f6c309bf9c8fff26258d6edf`

- policy: `a715269d31819240b9ec68ff14f70b1cd7f3aeb350b13e237a7090d2d93859cf`
- frozen417入力manifest: `e04546759be672eab8e2aff0612dcca5124dcc831748b0899babfad2aca74ac2`
- pool1024: `635ccc53b445562a06ea39a3485a8c61409db38357d586e56e1831eb1cee1e7c`
- raw selected weights: `79689ea718cf63938c06aca709083d9d6cfff843ea51819f37509af21528425f`
- selected JS: `7698f62f61171469f2b891f4e6457564606f2c86aaee2978cf664f2a7fb96074`
- zero-update pretraining commit `96e2ff3da65503181db5c1a5f91408d01fa5fed0`。データ/コード個別SHAはsource-manifest.json/policy.json、全成果とpartsはartifact-manifest.json。
- loss CSV: execution/instantaneous-training-loss-curve.csv / execution/paired-ce-curve.csv / execution/context-auxiliary-curve.csv。単位/範囲はexecution/curve-units.json。
- 再現/復元はREPRODUCTION.md、次の条件はNEXT_EXPERIMENT.md、結果はPR84へ保存。merge/deployしない。
