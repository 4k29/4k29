# conversation-v2：能力中心の評価設計

GOAL.mdの自然な日常会話を評価する。本文NLLや原文のtoken一致、短い相槌の自然さを、内容を伴う未知会話への適切な全文生成と同一視しない。この文書は独立評価担当の提案であり、実際の評価入力・人間採点・新TEST結果を作ったという記録ではない。機械可読な条件は `evaluation-design.json`。

## 既存結果から維持する判断

- R46は文脈に反応するが、話題語の取り込みだけでは意味的な応答にならない。
- 64組診断では正対応も置換対応も本文token top1が100%、自由生成の正解本文再現も16/16だった。それでもAは14/16で本文後に生成を続け、未更新32組のNLLは全件悪化した。有限表の記憶、適切な終了、更新外への転移を別々に扱う。
- 原文goldは一意な正解ではない。別の自然な応答・適切な質問も許容する。汎用的なgoldは置換履歴でも成立し得るため、別履歴を一律に意味的負例と呼ばない。
- 全文の崩れを省略しない。最初のgold相違token、機械的4gram反復、分岐後のcounterfactual gold NLLを、意味破綻や言語正答率と呼ばない。
- 旧17/13/9厳格ゲート、Pareto、日常会話の反復上限、R25正式anchorを緩和しない。新しい軸で過去の採点を上書きしない。

## 最初のCPU pilot

新系列の幅192と320の比較は、同一の新TRAINのみで学習した独自BPE、scratch初期化、fresh optimizer、データ・順序・target/EOS dose・固定更新数・生成条件を共有する。幅以外を変えない。異なる幅では初期tensor形状が違うため、同じseedは同一初期重みを意味しない。計算量も異なるので、同token量の比較とwall time/計算量を分ける。

固定32件のDEV原典会話履歴から、各endpointにつきfull-vocabulary greedy192・真の発話末尾EOSで無修正全文を保存する。new2モデルで64held TF windowsも評価し、本文/EOSを分離してNLL/tokenとNLL/UTF8byteを出す。R46の参考生成を加える場合は計96全文。

このpilotは `human_dialogue_continuation` であり、AIとしての直接応答・指示追従を獲得したとは呼ばない。role3/4は人間A/B、EOS2は人間発話末尾である。原典話者の「私は○○県」を再現しても、AI自身の事実的属性を回答できたことにはならない。

R46は旧plain履歴・旧BPEであり、旧TRAINを既学習である。new系列の文書/話者family holdoutは重み未露出で、新BPEも新TRAINだけならTokenizer未露出とできるが、R46にとっては未見ではない。したがって旧新比較は露出とformatの違う参照比較で、幅だけの因果比較や共通未知TESTではない。旧BPEを再利用するとTokenizer exposureも残る。

new role込みprefix<=64でも、旧plain prefixが旧BPEで64を超える場合がある。R46についてsilent cropやcase毎max-new変更で「同条件」にせず、ctx256内で192生成できるcoverageを別記する。new seriesの32件をR46に都合よく出力後に選び直さない。

更新終了は出力前に固定する。wall制約に備えるなら128/256/512などの共通milestoneを両armで保存し、双方が到達した最大事前milestoneを、更新数だけで選ぶ。片方512、片方途中という異なるdoseのterminalから容量の優劣を断定しない。再開replayも実更新予算へ数える。

**主要値は全32件の全文複合成功数**：自然さ・全文意味・入力への適切性・自然な発話終了が成立し、有害反復がないこと。入力から内容が必要なcaseでは、内容を伴う適切さも必要とする。各軸、不確定、純相槌、末尾崩壊を別表に残す。

探索的な実用signalの提案は、wideがsmallより複合成功で4/32以上増え、有害反復と無効UTF8/意図しないspecial tokenが増えないこと。これは事前の便宜的診断flagであり、32件・単一sourceの統計的優越、能力獲得、採用の基準ではない。family対応区間、全discordant case、NLLとは独立した全文理由を併記する。flag未達だけで容量を否定しない。

追加4episodeの自己履歴rolloutを行うなら、32件とは別枠でuser文と要求状態を出力前に固定する。実際の過去のモデル返答を履歴に入れ、gold履歴で置き換えない。モデル逸脱後に固定user script自体が不適合になった場合は、その適用性と最初のモデル失敗を分ける。

## rubricと原文annotation

