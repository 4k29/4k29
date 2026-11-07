# Round 13 結果 — 既存原文のジャンル構成対照

**実10,000 optimizer更新を完了。初文4/17、非ループ4/17、全文意味0/17。開発言語ゲート: False。** 公開モデル/Webサイトは変更していない。未見一般化は未実証。

## 事前固定した条件

Round 11を対照とし、同じRound 10採用親（系譜39,000）からの兄弟実験。TRAINジャンルのAozora行サンプル確率を45%→35%へ下げ、差分をMDN以外の既存現代説明文6siteへ元比率に比例配分。MDN15%固定。3ラウンド全体をRound 13のTHREE_ROUND_POLICY.jsonで学習前に凍結した。ジャンル構成の強さという一因子の対照で、原文数・新規文章の多様性は増やしていない。

通常/Glyph/文字境界40/30/30、8層dim192/heads4/hidden768/context256/dropout0.1、パラメータ4,655,808、独自語彙5,455/word merges512、原文とfold、seed2049、FP32/compileなし/CPU2、batch8、fresh AdamW/weight_decay0.05/clip1、lr最大0.00015/warmup250/cosine10000/最小15%、検証500ごと、共通3ビュー40/30/30の開発NLL/原UTF8 byteでの選択を固定。比率はサンプル行の確率で、原文文字数や厳密な勾配寄与の割合とは区別する。既存の原文・token streams・Tokenizerを読み取り専用で再利用した。

初期重み・Python/Torch RNG・全ビュー/siteの開発測定はRound 11と完全一致。データ完全性3テスト、SHA/親checkpoint、有限非ゼロ勾配（更新0）、各ジャンル/ビューの周辺確率を実行前に確認。policyとsource-manifestを途中変更していない。語彙/モデル大規模化、新しいseed/LR、外部重み/Tokenizer/生成API/他モデルの生成教師文は不使用。

## 実行数と保存state

実完了/予定=10000/10,000、採用step=10000、最新step=10,000。最新重み系譜49,000、採用系譜49000。兄弟3モデルの更新数を一つのモデルの系譜として足さない。全optimizer counter10,000、全weight/momentは有限FP32、RNG復元可、NumPy RNG不使用。中断・再開・破棄更新は0。

実target tokens=15,397,537、target UTF8 bytes=53,696,317、訓練checkpoint経過=5726.91秒。サンプラーのみを10,000回再生し、80,000行・末尾専用Python RNG・masked target token/byte数が一致。再生によるoptimizer更新0。実ビュー/site数はsampler-replay.json。処理token/byte量と長さbucket軌跡は比率変更で変わるため、等byte予算の対照や複数seedの再現性とは主張しない。

Checkpoint SHA: `a7a0dd2273b43f828ad4eb483a04ef8dd2dd36bc523b30d33ed07f92c3d6f819`

採用FP32 weights SHA: `6edf61af617b2be7791de21e39201be7767625ee68dc6f4bd3d68904a957ccdc`

model.js SHA: `0d300e70978c59e7ceaabb6133966f5f24b6d34c21b8084ddf2cace2f571df31`

exportのmodelVersion日付文字列は既存exporterを引き継いだもので、実行日や重みの同一性を表さない。モデルは上記SHAと採用stepで識別する。

親checkpoint SHA: `9e29821c608a49e4aa2ac90619a84e574454390481c89f3e063e1e009ae62bc0`

## lossと全文生成を分けた評価

| 採用モデル | 通常 | Glyph | 文字境界 | 共通加重NLL/byte |
|---|---:|---:|---:|---:|
| Round 11/9500 | 0.960596083 | 0.995815504 | 0.986355983 | 0.978889879 |
| Round 13/10000 | 0.963325888 | 0.998451258 | 0.988663843 | 0.981464886 |

Round 11採用との共通指標差=+0.263%。全21回の検証/site別値とsampled batchのtrain lossをmetrics.json、train.log、loss-history.csv、training-loss-events.csvへ保存。混合ビューは同じ元文章の別符号化で独立の追加文章ではない。

| 指標（開発17件） | Round 11 | Round 13 |
|---|---:|---:|
| 初文合格 | 4 | 4 |
| 非ループ | 4 | 4 |
| 全文意味 | 0 | 0 |
| 有効token | 17 | 17 |

