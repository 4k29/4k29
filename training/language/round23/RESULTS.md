# Round23 結果 — causal repeated-fourgram completion UL

実追加optimizer更新 **10000/10000**、全parameter optimizer counter[20000]、最新重み系譜59000。採用は追加step9500、採用重み系譜58500。elapsed 8845.59秒。

初期DEV NLL/byte 0.978919000749818 → 最良 **0.971455577147603**。事前閾値Round22 **0.971461170063259**、NLL成功条件=True。通常CEだけで選択し、ULをDEV指標へ加えない。40/30/30分割のweighted診断であり独立文章の確率や言語能力の証明ではない。

| 同条件の露出済みDEV17件 | Round22 CE | Round23 |
|---|---:|---:|
| 初文成立 | 6/17 | 6/17 |
| 非長期ループ | 4/17 | 4/17 |
| 全文意味成立 | 0/17 | 0/17 |
| 全言語ゲート | False | False |

## 単独変更と再現

科学的対照Round22と同じprepared TRAIN/validation/tokenizerを全SHA同一で再利用。新しい原文の取得・再分割は行わず、利用条件・出典・raw HTML・予約7文書・64文字重複監査はRound22とそのsource-manifestを参照。近似・言い換え重複なしの保証はしない。新TESTをencode/loss/生成に使用せず、17件は既存DEVで新TESTではない。

8層dim192/heads4/hidden768/context256/dropout.1/eps1e-5/4655808parameter、独自語彙5455、通常BPE40%/glyph30%/randomcuts30%、ジャンルmass、batch8、CPU2 FP32、LR2.2499999999999998e-5、wd.05/clip1、500更新検証を固定。同じRound11最新model/AdamW/Torch/private Python RNGから開始する兄弟対照で、Round22から追加更新を延長した実験ではない。best9500重みとlatest10000momentを混ぜない。

変更はCE+0.1×causal repeated-fourgram completion UL。位置tの既観測suffix3tokenと一致する過去trigramに続いたtokenを、直前64の既観測completion位置から集める。未来x[t+1:]を参照せず、一意化・非特殊ID>=6・現在gold除外・mask target除外を適用。-log(1-p)の候補和を有効target数で平均、p上限1-1e-6。正しい反復がgoldなら抑制しない。別モデルや自己生成を教師にしない。推論時のpenaltyや文章修正は使わない。

Round20/21の直前token全般へのULは必要な語を損なう可能性があり、NLL・全文意味を改善しなかった。Round22ではNLL改善と反復悪化が共存したため、4gram完成候補だけへ対象を絞った。teacher forcingの履歴だけを使うため自己生成後の分布外文脈や別表現の反復へ逃げる問題が残り得る。

実target 15,543,567token / 54,500,806bytes、対照と完全一致。初期weights/moment/RNG/全DEV、最終sampler Python RNG/Torch RNGも照合した。学習合成目的/CE/UL/候補数を100更新ごとに分記録し、100イベントでCE+0.1ULの一致と有限性を監査。全21検証点のpaired-ce-curve.csvを保存。1seedであり統計的有意差は示さない。

独立参照計算と勾配一致、因果性/正解/特殊/mask/履歴幅、極端確率/勾配方向/空候補、tiny optimizer/RNG完全再開の4テスト成功。実モデル全parameter有限非ゼロ勾配、親optimizer/RNG復元、全source hash、sampling40/30/30を更新前に検証した。

## 全生成と数値一致

FULL_GENERATIONS.mdとold/new-validation.jsonに同入力17件の全tokenと無加工全文を保存。greedy full vocabulary/max192/trueEOS/Python1thread固定。旧判断は生成全文・token・条件がRound22と一致した場合だけ継承し、過去ファイルを改変しない。新判断は全prefix+continuationの実読解をSHA結合し、文法・主述・修飾・文中意味・文間接続・途中崩壊・反復を理由付きで記録。未知固有名・APIの事実未確認だけでは失格にせず、仕様正確性も認定しない。独立盲検の人間採点ではない。

初文80%・非ループ90%・全文意味80%をexpanded17/parent13/original9とnarrative/contemporary groupsで要求する従来の全ゲートを変更しない。EOSや短さ、局所初文成立を全文意味と同一視しない。不確実な読みはevaluation-sensitivity.jsonに残す。

