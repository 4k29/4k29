# Round 42 結果 — 実10000更新完了、意味改善は実証されず不採用

R41と同じ初期R28 full model/Adam20000/RNGから実10000 optimizer更新を実行した。選択は事前固定の共通DEV最小値で9000更新（Adam29000）、terminalは10000更新（Adam30000）。R41の不採用terminalを追加延長した実験ではない。公開モデル・サイト・R25採用anchorを変更していない。

## 比較結果

|指標|R41 selected9000|R42 selected9000|R41 terminal10000|R42 terminal10000|
|---|---:|---:|---:|---:|
|共通DEV NLL/UTF8 byte|0.9653923983|0.9654554390|0.9658633414|0.9657874075|
|人間会話DEV99 NLL/byte|0.9338386936|0.9335080179|0.9329926932|0.9330825802|
|従来17初文合格|7|6|6|7|
|従来17非loop|3|2|2|2|
|従来17全文意味成立|0|0|0|0|
|日常12全文意味/最小会話行為|0|0|0|0|
|日常12長い反復|3|4|6|4|
|日常12EOS|9|8|6|8|
|実会話8全文意味/最小会話行為|2|2|2|2|
|実会話8長い反復|2|2|1|2|
|実会話8EOS|8|8|7|7|
|別資料5全文意味/最小会話行為|0|0|0|0|
|別資料5長い反復|2|1|2|2|
|別資料5EOS|4|4|3|3|

人間DEV selectedは僅かに改善するが、共通DEV・従来初文/非loop・日常反復は改善しない。実会話8の2件は短い好みの共有/同意で、具体名を明示した参照や新情報は0。長い自然な日本語を獲得したとはいえない。R10固定の17/13/9 scopesとnarrative/expository両群の全ゲートは不合格。固定humanDEV上限0.9107185711429243、日常全成立/非loop床、旧比較/anchor Paretoを緩めていない。

## 一条件と実際の学習

元の2漢字以上共有1616候補・donor・SHA順を保持し、必須3漢字span条件だけ外して先頭256組にした。2漢字候補制約は残る。旧256組を同じ候補から完全再構築しSHA一致を証明。正例文書163→190、旧と同じ正例30組。新資料、文書均等化、意味filter、係数gridはない。10 core learning filesは全てR41とbytes同一。pool変更に伴う文書/長さ/語彙/勾配規模の変化はこの条件の効果に含む。

own8層192dim/4heads/FFN768/context256/4,655,808params、既存own BPE5455語彙、main40/30/30、human RP25%+JMRD5%、CPU2 FP32、seed2049、LR2.2499999999999998e-5、batch8、wd.05、clip1を保持。correct-context CE係数.1/every10/batch2/cyclic/eval/fork_rng、wrong forwardは診断のみ。teacher UL1/selfnegative UL.1/EOSaux.3/competing-newline mainCE除外と元denominatorも維持。

実10000のmain正解対象15,578,400tokens/54,368,222bytes。全aux1000calls/2000pairs/47,057正解targettokens/94,114両文脈scoretokens/266,940両入力tokensを実traceと照合。mainとaux露出を混同しない。R41とのmain draws・最終Python/Torch RNG・初期model/momentsは一致。selfnegative rollout1000calls/39,026生成tokens/14,628negative位置は各モデル自身の生成で異なる。実loss100瞬間batch点、DEV21点、aux1000点をCSV保存。瞬間lossを全TRAIN平均と呼ばない。elapsed学習9312.23秒、resume/破棄更新なし。

## 原典と勾配・中間点

43 Python契約テスト、main35ファイル、全189166境界/mask、初期DEV0.9718989571266189・Adam/RNG一致、原典/再tokenize/donor/連結を全256組で検証した。最初16正例のprefix+target全文のみ開始前に実読解。残り240組とwrong donorの全意味監査はしていない。第一aux batch gradient norm12.691663、参照human CE5.029900、重み付き比.252324は有限。係数は測定前固定で、この一batchを全pool/composite校正としない。