各モデルに同じ開発用17書き出し、全語彙greedy、max192 new tokens、真EOS停止、Python1スレッドを使用。無修正全文と全tokenを{old,new}-validation.json/JS JSONとFULL_GENERATIONS.mdへ保存。修正・検索・テンプレート・反復penaltyなし。Round 11の再生成全文は保存済み全文と17/17完全一致を確認した上で旧判定を引き継いだ。新モデルは全件を再読し、生成SHAに結合した理由を記録した。

expanded17/parent13/original9の各範囲、物語/現代説明の各群について、初文80%以上/非ループ90%以上/全文意味80%以上の既存ゲートを維持。合計9以上・grammar2・connection2・閉じた初文・有効tokenという初文条件も維持した。各scope/groupはcomparison.json/review.json参照。EOSだけで非ループや意味成立を認定していない。短い局所重複と長い観測同句反復、全文意味を分け、無限反復の数学的証明とはしない。

## 全件の判定と失敗

- `validation-aozora-00`: 初文「のぼりはじめました」は自然。以降は虫からおい・おじさん・おじいさん・おかあさんへ飛び、所有関係と呼びかけを延々重ね、動作語形も崩れる。
- `validation-aozora-01`: 寒さを防ぐ動作・述語がなく、そのままを反復し、おおおという文字列とおかあさんの所有関係へ崩れる。閉じた初文も意味の進展もない。
- `validation-aozora-02`: 冒頭の隠れるという句の後、さっきのなかにかわらい・おまえてはいってという語形と修飾が不成立。後半はおかあさんの所有関係を延々反復する。
- `validation-mic-03`: eシールシンガポール計画・開催したeシールを策定・eシールシールを実施という対象と行為が不明。以後は日付と第1回会合を開催する句を繰り返し、会合と国会を混同する。
- `validation-mic-04`: 初文は自然。後続はコンテンツ市場の内訳を電話契約数とドルの差に結び、何の差か不明で単位が混同する。4文でEOS、同じ2024年の節を局所的に重ねるが、長い同一節の循環とは区別する。数値と図表の事実性は認定しない。
- `validation-env-05`: 循環分野の経済活動に関する国際協力という初文は自然。後続は我が国の我が国の・経済産業省におけるの重複、産業と省庁の修飾混同、いわゆっくという語形崩れと未完文がある。対象・節は変化し、長い同一節の循環とは分類しない。非EOSでも非ループと全文意味を区別する。
- `validation-env-06`: 目標に続けて海洋ごみ対策法と法律番号・に基づきを延々重ね、整備の主文が閉じない。法律や年を変えても文の意味は進展しない。
- `validation-jma-07`: 発生をお知らせると予想される避難をとるという活用・修飾・主述が不成立。後続で噴火警戒レベルを付してという長い同句を近接3回重ね、警報が警報・注意報を発表する関係も崩れる。観測範囲の反復としてloopとし、無限反復を数学的に証明したとはしない。
- `validation-jma-08`: 速報版の発表状況・浸水害と高解像度予報を未完成の並列でつなぎ、発表況を予測を発表という対象と助詞が不成立。解析雨量の解説・基準・分布・5段階分析の関係も不明。5文でEOS、短い語の重複はあるが長い同一節の循環ではない。
- `validation-mdn-new-00`: 初文は構文上成立するがCSSオブジェクトのプロパティという返却対象・関数との関係が曖昧。後続ではSVGプロパティを返すという同じ節を延々重ね、説明が進まない。事実の正しさだけを全文意味の尺度にはしない。
- `validation-mdn-new-01`: 初文はHTMLのグローバル属性という話題を自然な構文で維持する。定義と指定・保持との役割は曖昧なためmeaning1、固定合計基準では初文合格。後続は要素を指定できる・できないを混在させ、目的語と要素の再帰を延々繰り返す。
- `validation-mdn-new-02`: 複雑なInternateTormStreamToker等の識別子とIDBKeyRangeの操作関係が不明。後続はDOMElementやSetchの呼び出し、呼び出せるかの確認へ移り、説明対象・目的が定まらず末尾も未完。長い同一節循環はなく、DOMElementの節の一度の局所重複はnonloopとする。未知名詞だけを機械的に不合格にした自動判定ではない。
- `validation-mdn-new-03`: 信頼型オブジェクトの定義からSVGオブジェクトを参照してくださいという指示へ移り、ポリシーと参照・返却の関係が不明。以後はSVGオブジェクトを返す・メソッドを返すを延々反復する。
- `validation-stat-new-00`: 企業のオンラインショッピングからウェブサイトを提供するCSSリクエストという対象混同へ移り、同じ句とCSSSの文字列を反復する。主文が閉じない。
- `validation-stat-new-01`: 客観的な取組を進めに続けて説明のない件数を列挙し、品質管理から水質汚濁へ飛ぶ。同じ数値と水質汚濁に係るものが減少する句を長く反復し、文が閉じない。
- `validation-bunka-new-00`: 副大臣が表彰のための施策を開催したという目的語と動作が不自然。以後は日米首脳会談を繰り返し、会談を発出・会議を公表する動作関係と話題が崩れる。
- `validation-bunka-new-01`: この法附則の説明で施策を講じられていますは助詞・態の関係が不自然。以後は文化観光法に基づきを繰り返し、化学物質管理施設の観光推進へ話題が飛ぶ。

