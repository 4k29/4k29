# Round 14 結果 — 既存原文のジャンル構成対照

**実10,000 optimizer更新を完了。初文5/17、非ループ2/17、全文意味0/17。開発言語ゲート: False。** 公開モデル/Webサイトは変更していない。未見一般化は未実証。

## 事前固定した条件

Round 11を対照とし、同じRound 10採用親（系譜39,000）からの兄弟実験。TRAINジャンルのAozora行サンプル確率を45%→25%へ下げ、差分をMDN以外の既存現代説明文6siteへ元比率に比例配分。MDN15%固定。3ラウンド全体をRound 13のTHREE_ROUND_POLICY.jsonで学習前に凍結した。ジャンル構成の強さという一因子の対照で、原文数・新規文章の多様性は増やしていない。

通常/Glyph/文字境界40/30/30、8層dim192/heads4/hidden768/context256/dropout0.1、パラメータ4,655,808、独自語彙5,455/word merges512、原文とfold、seed2049、FP32/compileなし/CPU2、batch8、fresh AdamW/weight_decay0.05/clip1、lr最大0.00015/warmup250/cosine10000/最小15%、検証500ごと、共通3ビュー40/30/30の開発NLL/原UTF8 byteでの選択を固定。比率はサンプル行の確率で、原文文字数や厳密な勾配寄与の割合とは区別する。既存の原文・token streams・Tokenizerを読み取り専用で再利用した。

初期重み・Python/Torch RNG・全ビュー/siteの開発測定はRound 11と完全一致。データ完全性3テスト、SHA/親checkpoint、有限非ゼロ勾配（更新0）、各ジャンル/ビューの周辺確率を実行前に確認。policyとsource-manifestを途中変更していない。語彙/モデル大規模化、新しいseed/LR、外部重み/Tokenizer/生成API/他モデルの生成教師文は不使用。

## 実行数と保存state

実完了/予定=10000/10,000、採用step=9500、最新step=10,000。最新重み系譜49,000、採用系譜48500。兄弟3モデルの更新数を一つのモデルの系譜として足さない。全optimizer counter10,000、全weight/momentは有限FP32、RNG復元可、NumPy RNG不使用。実行プロセス終了後、保存済みstep6400のoptimizer・RNGから同一条件で正確に再開。原因は未確認。ログは追記で保存。最終counterは保持した学習系譜の更新数を示す。停止直前の未保存・喪失更新の有無と回数は不明で、0とは推定していない。再開は保存step6400の次の更新から行った。resume-record.json参照。

実target tokens=15,477,748、target UTF8 bytes=53,693,230、訓練checkpoint経過=5913.32秒。サンプラーのみを10,000回再生し、80,000行・末尾専用Python RNG・masked target token/byte数が一致。再生によるoptimizer更新0。実ビュー/site数はsampler-replay.json。処理token/byte量と長さbucket軌跡は比率変更で変わるため、等byte予算の対照や複数seedの再現性とは主張しない。

Checkpoint SHA: `171fd9263aff4e81e604695736915ad679f63c1396c95fc4aa7ba91e4cccadaa`

採用FP32 weights SHA: `b279508804cb972f37b1711158d5d69f2359d4bcefd34d32b16342e583994563`

model.js SHA: `4d4dfdb6685101f5cc30fcb4f525d3e8351349433b4bc7297161a8804009fd47`

exportのmodelVersion日付文字列は既存exporterを引き継いだもので、実行日や重みの同一性を表さない。モデルは上記SHAと採用stepで識別する。

親checkpoint SHA: `9e29821c608a49e4aa2ac90619a84e574454390481c89f3e063e1e009ae62bc0`

## lossと全文生成を分けた評価

| 採用モデル | 通常 | Glyph | 文字境界 | 共通加重NLL/byte |
|---|---:|---:|---:|---:|
| Round 11/9500 | 0.960596083 | 0.995815504 | 0.986355983 | 0.978889879 |
| Round 14/9500 | 0.968617095 | 1.002504817 | 0.994192625 | 0.986456071 |

Round 11採用との共通指標差=+0.773%。全21回の検証/site別値とsampled batchのtrain lossをmetrics.json、train.log、loss-history.csv、training-loss-events.csvへ保存。混合ビューは同じ元文章の別符号化で独立の追加文章ではない。

| 指標（開発17件） | Round 11 | Round 14 |
|---|---:|---:|
| 初文合格 | 4 | 5 |
| 非ループ | 4 | 2 |
| 全文意味 | 0 | 0 |
| 有効token | 17 | 17 |