200/1000/5000状態を保存。1000の新12全文も実読解し、日常意味0→0、反復2→4、humanDEV0.9434491396→0.9435959363。5000humanDEV0.9410305777→0.9413361017。中間結果で条件やselectorを変更しなかった。

## TRAIN診断を未見評価にしない

固定64組には新auxと同一発話7組が含まれる。事前に7/57の別集計を宣言し、重複を消すための再選択はしていない。両群ともTRAIN/source overlapであり57組もheldoutではない。現poolに含むというラベルを旧R41にも同じく付けるが、旧R41がその7組をauxで学んだという意味ではない。

|selected TRAIN診断|R41 correct NLL|R42 correct NLL|R41 gap|R42 gap|
|---|---:|---:|---:|---:|
|全64|3.47147597|3.42664828|0.10222097|0.11357256|
|現pool同一7|3.50125718|3.11422212|0.16996121|0.27536430|
|その他TRAIN57|3.46781863|3.46501640|0.09390199|0.09370340|
|現R42pool256|3.33028864|3.06585418|0.15939643|0.25080256|

改善は重複7組と訓練poolで大きく、非pool57への移行は小さい。64集計の改善を意味/未見一般化の証拠にはしない。旧R41自身の3漢字poolのNLLと新poolのNLLを異なるtargetのまま比較しない。human99は別speaker foldの既存DEVだがexact duplicate pair1組があり、TRAIN99対DEV99の話題/長さも一致しない。selected TRAIN99 NLL0.9062250381→0.9060703953、gap0.0276136555→0.0274376226は局所診断のみで全TRAIN過学習判定ではない。

## 全文読解・失敗と評価の限界

旧新selected/terminalの全168出力をALL_FOUR_STATE_GENERATIONS.mdに無省略・無修正で保存しtoken IDsも保持。新84全文を実際に読み、79種類のprefix/textをSHA照合したが独立79問とはしない。旧selected42は再生成raw coreと凍結R41読解の一致後に再bind。旧terminal42はSHA検証済み履歴。初文componentsは同一のliteral prefix+最初の句点までの文なら変更せず、R39〜R42の整合を検証。独立したblind人手評価ではない。

日常では「天気の毒が出るのか」「天井の話はどんな話を聞いているのか」など、語の局所結合は似ても質問の対象・主語述語・談話行為が崩れる。料理は時間、公園は行政的整備、週末は予報の説明へ逸れる。短いEOSと非loopだけでは意味成立にならない。実会話では歩行への「私も好きです」、パスタへの「おいしいですね」は普通の対象省略を認め自然な最小行為とした。新情報がないことだけを失敗にしない。

夕食を未提示他者への希望質問と補うなら日常whole1の感度、nativeの曖昧な具体化/好み質問を認めるならselected2→4、sourceの推薦/場所/経験の省略を認めるならselected0→2/terminal0→3を別記。terminal週末の有限多文・短い今日はstutterはprimary非長期loopだが侵入反復。語彙循環を広く数えればterminal日常loop4→5。selectedsourceの有限世代所有句は旧R40と同型のprimary非loopだが広く数えればsource1→2。terminal原17の短いSVG循環はprimaryloopだが有限構文重複と見れば非loop+1。出力は一文字も修正しない。未知固有名、創作事実、打切りだけで失格にしない。別資料5はONE cast/3公開仮名話者で5独立ジャンルではない。

## 数値とチェック

新84全sequenceでPython/JSとraw FP32/7decimal exportのprefix・token・EOS・全文が一致。測定reference最大logit差はPy/JS1.33514404296875e-5、raw/export2.288818359375e-5で固定2e-4未満。reference logitは標本で全生成step/全hardware保証ではない。旧selectedの今回JS42、raw25、原17raw未再実行、旧terminal数値は履歴という範囲を明示。既知R10 near-tie16/17（round11/execution/old-numerical-divergence.json）を保持し隠さない。

repository node962/962、既存public43問2580応答2580/2580、docs/app.js構文確認を実施。これは実験モデルの言語ゲート合格を意味しない。sequence-saturationのoldはR25anchor9500、legacy train-development-gapはR11canonical/R12cached選択行であり今回のR41対照/expanded全TRAIN平均ではない。reserved TESTにmodel/tokenizerを適用していない。R39の過去operator-wide policy表示で生じたexposure incidentも履歴に残り、blind TEST成功と主張しない。