手動判定はassistant・非blindで、独立人間評価ではない。未知固有名詞・省略された主語・技術説明の役割には判定の不確実性があり、独立再評価が必要。 unsupported factsは認定せず、事実不一致だけを言語意味失敗の自動条件にはしない。旧結果のSHAや閾値を変更して合格にしていない。

## 推論一致

Round 11のPython/JSは17/17、Round 13は17/17。新モデルの4書き出し最大logit誤差=1.14440918e-05、許容値2e-4は不変。厳格な終了値をparity-status.json、共通prefix分岐をnumerical-divergence.jsonへ保存。許容値内でも全文一致とは限らない。

丸め前採用FP32対7桁exportは17/17、最大参照差=1.90138817e-05。丸め前の全文もexport-rounding.jsonに保存。この有限probe以外への保証はしない。さらに古いRound 10のJMA08 near-tie分岐（16/17）はRound 11成果に無修正で保持している。凍結exportのversion文字列/既存日付ではなくmodel/policy SHAで今回の各モデルを識別する。

## 原因分析の補助

同じ固定TRAIN/開発サンプル（seed3132、通常BPE、共通7site最大32行/site）を使い、Round 12で保存・検証された行と親/Round 11の測定を再利用して、新モデルだけを測定した。新しい測定は選択に不使用、追加optimizer更新0。全TRAIN平均ではない。

| モデル | TRAIN | 開発 | 開発−TRAIN |
|---|---:|---:|---:|
| parentRound10 | 0.795346 | 1.018948 | 0.223602 |
| round11 | 0.767786 | 1.016398 | 0.248612 |
| round13 | 0.769523 | 1.019577 | 0.250054 |


既存原文約504万TRAIN文字・2,209文書のまま行比率を変えた対照なので、原文不足/新しいジャンルの多様性を解消したとは言えない。容量対照はなく4.66Mが唯一の原因とは断定しない。token境界/LR/optimizer/contextは共通で、その最適性も証明しない。有限sampleのgapや後半lossの微小変動だけで過学習を断定せず、単純な回数追加を成功の根拠にしない。数値一致と全文能力を分ける。3ラウンド全体の比較・8仮説の切り分け・次実験の推奨はRound 13/THREE_ROUND_RESULTS.mdへまとめる。

既存の短文共有56種、未閲覧ではない開発17件、単一seed・非blind判定の限界を継承。TESTはtoken化・生成・学習・選択に不使用。以前の作業でpolicy内の保存TEST参照が表示された履歴があるため、評価者がTEST全内容を未閲覧だとは主張しない。未見一般化は未実証。公開モデル交換/サイト回答変更/instruction tuningは行わない。

## 保存と再現

Python3.12.14、PyTorch2.14.1+cpu、NumPy2.3.5。checkpoint.ptに最新model/optimizer/RNG/history/beststate、checkpoint-0.ptに親重みとfresh optimizer、selected-weights.ptに採用FP32、model.jsに推論exportを保存。config/metrics/resultとartifact-manifest.jsonに実更新数・設定・入力/コード/成果SHAを記録。採用重みと最新optimizerを混ぜない。

`bash training/language/round13/execution/run.sh`が実行command。途中stateだけは同じcommandに--resumeを付けて正確に再開する。完了済みrunを上書き/再実行せず、新しい実験は新しいpolicy/runで固定する。3ラウンドの実行wrapperはRound 13/execution/run_three.shで、既存checkpointを勝手に再実行しない。

`verify_manifest.py`で保存成果を検証。`compare.sh`で再生成後、旧判定はrebind_old.pyで全文完全一致を要求する。新しいJSONの時刻/環境もSHAに含まれ得るため、今回だけのscore_new.pyを未来のモデル/別SHAへ流用せず再読・再判定する。sampler-replay、initial-equivalence、optimizer-audit、export-rounding、train-development-gapに各検証を保存した。元source-manifestは再凍結していない。
