# Model Researcher：会話能力から逆算した新系列

独立分析。既存DecoderとR46設定、PR90/64組診断を読んだ。モデル推論・optimizer更新・学習コード変更は行っていない。計算値・SHA・仮定の機械可読版は`model-research.json`。

## 判断

4.66Mは64組の正対応と任意置換を両方記憶できた。これは「小さい表すら学べない」という説明を退けるが、広い日本語を合成・一般化する表現容量が十分という証明ではない。未更新32組は両条件とも全件悪化し、全文生成も改善しなかった。容量不足、データ分布、目的、最適化をまだ因果的に分離していない。

方針を狭いloss係数変更の反復から、**十分な人間原文を用いる言語基盤→自然な応答→複数ターン**へ移すことを支持する。容量拡大は有力候補に戻す。ただし現在のデータ量のまま大きな表を暗記するモデルを作らない。

## 容量候補と計算資源

以下は現自作Decoderと同じpre-LN/GELU/FFN4d/tied embedding、8層、context512、旧ownBPEのV=5455を使った**例示の厳密parameter count**。新Tokenizer/構造採用時は実際のV/層から再計数する。GPUでの適切なhead幅64の例としてheads5/8/12を示すが、これは後述のheads4固定width-only pilotとは区別する。

`P=Vd+Sd+L(12d²+13d)+2d`

| 候補 | dim / heads | parameter数 | FP32 model+grad+Adam静的状態 | model+Adam checkpoint概算 |
|---|---|---:|---:|---:|
| small | 320 / 5 | 11,773,760 | 179.7MiB | 134.7MiB |
| medium | 512 / 8 | 28,275,200 | 431.4MiB | 323.6MiB |
| large | 768 / 12 | 61,287,168 | 935.2MiB | 701.4MiB |

FP32 parameter4+gradient4+Adam moments8=16bytes/parameter。保存はmodel4+moments8=12bytes/parameter（beststate重複なし）。activation、attention、logits、CUDA allocator、Python、データ、再開一時ファイルとGitの複製は含まない。FP32 modelにautocastを使っても静的16Nは減らず、主にactivationが減る。

仮のplanning bandを20N〜50N処理tokens、密行列学習を`6NT`FLOPsと置く。これは最適点、必要十分量、会話成功の保証ではない。

| 候補 | 処理token計画帯 | dense計算量 | 実効5TFLOP/sの場合 | 実効20TFLOP/sの場合 |
|---|---:|---:|---:|---:|
| 11.8M | 235M〜589M | 16.6〜41.6PFLOP | 0.92〜2.31h | 0.23〜0.58h |
| 28.3M | 566M〜1.414B | 95.9〜239.8PFLOP | 5.33〜13.32h | 1.33〜3.33h |
| 61.3M | 1.226B〜3.064B | 450.7〜1126.8PFLOP | 25.04〜62.60h | 6.26〜15.65h |

この時間は**利用可能なGPUの実測ではない**。5/20TFLOP/sはpeakではなく仮の実効速度。attentionの二次項、padding、再計算、入出力、保存、逐次生成評価、kernel launch等を除く。小型モデルの低utilizationもあり、実機profile前にこの時間で予算を確約しない。end-to-endには2〜4倍以上の余裕も必要になり得る。

batch4〜8/context512/効率的attentionを想定する初期GPU trialの目安はsmall8GiB（16GiBなら余裕）、medium12〜16GiB、large16〜24GiB。実ピークVRAMは未測定であり、microbatch・accumulation・activation checkpointingを含めて測り、余裕を残す。context1024はparameterだけでなくactivationとattention計算を増やす。

現環境はGPUなし、3vCPU/RAM9.7GiB。仮にCPU実効20GFLOP/sでも上記dense学習の20N下限はsmall約9.6日、medium約55.5日、large約260.8日。GPUと同じ日程感でCPU本学習を開始すべきではない。空き142MiB時点ではsmallのfullstateだけでほぼ尽き、再開/保存/版管理が成立しない。親の安全なcache整理後にも、最小pilotは>=1GiB、大モデルstate試験は>=4〜8GiBの空きと実測を勧める。

## データ量が拡大判断を制約する

R46 `train.index.json`のvariant0だけを集計すると、全canonical11,078,787tokens、うちhuman-chat7,505,019tokens/13,550原典、非会話3,573,768tokens。重複windowや3segmentation viewsを新情報3倍として数えない。