各モデルに同じ開発用17書き出し、全語彙greedy、max192 new tokens、真EOS停止、Python1スレッドを使用。無修正全文と全tokenを{old,new}-validation.json/JS JSONとFULL_GENERATIONS.mdへ保存。修正・検索・テンプレート・反復penaltyなし。Round 11の再生成全文は保存済み全文と17/17完全一致を確認した上で旧判定を引き継いだ。新モデルは全件を再読し、生成SHAに結合した理由を記録した。

expanded17/parent13/original9の各範囲、物語/現代説明の各群について、初文80%以上/非ループ90%以上/全文意味80%以上の既存ゲートを維持。合計9以上・grammar2・connection2・閉じた初文・有効tokenという初文条件も維持した。各scope/groupはcomparison.json/review.json参照。EOSだけで非ループや意味成立を認定していない。短い局所重複と長い観測同句反復、全文意味を分け、無限反復の数学的証明とはしない。

## 全件の判定と失敗

- `validation-aozora-00`: 初文ののぼりはじめましたは自然。以後はあんまりましたという語形崩れ、木の木のかいいという不明な修飾といまの木のかの反復へ崩れる。
- `validation-aozora-01`: 寒さを防ぐ動作や述語がない。そのままを繰り返した後、いつのつのつという文字列の長い反復に入り、文が閉じない。
- `validation-aozora-02`: 風の花をかけてみたいから主文につながらず、そこに来た・そこにはを混同する。いつも・いま・読点だけの長い反復へ崩れる。
- `validation-mic-03`: eシールの名称に続いてe-everyとハイフンを延々生成する。日本語の主文も引用の終わりもない。
- `validation-mic-04`: 初文は自然。後続はコンテンツ市場から携帯電話・ICT市場へ移り、出荷額とシェアを混同し出荷額を割合で表す。括弧・前年比較も崩れる。3文でEOS、内訳の一度の局所重複は長い同一節循環とは区別する。数値の事実性は認定しない。
- `validation-env-05`: 循環分野の経済活動に取り組む必要という初文は自然。後続は我が国の産業の産業、経済産業省の長い列挙、競争力の強化を図り込みという活用と主体の混同を繰り返し、末尾も崩れる。
- `validation-env-06`: 法の目標及び第10号の設定から大量の名詞列挙へ進み、海洋ごみ対策・海岸の水域等を反復する。閉じた文はあるが整備と目標・番号・水域ごみの関係が不明。後続もプラスチックごみについてを重ね未完。
- `validation-jma-07`: お知らせると予想される避難のあるかを期間に確認という活用・修飾が不成立。重要な噴石を運用する関係も崩れる。EOSでも噴火警戒レベルを付して運用の句が循環し、引用も閉じない。
- `validation-jma-08`: 速報版の発表状況を五段階に分けることと解析雨量・予測処理の関係が不明。後続では線状降水帯情報を列挙し、13時間・130分・10000分と10mの次元や助詞が混同する。同句やマップとして表示の節を繰り返す。
- `validation-mdn-new-00`: 初文はCSS関数とSVG文字列をつなぐ自然な構文。CSSで使用するかという判定の対象・役割が曖昧なのでmeaning1だが固定合計基準では初文合格。事実性は認定しない。後続はfalseの値の値とfont-sizeが指定された場合を長く反復し、主文が閉じない。
- `validation-mdn-new-01`: HTML要素のグローバル属性を指定できるという初文は自然。後続ではCSSプロパティと要素を混同し、要素を指定する要素を指定するという再帰や同句をEOSまで繰り返す。
- `validation-mdn-new-02`: IDBKeyRangeからInternationオブジェクトのメソッドを返すという説明対象・操作関係が定まらない。未知名だけを自動失敗条件にはせず、旧判定と同様の意味関係の不確実性を残す。以後は返却対象が変わり、配列の配列を返す文を延々反復する。
- `validation-mdn-new-03`: JavaScriptで使用するを初文内で三度重ね、ポリシーとURL返却の関係が不明。後続はこのメソッドを返しますとURLオブジェクトのメソッドを返すを循環し、説明が進まない。
- `validation-stat-new-00`: ウェブサイトのウェブサイトを提供するウェブサイトという再帰が一文全体に広がる。ワッキンググメントとの関係も不明。EOS一文でも長い同句反復があるので非ループとはしない。
- `validation-stat-new-01`: データなどの客観的な取組は名詞関係が不自然。後続は地方公共団体が保有する利用者が保有するなどという未完修飾と、何を誰が保有するかの混同がある。2文でEOS、統計調査の局所重複は長い同一節循環と区別する。
- `validation-bunka-new-00`: 表彰の施策を開催しましたは目的語と動作が不自然。後続は文化大臣から締約国会議へ飛び、COP番号と第1回会議・第1条を長く反復する。
- `validation-bunka-new-01`: 法律附則の説明で施策を講じられていますの助詞・態が不自然。後続は公布事業という関係不明の語と文化観光拠点施設の再帰、地域計画の整備を反復し、文章の意味が進まない。

