# Round 15 結果 — 既存原文のジャンル構成対照

**実10,000 optimizer更新を完了。初文4/17、非ループ1/17、全文意味0/17。開発言語ゲート: False。** 公開モデル/Webサイトは変更していない。未見一般化は未実証。

## 事前固定した条件

Round 11を対照とし、同じRound 10採用親（系譜39,000）からの兄弟実験。TRAINジャンルのAozora行サンプル確率を45%→15%へ下げ、差分をMDN以外の既存現代説明文6siteへ元比率に比例配分。MDN15%固定。3ラウンド全体をRound 13のTHREE_ROUND_POLICY.jsonで学習前に凍結した。ジャンル構成の強さという一因子の対照で、原文数・新規文章の多様性は増やしていない。

通常/Glyph/文字境界40/30/30、8層dim192/heads4/hidden768/context256/dropout0.1、パラメータ4,655,808、独自語彙5,455/word merges512、原文とfold、seed2049、FP32/compileなし/CPU2、batch8、fresh AdamW/weight_decay0.05/clip1、lr最大0.00015/warmup250/cosine10000/最小15%、検証500ごと、共通3ビュー40/30/30の開発NLL/原UTF8 byteでの選択を固定。比率はサンプル行の確率で、原文文字数や厳密な勾配寄与の割合とは区別する。既存の原文・token streams・Tokenizerを読み取り専用で再利用した。

初期重み・Python/Torch RNG・全ビュー/siteの開発測定はRound 11と完全一致。データ完全性3テスト、SHA/親checkpoint、有限非ゼロ勾配（更新0）、各ジャンル/ビューの周辺確率を実行前に確認。policyとsource-manifestを途中変更していない。語彙/モデル大規模化、新しいseed/LR、外部重み/Tokenizer/生成API/他モデルの生成教師文は不使用。

## 実行数と保存state

実完了/予定=10000/10,000、採用step=10000、最新step=10,000。最新重み系譜49,000、採用系譜49000。兄弟3モデルの更新数を一つのモデルの系譜として足さない。全optimizer counter10,000、全weight/momentは有限FP32、RNG復元可、NumPy RNG不使用。中断・再開・破棄更新は0。

実target tokens=15,368,295、target UTF8 bytes=52,970,580、訓練checkpoint経過=5867.35秒。サンプラーのみを10,000回再生し、80,000行・末尾専用Python RNG・masked target token/byte数が一致。再生によるoptimizer更新0。実ビュー/site数はsampler-replay.json。処理token/byte量と長さbucket軌跡は比率変更で変わるため、等byte予算の対照や複数seedの再現性とは主張しない。

Checkpoint SHA: `3fb163d36b62ef7b05638534e6d53e5a62d2e99700dd8ada352a5b5371ed3719`

採用FP32 weights SHA: `f5f790492cecbdc1cf3c7fa8aea923a12704406b7ed0d141263ab1f8796a8c36`

model.js SHA: `23feef0ea8cd817f632f80443ca35a7006424f30315d600da6bb18fec0c73a63`

exportのmodelVersion日付文字列は既存exporterを引き継いだもので、実行日や重みの同一性を表さない。モデルは上記SHAと採用stepで識別する。

親checkpoint SHA: `9e29821c608a49e4aa2ac90619a84e574454390481c89f3e063e1e009ae62bc0`

## lossと全文生成を分けた評価

| 採用モデル | 通常 | Glyph | 文字境界 | 共通加重NLL/byte |
|---|---:|---:|---:|---:|
| Round 11/9500 | 0.960596083 | 0.995815504 | 0.986355983 | 0.978889879 |
| Round 15/10000 | 0.975855190 | 1.009704565 | 1.001175789 | 0.993606182 |

Round 11採用との共通指標差=+1.503%。全21回の検証/site別値とsampled batchのtrain lossをmetrics.json、train.log、loss-history.csv、training-loss-events.csvへ保存。混合ビューは同じ元文章の別符号化で独立の追加文章ではない。

| 指標（開発17件） | Round 11 | Round 15 |
|---|---:|---:|
| 初文合格 | 4 | 4 |
| 非ループ | 4 | 1 |
| 全文意味 | 0 | 0 |
| 有効token | 17 | 17 |