出力を見る前に32件の `contentRequired`、許容される内容/質問の条件、文脈で決まらない個人情報、原文goldの省略・未完結懸念を記録する。必要内容はgoldの文字列と同一である必要はない。元原典が途中文で終わっていれば、その再現を全文成功にしない。

全文に対し以下を別々に採点する。

| 軸 | 判断 |
|---|---|
| naturalWhole | 活用・語順・修飾・文接続が末尾まで自然か。自然な口語省略は許容 |
| meaningfulWhole | 途中から意味や主語述語、文と文の整合が壊れないか |
| appropriateWhole | 人間の実際の発言意図・話題・先行条件に全文として応じるか |
| specificContentAppropriate | 必要な情報・提案・適切な確認質問があるか。単語pickupや相槌だけは不可 |
| genericOnly | 他の会話でも使い回せる相槌だけか。自然さとは別 |
| harmfulRepetition | 同内容の循環・句読点連打など意味上有害な反復があるか |
| contextConsistency | 過去の対象・制約・好み・参照を維持するか |
| naturalTermination | 真のEOS/EOTで適切な内容を自然に終えたか。空応答・途中切れ・max到達・loop末尾は失敗 |

不明は理由付きnullとし、成功に加えない。原文と違う正当な返答、分からない事項への適切な質問は許容する。反対に、human continuationと違って `assistant_reply` では入力にないAIの私的経験・属性の捏造を適切としない。

pilotの盲読はassistantでもよいが、モデル名/幅/step/gold/TF値を隠し、全出力を実読し、主観性・原文記憶・同一出力から推測できる制約を記録する。独立した人間評価と呼ばない。正式milestoneでは日本語母語の独立2名以上が盲検で全件を読み、不一致と事前のadjudicationを保存する。

## 日常会話の正式benchmark案

まだ刺激を収集・固定していない将来仕様であり、既存封印TESTは開かない。新たな適法な人間原典/family、または人間が作成した評価資料について、学習・Tokenizer・選択・過去の評価への露出を監査する。assistantが作った文章を人間原典と偽らない。

| component | 内容 | 件数/model |
|---|---|---:|
| JP60 | 現代日本語の継続、短/中/長各20、少なくとも3source/family strata | 60 |
| REPLY80 | 質問・説明・相談・内容を要する雑談、各20 | 80 |
| CTX40 | 直前発話が同じで、先行履歴によって必要内容が異なる20対 | 40 |
| ROLL72 | 実際の自己返答を履歴に含む24episode×3返答 | 72 |
| 合計 | 独立した軸で採点、modeとsource別に集計 | 252 |

CTXは両履歴への適切な返答と要求された意味差がそろって成功。文面が異なるだけ、どちらも一般相槌、関連語が違うだけでは成功にしない。内容最小対は人間が要求差を出力前に定義し、NLL用同長対と混同しない。

### 段階を進める将来の要件案

数値は現在の結果に合わせた緩和ではなく、今後事前登録するproduct/research要件の提案である。現時点で正式benchmarkの実体や合格結果はない。

- Phase1：JP60で全文自然/意味各90%以上、各長さstratumの全文意味85%以上、有害反復2%以下、話題逸脱5%以下、自然な終了95%以上、無効UTF8/意図しないspecial token0。独立なsource/family TEST counterpartと複数seedでも確認する。
- Phase2：Phase1を保ち、REPLY80で全文適切85%以上、内容適切80%以上、各intent適切75%以上。内容を要するcaseのgeneric-only10%以下、有害反復2%以下、自然終了95%以上。
- Phase3：前段階を保ち、CTXの両方が意味差を反映する対85%以上、ROLLの全3返答が適切で整合するepisode80%以上。有害反復/終了も維持する。

小標本の点推定は保証ではない。最低200件の完全な独立heldout返答、人間2名以上、family/episode単位の95%区間と全n/Nを公開し、区間が広ければ追加評価する。旧17/13/9・Pareto・実用guardも引き続き満たすことが必要で、ここだけを通って公開へ進まない。今回、公開置換やマージはしない。

## まだ必要なこと

実際の32件とTF64windowsのsource/family/Tokenizer exposure receipt、出力前annotation、generation/step rule/hashの固定が必要。将来252benchmarkの独立source、封印custody、人間ratersは未確保。新native長contextや新Tokenizerを入れた場合は実際のbytes/token/coverageを固定し直し、異なるtoken NLLを直接比較しない。この不足を「benchmark完成」や「言語能力合格」と記録しない。