## 原因の切り分けと次の一条件

1. 容量不足: 4.66Mモデルで多ジャンルを保持する制約は候補。ただし本比較は容量固定で局所poolだけ適応しており容量を原因と断定できない。直ちに大規模化しない。
2. データ量/偏り: 3漢字条件撤廃で文書190へ広がっても意味は改善せず、pool局所適応が大きい。mainは非会話70%、2漢字共有候補制約も残る。広い会話継続の被覆不足が有力候補。
3. 分割/文字境界: 全mask/token/連結検証、既存BPE40/30/30を維持。語片・活用崩れは残るがデータ破損証拠はない。分割そのものの能力制約は未分離。
4. LR/optimizer: finite moments/勾配/同一初期/RNG/実counterを検証、急な数値破綻なし。LR最適性は未検証で同時変更しない。
5. context長: 256制約と長文劣化は候補だが短い会話prefixから既に崩れるため、長さだけでは説明できない。
6. 不足学習/過学習: 局所poolは大幅改善、TRAIN57移行は小さい。学習不足だけ/全TRAIN過学習とは断定しない。単純なdose追加は優先しない。
7. 推論誤差: 新84でraw/export/PyJS全文一致なので今回の主失敗を丸め誤差で説明できない。既知R10分岐と全hardware保証の欠如は残す。
8. 評価欠陥: 既知DEVの小標本・曖昧省略・TRAIN64重複・話題非整合・greedyのみ。primaryと感度を分け、同一全文/初文の判定整合を検証したが、未見全般への統計的結論は出せない。

次は同じ1616候補SHA順の先頭を使い、aux poolサイズのみ256→1024とする比較を推奨する。総10000更新/1000calls/2000pairsと係数を固定し、同じ少数正例の反復を減らして被覆を広げた場合に非poolTRAIN57とhumanDEV/全文へ移るかを見る。候補制約・donor・main・容量・LR・seed・dose・selectorは変えない。対象長/構成の変化はpool-size効果に含む。新規追加分の原典/token/境界と勾配を開始前に監査し、固定TRAIN64の新overlapを再測定する。これを未見と呼ばず、意味成立しないままNLLだけで採用しない。これは次ラウンド案で、R42中に実装/訓練していない。

## checkpoint/SHAと再現

全ての重み・Adam・private Python/Torch RNGを整合した6役割として保存。rawは追跡lossless partsからbyte一致復元できる。ファイルmetadata SHAとmodel tensor一致を区別する。

- initial: `3be999e885246a07460361be559524d1857b10a594f23908b10abf2dead056fb`
- 200: `843dfffb55065d7fc4500f76469a92963107fed6669ac284bdf6bf050854b768`
- 1000: `cdfdcb4d82d7ad064fd7373d16c16d0d73e10265c863325b5fc8fdae26ec4427`
- 5000: `94739afb1733950f5116d29fd4ee4b069ec1b3c8af0d0f8e40279ec05bff4851`
- selected9000: `f087101dc480e0dcd3591caecb6ea590efa4e533d9ca0c55121a93ec0aeb167f`
- terminal10000: `8895b6e2064e3220d678cd4edfc45da7de1355abdfc217805775b3c3a22439a0`

- policy: `23258a711973cf058146b6b5e0ed1ecc54e2f1f23bd4369b8bdd29526f2ebc72`
- frozen417入力manifest: `0bc6ede953ebc0e9b48d0107abe10622d4122ca84ac84c9de13e52d95bd0e254`
- 新auxpool: `450bc9edbc5009a649ea1300637fbec4f903bca73b45b03978595c145521766e`
- pretraining commit: `357d5cf`。データ/コード個別SHAはsource-manifest.json/policy.json、最終成果はartifact-manifest.json。
- RESULTS/REPRODUCTION/NEXT_EXPERIMENT、全loss CSV、全full state/読解/数値をPR83へ保存。merge/deployしない。