Python/JS完全列一致は旧17/17、新17/17。reference最大絶対差は旧9.53674316406e-06、新1.23977661133e-05。許容2e-4不変。丸め前FP32/7桁export比較はexport-rounding.json、全分岐はnumerical-divergence.json。Round10既知near-tieの16/17一致も保存し、一部の一致を全入力へ一般化しない。

生成4gram反復率 64.074074%→64.074074%、EOS 4→4、完全同一全文17件。補助的な事後指標で言語ゲートの代用ではない。

## 原因の切り分け

- 容量: 465万parameter固定で直接比較なし。容量不足は候補だが本実験だけで確定しない。
- データ: 対照と全bytes/exposure同一で今回の差を追加量に帰さない。政府・専門文中心の偏りと小規模性は残る。
- 局所適合: Round22追加TRAINのteacher-forced NLLは0.809066657→0.809051399。TRAIN指標を未見/自己回帰能力としない。
- 分割・文字境界: 同じ独自BPE/語彙と40/30/30、文字空白・語token比はgeneration-granularity.json。4gramのtoken単位と日本語の意味反復は一致しない可能性がある。
- LR/optimizer: 同じ親整合状態・LR・更新数。UL対象だけの変更であり最適LRは未比較。今回の疎な候補は大きな意味の誤り全般を直接教える損失ではない。
- context: 256固定。短い初文の主述の崩れと長い出力のループを別に評価し、context延長だけで解決すると断定しない。
- 学習不足/過学習: 固定された旧canonical TRAIN 0.754725106 /DEV 1.009662503、gap 0.254937397。追加原文/全TRAINを代表しない。全loss推移と自由生成の乖離を見て、単純な更新延長を自動選択しない。
- 数値誤差: 全文列・raw/丸めの実測を残す。対応する列が一致しても意味破綻があれば数値誤差だけでは説明できない。
- 評価: 露出済みDEV/1seed/assistant読解という限界。無加工全文・理由・感度分析を保存し、同じ初文や未知名への基準を勝手に変えない。

## 再開・保存

launch.jsonに凍結commitと起動PID/UTC。checkpoint-0.pt、checkpoint.ptに最新weights/AdamW/Torch/private Python RNG/実counter/history/exposureを保存し、selected-weights.ptは採用beststateを独立保存する。model.js、全loss CSV、設定・ソース/データSHA・生成全文・失敗理由を保存。persistent controllerがチャットと独立に学習→機械評価→PR保存を行い、MECHANICAL_STATUS.mdのmeaning pendingは当時の自動保存snapshot、本報告とreviewが後の最終判定。

完了したrunを再実行しない。未完了かつ稼働プロセスがない場合だけ `bash training/language/round23/execution/run.sh --resume`。予定数を実完了数へ転記せずcheckpointと全optimizer counterを監査。artifact-manifest.jsonのSHA/sizeはverify_manifest.pyで照合する。外部学習済みweights/tokenizer/API/教師文章なし。公開モデル・サイト変更なし。TEST生成なし。

## 個別の全文評価