各モデルに同じ開発用17書き出し、全語彙greedy、max192 new tokens、真EOS停止、Python1スレッドを使用。無修正全文と全tokenを{old,new}-validation.json/JS JSONとFULL_GENERATIONS.mdへ保存。修正・検索・テンプレート・反復penaltyなし。Round 11の再生成全文は保存済み全文と17/17完全一致を確認した上で旧判定を引き継いだ。新モデルは全件を再読し、生成SHAに結合した理由を記録した。

expanded17/parent13/original9の各範囲、物語/現代説明の各群について、初文80%以上/非ループ90%以上/全文意味80%以上の既存ゲートを維持。合計9以上・grammar2・connection2・閉じた初文・有効tokenという初文条件も維持した。各scope/groupはcomparison.json/review.json参照。EOSだけで非ループや意味成立を認定していない。短い局所重複と長い観測同句反復、全文意味を分け、無限反復の数学的証明とはしない。

## 全件の判定と失敗

- `validation-aozora-00`: のぼりはじめましたの初文は自然。以後はおじさんを長く呼び続け、さんだけの文字列反復へ崩れる。人物関係・動作の意味が進まない。
- `validation-aozora-01`: 寒さを防ぐ動作・述語がなく、そのまま、いま、読点といいの文字列を長く反復する。主文が閉じない。
- `validation-aozora-02`: 葦が風のよくなってしまったは修飾・語順が不成立。後続は晩から三日の朝へ飛び、お茶の間にかから・かかるという語形と同句を長く反復する。
- `validation-mic-03`: eシールシールシールと開催を開催という重複、名称・行為・対象の混同が初文にある。後続はSecurity等の入れ子と以下の3つの3つを長く反復し、説明が閉じない。未知名だけを不合格の条件にはしない。
- `validation-mic-04`: 初文の市場規模は自然。後続は内訳と主要企業シェアの主題を重ね、携帯電話端末のシェアがシェアを伸ばすという関係に崩れる。最後はMicrosoftを長く反復する。
- `validation-env-05`: 活動に取り組む必要から産業構造の促進・創出、資源循環経済を目指す地域へ進むが述語を閉じず、地域の資源循環経済の実現を目指すという長い句を循環する。主文と修飾関係が定まらない。
- `validation-env-06`: 初文の構文は成立するが海岸保全施設の整備から海洋プラスチック対策の検討へ移り、整備との目的・接続が曖昧。法令の事実性だけを失敗条件にはしない。後続は2024年12月と法律・計画に基づきを長く重ね、主文が閉じない。
- `validation-jma-07`: お知らせるという活用、予想される避難の判断の修飾が不成立。初文内で発表された場合を三度重ね、後続も噴火警戒レベルを付して発表する句を循環する。
- `validation-jma-08`: 予測処理において、と速報版の発表を継続できることが未完成の並列でつながり、解析雨量の役割が不明。後続は引用が閉じず、気象解説情報という長い語句を繰り返して説明が進まない。省略主語だけを失敗の自動条件にはしない。
- `validation-mdn-new-00`: 初文はCSS関数とSVG文字列をつなぐ構文を維持する。指定するSVGプロパティの役割は曖昧なのでmeaning1、固定合計基準では初文合格。事実性は認定しない。後続は値の値とSVGの値がを再帰的に重ね、VRへ話題と構文が崩れる。
- `validation-mdn-new-01`: HTML要素のグローバル属性を指定できるという初文は自然。後続はCSSプロパティ・div・要素を混同し、要素を指定する要素を指定しますという文を長く循環する。
- `validation-mdn-new-02`: InterElement.gourmationの返却から別メソッド、IDB・IDBE・IDオブジェクトのメソッドへ返却対象が変わり、操作関係が定まらない。未知名だけを自動失敗条件にはしない。7文でEOSでもこのメソッドはオブジェクトのメソッドを返すという長い節が循環する。
- `validation-mdn-new-03`: ポリシーオブジェクトからSVGアプリケーション・APIを送信するへ役割が飛び、同じ句を初文から重ねる。後続もSVG APIを送信するのに便利という句とSVGの再帰で説明が崩れる。
- `validation-stat-new-00`: 企業のショッピング用ウェブサイトからCSSで使用するCSSを使うにはという再帰へ移り、助詞・態が不自然。CSSSの文字列と同句を長く反復する。
- `validation-stat-new-01`: 客観的な取組はデータとの名詞関係が不自然。後続では世論調査・統計学・統計の基礎資料を得ることができるという長い節を四度重ね、人物の人物を配分するという対象・行為が崩れる。3文でEOSでもこの観測反復を非ループとはしない。
- `validation-bunka-new-00`: 文化大臣の表面会合という名詞結合、プランを設立する目的語と動作、日本大臣にてはという助詞・修飾が不成立。後続の未知国名・会合名も関係が定まらない。日本大臣やフィリードにおいての一度の局所重複はあるが長い同一節の持続循環とは区別する。非ループでも全文意味は不合格。
- `validation-bunka-new-01`: 法律附則の説明で施策を講じられていますの助詞・態が不自然。後続は文化観光推進法に基づくを長く再帰的に重ね、施行令を実施という行為関係も崩れる。