手動判定はassistant・非blindで、独立人間評価ではない。未知固有名詞・省略された主語・技術説明の役割には判定の不確実性があり、独立再評価が必要。 unsupported factsは認定せず、事実不一致だけを言語意味失敗の自動条件にはしない。旧結果のSHAや閾値を変更して合格にしていない。

## 推論一致

Round 11のPython/JSは17/17、Round 14は17/17。新モデルの4書き出し最大logit誤差=1.04904175e-05、許容値2e-4は不変。厳格な終了値をparity-status.json、共通prefix分岐をnumerical-divergence.jsonへ保存。許容値内でも全文一致とは限らない。

丸め前採用FP32対7桁exportは17/17、最大参照差=1.83582306e-05。丸め前の全文もexport-rounding.jsonに保存。この有限probe以外への保証はしない。さらに古いRound 10のJMA08 near-tie分岐（16/17）はRound 11成果に無修正で保持している。凍結exportのversion文字列/既存日付ではなくmodel/policy SHAで今回の各モデルを識別する。

## 原因分析の補助

同じ固定TRAIN/開発サンプル（seed3132、通常BPE、共通7site最大32行/site）を使い、Round 12で保存・検証された行と親/Round 11の測定を再利用して、新モデルだけを測定した。新しい測定は選択に不使用、追加optimizer更新0。全TRAIN平均ではない。

| モデル | TRAIN | 開発 | 開発−TRAIN |
|---|---:|---:|---:|
| parentRound10 | 0.795346 | 1.018948 | 0.223602 |
| round11 | 0.767786 | 1.016398 | 0.248612 |
| round14 | 0.768885 | 1.026116 | 0.257231 |


既存原文約504万TRAIN文字・2,209文書のまま行比率を変えた対照なので、原文不足/新しいジャンルの多様性を解消したとは言えない。容量対照はなく4.66Mが唯一の原因とは断定しない。token境界/LR/optimizer/contextは共通で、その最適性も証明しない。有限sampleのgapや後半lossの微小変動だけで過学習を断定せず、単純な回数追加を成功の根拠にしない。数値一致と全文能力を分ける。3ラウンド全体の比較・8仮説の切り分け・次実験の推奨はRound 13/THREE_ROUND_RESULTS.mdへまとめる。

既存の短文共有56種、未閲覧ではない開発17件、単一seed・非blind判定の限界を継承。TESTはtoken化・生成・学習・選択に不使用。以前の作業でpolicy内の保存TEST参照が表示された履歴があるため、評価者がTEST全内容を未閲覧だとは主張しない。未見一般化は未実証。公開モデル交換/サイト回答変更/instruction tuningは行わない。

## 保存と再現

Python3.12.14、PyTorch2.14.1+cpu、NumPy2.3.5。checkpoint.ptに最新model/optimizer/RNG/history/beststate、checkpoint-0.ptに親重みとfresh optimizer、selected-weights.ptに採用FP32、model.jsに推論exportを保存。config/metrics/resultとartifact-manifest.jsonに実更新数・設定・入力/コード/成果SHAを記録。採用重みと最新optimizerを混ぜない。

`bash training/language/round14/execution/run.sh`が実行command。途中stateだけは同じcommandに--resumeを付けて正確に再開する。完了済みrunを上書き/再実行せず、新しい実験は新しいpolicy/runで固定する。3ラウンドの実行wrapperはRound 13/execution/run_three.shで、既存checkpointを勝手に再実行しない。

`verify_manifest.py`で保存成果を検証。`compare.sh`で再生成後、旧判定はrebind_old.pyで全文完全一致を要求する。新しいJSONの時刻/環境もSHAに含まれ得るため、今回だけのscore_new.pyを未来のモデル/別SHAへ流用せず再読・再判定する。sampler-replay、initial-equivalence、optimizer-audit、export-rounding、train-development-gapに各検証を保存した。元source-manifestは再凍結していない。