- **validation-aozora-00**: 初文ののぼりはじめましたは自然。後続はおじさんを数十回呼び続けて意味が進まず、文が閉じない。
- **validation-aozora-01**: 寒さを防ぐために出て来たという初文は文法的には成立する。出る先が不明で目的との関係は弱いが、文脈にない外気へ出たと決めつけて失格にしない。後続はその夜の夜の夜を長く反復する。初文の接続には解釈差を別記する。
- **validation-aozora-02**: 葦が風のなかにかけていたという対象不足に加え、母が母にかかっていたという関係が初文から崩れる。後続も母の主語・対象が入れ替わり、最後は母の所有を長く再帰する。擬人化だけの失格ではない。
- **validation-mic-03**: 立ち上げた名称の引用が閉じず、Internationを長く反復する。未知英字名の存在ではなく文の未成立と反復を失敗理由にする。
- **validation-mic-04**: 初文は自然。後続はコンテンツ市場の内訳から電話契約へ移り、契約数を億円や百分率で表す対象・単位関係が崩れる。局所的な内訳・電話句の再利用はあるが長い周期ループとはしない。EOSだけでは全文合格にしない。
- **validation-env-05**: 初文内で地方公共団体等と連携しつつを五回反復するため初文も不合格。後続は脱炭素化促進の法律と地域の所有を再帰して閉じない。法の実在性だけの判断ではない。
- **validation-env-06**: 海洋ごみの海洋ごみという所有を重ね、海洋ごみの維持・再生可能エネルギー等の対象が崩れる。海域の利用と促進を長く再帰し、自然な文として閉じない。
- **validation-jma-07**: お知らせると予想される現象ののと初文から活用・修飾が崩れる。とるべき防災対応を三回ずつ列挙して意味が進まないが、文全体は変化し、長い同一周期ループとは区別する。噴火速報・警報・レベルの説明の関係もつながらない。
- **validation-jma-08**: 解析雨量という主題と速報版の発表状況や解析雨量の基準を満たしたものという述語がつながらない。後続の解析の解析や解説情報の解説への案内も局所再帰。短いEOS出力だが全文意味は不成立。
- **validation-mdn-new-00**: 関数がCSSパスをfalseに設定する初文は文法上成立し、API仕様の真偽は認定しない。後続はfont-fillプロパティの値が指定された場合を長く反復して閉じない。
- **validation-mdn-new-01**: 初文はグローバル属性を指定する自然な文。後続は要素が指定された要素に設定されている要素という修飾を何度も再帰する。EOSで止まっても対象関係と説明の進行が成立しない。未知要素名だけの失格ではない。
- **validation-mdn-new-02**: メソッドがInternationオブジェクトを返す初文の文法・対象は成立し、未知名だけを失格にしない。後続は同じメモと返却説明を繰り返し、最後は配列の単語列へ崩れる。
- **validation-mdn-new-03**: SVGオブジェクトをという目的語を二重に置くため初文の関係が不成立。後続もSVG要素の目的語と指定節を長く再帰する。
- **validation-stat-new-00**: ウェブサイトの所有を重ねたうえでHTML要素を提供・指定する句を多重に再帰する。後続も同じこの例ではから始まる文を長く反復し、統計の文脈からHTMLへ崩れる。EOSでも全文不合格。
- **validation-stat-new-01**: データなどの客観的な取組という修飾関係は旧と同様に不自然。後続は具体的な取組の自己説明から製造業の創出・所有の長い反復へ崩れる。
- **validation-bunka-new-00**: 表彰のための国際連携の下から再び協力強化のための国際連携の下へ重ね、初文は文法的だが冗長で対象・目的が弱い。後続は日中韓・日米国の関係が崩れて韓国を長く反復する。歴史的事実の未確認だけの判定ではない。
- **validation-bunka-new-01**: 施策を講じられていますという受身と目的語の関係が不自然で、前の法附則の話題だけでは敬語の主体も明確でない。後続は施設の推進の法律、認定及び認定を局所再帰し、地方公共団体が認定された地域の認定者へ対象が崩れる。長い同一周期ループとは区別するが全文意味は不成立。敬語解釈の不確実性を別記する。

## 結論と次の実験

NLLは対照より0.000005592916（約0.000576%）低いが、初文6/17、非長期ループ4/17、全文意味0/17、4gram反復64.0741%、EOS4件、全17全文が対照と完全同一。**実測NLLのごく小さい改善のみ、反復・全文意味の改善は未達**。全言語ゲート不合格、公開採用なし。20回のpost-update CEはいずれも対照より低いが、相関する同seedの時点であり20独立試行や統計的有意差ではない。

追加診断は独立プロセスで同じRound11初期weightsを固定し、TRAIN samplerの最初16batchでCE/UL勾配を別に測定。実験optimizer更新0、optimizer自体も未生成。UL/CE勾配norm中央値0.0253994366、係数0.1では0.00253994366（0.254%）。これは初期TRAIN診断だけで、後半や自己生成文脈へ一般化しない。勾配方向のcosineも全batch保存。measure_gradient_balance.pyは当初/tmpで実行した同じ計算をリポジトリ相対の入出力へ移した再現用script。

ユーザーの追加継続指示により、次のRound24は同じ4gram ULの係数だけ0.1→1.0とする。初期中央値でCEの約2.54%という適度な規模へ増やし、対象を広げず、同じデータ・親model/moment/RNG・LR・更新数・全ゲートを固定する。今回の17件同一と小さな勾配が根拠だが、抑制不足が原因だったという確証ではない。NLLや文法を損なう可能性も通常CE/全生成で検証する。新原文追加やモデル拡大を同時には行わない。

検査: objective4テスト、実モデル有限非ゼロ勾配、Node962/962、公開評価2580/2580、app構文成功。SHA/sizeはartifact-manifest.jsonとverify_manifest.pyで再確認。公開側検査は実験モデルの日本語合格を意味しない。