手動判定はassistant・非blindで、独立人間評価ではない。未知固有名詞・省略された主語・技術説明の役割には判定の不確実性があり、独立再評価が必要。 unsupported factsは認定せず、事実不一致だけを言語意味失敗の自動条件にはしない。旧結果のSHAや閾値を変更して合格にしていない。

## 推論一致

Round 11のPython/JSは17/17、Round 15は17/17。新モデルの4書き出し最大logit誤差=9.53674316e-06、許容値2e-4は不変。厳格な終了値をparity-status.json、共通prefix分岐をnumerical-divergence.jsonへ保存。許容値内でも全文一致とは限らない。

丸め前採用FP32対7桁exportは17/17、最大参照差=1.54972076e-05。丸め前の全文もexport-rounding.jsonに保存。この有限probe以外への保証はしない。さらに古いRound 10のJMA08 near-tie分岐（16/17）はRound 11成果に無修正で保持している。凍結exportのversion文字列/既存日付ではなくmodel/policy SHAで今回の各モデルを識別する。

## 原因分析の補助

同じ固定TRAIN/開発サンプル（seed3132、通常BPE、共通7site最大32行/site）を使い、Round 12で保存・検証された行と親/Round 11の測定を再利用して、新モデルだけを測定した。新しい測定は選択に不使用、追加optimizer更新0。全TRAIN平均ではない。

| モデル | TRAIN | 開発 | 開発−TRAIN |
|---|---:|---:|---:|
| parentRound10 | 0.795346 | 1.018948 | 0.223602 |
| round11 | 0.767786 | 1.016398 | 0.248612 |
| round15 | 0.767774 | 1.033984 | 0.266210 |


既存原文約504万TRAIN文字・2,209文書のまま行比率を変えた対照なので、原文不足/新しいジャンルの多様性を解消したとは言えない。容量対照はなく4.66Mが唯一の原因とは断定しない。token境界/LR/optimizer/contextは共通で、その最適性も証明しない。有限sampleのgapや後半lossの微小変動だけで過学習を断定せず、単純な回数追加を成功の根拠にしない。数値一致と全文能力を分ける。3ラウンド全体の比較・8仮説の切り分け・次実験の推奨はRound 13/THREE_ROUND_RESULTS.mdへまとめる。

既存の短文共有56種、未閲覧ではない開発17件、単一seed・非blind判定の限界を継承。TESTはtoken化・生成・学習・選択に不使用。以前の作業でpolicy内の保存TEST参照が表示された履歴があるため、評価者がTEST全内容を未閲覧だとは主張しない。未見一般化は未実証。公開モデル交換/サイト回答変更/instruction tuningは行わない。

## 保存と再現

Python3.12.14、PyTorch2.14.1+cpu、NumPy2.3.5。checkpoint.ptに最新model/optimizer/RNG/history/beststate、checkpoint-0.ptに親重みとfresh optimizer、selected-weights.ptに採用FP32、model.jsに推論exportを保存。config/metrics/resultとartifact-manifest.jsonに実更新数・設定・入力/コード/成果SHAを記録。採用重みと最新optimizerを混ぜない。

`bash training/language/round15/execution/run.sh`が実行command。途中stateだけは同じcommandに--resumeを付けて正確に再開する。完了済みrunを上書き/再実行せず、新しい実験は新しいpolicy/runで固定する。3ラウンドの実行wrapperはRound 13/execution/run_three.shで、既存checkpointを勝手に再実行しない。

`verify_manifest.py`で保存成果を検証。`compare.sh`で再生成後、旧判定はrebind_old.pyで全文完全一致を要求する。新しいJSONの時刻/環境もSHAに含まれ得るため、今回だけのscore_new.pyを未来のモデル/別SHAへ流用せず再読・再判定する。sampler-replay、initial-equivalence、optimizer-audit、export-rounding、train-development-gapに各検証を保存した。元source-manifestは再凍結していない。