この全canonical量を変更せず20N〜50Nを処理すれば、smallで約21〜53epoch、largeで約111〜277epochに相当する。これだけ反復しても新しい人間の発言や話題は増えない。現在の人間会話量を基礎として活用しつつ、modern human prose、日常会話、相談・説明・質問の広がりとライセンスを監査し、独立な原文を確保する必要がある。新seriesのspeaker分割後のTRAIN量はさらに少ないので再集計する。

現BPEのhuman原典効率は1.273characters/token。context256は平均約326文字、512は約652文字に対応するだけで、何ターンを保持できるかの保証ではない。全文の発話境界、参照対象、履歴の必要部分が収まる率を実測する。独自8k/16kBPEは候補だが、TRAINのみfit、byte roundtrip/UTF8/fallback/文節分割/圧縮効率を監査し、tokenizer間ではper-token NLLを直接比較せずbyte基準も使う。語彙増加はembedding容量も変えるため、その介入を容量効果と混同しない。

## 親が確定した最初のpilotへの確認

最初の新系列は、原典話者で新TRAIN/held splitを作り、**新TRAINだけからown glyph+512wordBPEをfit**する。旧Tokenizerは新held speakerを元TRAINで既に見ているため、新系列の真の未見評価へ流用しない判断に同意する。

新系列内の比較は8層/context256/heads4固定、dim192対320（FFN4d）とし、差はwidthと派生shapeのみ。fresh random weights/fresh Adam、同じ学習・データ・条件を共有する。各モデル512本線+再開replay2=計1028実更新を上限とする親案は、**CPU2threadで全体30分の予算に収まる実測profileが通った場合のみ**実行可能。forward/backward/保存/生成評価まで見積もる。V=5455の場合のdense step負荷はB4×S256でsmall現行幅約28.6GFLOP、dim320約71.8GFLOPなので、2arm合計512更新ずつでも実効40GFLOP/sなら約21.4分＋overheadが目安。実効速度を仮定だけで確定しない。

EOS2は発話末尾、roles3/4は人間A/B、BOSはdocument開始、turn5は未使用という親のprotocolを一貫して学習/推論/評価へ適用する。人間A/Bは本物のAI assistant役ではないので、この段階は自然な会話継続の言語基盤であり、指示追従やAI人格獲得ではない。本文とend/roleをcausal CEの正例にする。EOSを一部の独立newline BPEにだけ結びつける旧制約を避ける。

**BOS tokenだけではattentionをresetしない。** 1sample=1doc内window、または明示的cross-document maskを検証する。role/endのeasytokenだけでlossが下がる危険があるので本文NLLと境界NLLは別報告し、最終判断を生成全文の内容・適切性・自然さ・反復へ置く。

R46と新seriesではsplit/tokenizer/境界表現/初期化/学習recipeが複数変わる。両者は記述的な参照比較であり、改善をwidthだけの効果と呼ばない。width効果の科学的比較は新2モデル内だけで行う。新speaker-heldは新scratch weights/tokenizerには未見だが、R46は元TRAINとして知っているので、その曝露差も表示する。

## 段階と次へ進む条件

1. **言語基盤**：人間が書いたmodern proseと原典会話を、正しい境界とcausal CEで広く学ぶ。独立doc/family入力から無修正の全文が安定して意味を持ち、長い反復が少ないことを確認する。pipeline smoke成功やNLL低下だけで会話能力を獲得済みとしない。
2. **日常応答**：完整な前発話と人間返答を保ち、短い相槌と内容返答を分けて評価する。基盤分布のreplay/mixで更新外の発話を壊さない。相槌の自然さだけでなく未知familyの内容適切性が改善し、全文反復/終了が悪化しないことを進級条件にする。
3. **複数ターン**：必要な過去の対象・話題を含む2〜8turnの参照を評価する。同じ直近発話でも前の文脈に応じた**内容**が変わるかを見る。文面の変化だけで成功としない。履歴coverageの必要性を示してからcontextを拡張する。
4. **知識/推論**：自然な日常会話が先。後に出典付き知識とheld問題で測る。現在の小pilotから汎用AIへの到達時間を推測しない。

RoPE/RMSNorm/SwiGLU等の自作は候補だが、最初から全部入れたpackageの差を原因別に説明しない。新family内の共通構造にするか、独立したablationにする。外部weights/tokenizer/生成正解は不要であり、使用しない。

最初のpilotの成果は、実行可能性と新splitでの最初の言語能力測定である。natural-languageの合格条件を満たさなければ、そのまま公開へ進めず、必要なデータ・GPU・次の識別可能な比較を残す。
