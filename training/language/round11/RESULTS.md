# Round 11 — 実10,000更新完了、日本語全文ゲートは未合格

**訓練は予定の10,000 optimizer更新を実際に完了した。意味の通る全文は旧・新とも0/17件で、この問題の改善は実証できなかった。**
2026-10-12、保存step1,000から同一条件で更新1,001–10,000を継続し、正常終了した。
全AdamW counterは10,000、残り更新は0。途中で計画・LR・seed・精度・検証条件を変更していない。
加重開発NLL/byteの事前固定基準で選択された重みは**step9,500**。最新の重み/optimizer/RNGは**step10,000**として保存した。
最後の500更新も実行済みだが、選択重みには含まれない。巻き戻しや再実行をしたわけではない。
実験用採用重みの保存は公開回答モデルの採用を意味しない。公開モデル・Web挙動は変更していない。

以前の実1,000更新・中断評価はGit commit `d69389e8f93e6aeb70deb684d635787a947896a6`に保存されている。
この報告はその部分結果を上書きする**完了時の評価**であり、1,000更新を別途加算して11,000更新と数えない。
今回の再開後は運用上の途中停止を行わず、10,000更新の予定終了まで継続した。無人学習は残していない。

## 実行条件と確認

- 既存Round 11のprepare/train/initialization/batching/policy/source-manifestと準備済みデータを変更していない。
- Round 10採用重みから完全一致で初期化。親checkpoint SHA `9e29821c608a49e4aa2ac90619a84e574454390481c89f3e063e1e009ae62bc0`。
- 自作8層、dim192、heads4、hidden768、context256、dropout0.1、独自語彙5,455、4,655,808パラメータ。全パラメータを訓練。
- 通常BPE0.4、Glyph BPE0.3、固定ランダム8–24文字境界BPE0.3。3ビューは同じ原文を別のtoken列にしたもので、独立した文章を増やしていない。
- seed2049、batch8、threads2、LR上限0.00015、AdamW/weight_decay0.05、clip1.0、既存250更新warmup/10,000更新cosineスケジュール。500更新ごとの固定検証。
- optimizerを新規作成したのはstep0のみ。step500・1,000からの再開はmoment/counter/RNGを復元し、resetしていない。
- Round 11既存CLI既定のFP32、compileなしを更新前に固定。Round 10訓練のactivationはBF16だったため、跨Round差を分割だけの因果効果と断定しない。
- CPU2・GPUなし。Python3.12.14、PyTorch2.14.1+cpu、NumPy2.3.5。累積の訓練/固定検証時間はcheckpointで5,813.33秒（約96.89分）、export等を含む終端ログは5,818.66秒。停止区間の待ち時間は含まない。
- 事前3テスト・ソース固定テスト、全原文/全ターゲット復元、親重み一致、各ジャンル×ビューのsampling mass、全パラメータの有限非ゼロ勾配を確認。これらの確認はoptimizer更新0。

最新checkpoint SHA: `6637813862d68c2e9d291bf0ae4d0bc8ba2fc35e51c8c233d519517af1067f49`。
初期checkpoint SHA: `edb7861aea2d622e64195dc587a3c6d45bd647a16f89c02a7b589ec038f62fa9`。
採用step9,500の重みSHA: `139ff7ff4600ebc4c7cdb026a7bd159bca3558e1a2f00d5094dfe7e9e68c6c54`。
採用export SHA: `7f2f80dbed50892f943224367de819bc575a740b7414b3e7df007ddd43f546c7`。
選択重み系譜は39,000+9,500=48,500、最新重み系譜は39,000+10,000=49,000更新。全生涯の物理更新数ではない。

`execution/optimizer-audit.json` は全counter=10,000、全parameterのmoment、有限FP32重み/moment、
初期optimizer空、RNG復元、設定/ビュー固定、元のsource-manifest、exportとbeststateの対応を確認する。
NumPy乱数は使わず、訓練で使うPyTorch CPU RNGと専用Python sampler RNGを保存した。
`execution/resume-1000-verification.json` は再開前のSHA/counter、`inflight-midpoint.json`は訓練を止めない読み取り監査（実step5,200）を記録する。

`execution/sampler-replay.json`では、追加訓練なしで固定サンプラーを初期RNGから再現した。
80,000行のdraw後のPython RNGがcheckpointと完全一致し、実ターゲット15,422,254 token・54,017,389 UTF8 bytesも一致した。
この再現はforward/backward/optimizer更新を行っていない。

| ビュー | 実sampled行数 | 行の実割合 | 実ターゲットtoken | 実ターゲットbytes |
|---|---:|---:|---:|---:|
| 通常BPE | 31,958 | 39.9475% | 6,151,070 | 23,470,942 |
| Glyph BPE | 24,197 | 30.24625% | 4,633,201 | 13,245,185 |
| 文字境界BPE | 23,845 | 29.80625% | 4,637,983 | 17,301,262 |

40/30/30は固定sampling確率であり、有限回drawの実割合を予定値に書き換えていない。累積bytesも同じ原文の反復・別分割を含み、独立した原文量ではない。

## 開発loss — 言語能力とは別の測定

| 実step | 通常BPE NLL/byte | Glyph NLL/byte | 文字境界BPE NLL/byte | 0.4/0.3/0.3加重値 |
|---:|---:|---:|---:|---:|
| 0 | 0.966512 | 1.351240 | 0.999763 | 1.091906 |
| 1000 | 0.995598 | 1.064362 | 1.020057 | 1.023565 |
| 5000 | 0.974963 | 1.015847 | 1.000499 | 0.994889 |
| 9500（採用） | 0.960596 | 0.995816 | 0.986356 | 0.978890 |
| 10000（最新） | 0.960694 | 0.995751 | 0.986386 | 0.978919 |

採用重みは加重値10.35%、通常BPE0.61%、Glyph26.30%、文字境界BPE1.34%の低下。
改善の大部分はGlyphに由来する。序盤の通常/文字境界BPE悪化は後半で回復したが、日本語全文成功へは結び付かなかった。
この加重和は同じ原文の分割診断であり、独立した追加文章の確率や全token化経路を周辺化した文章確率ではない。
異なる分割のtoken perplexity同士を言語能力の比較に使わない。

通常BPEのaozora NLL/byteは1.186017→1.186049でほぼ不変、jmaは0.967681→0.976719へ悪化。
mdnは0.812468→0.799942へ低下。全体の小さな通常BPE改善を、各ジャンルの改善と混同しない。
全21検証点と各ビュー/site別測定は `continue-10000/metrics.json`、CSVは `execution/loss-history.csv`。
100更新ごとの実TRAIN batch lossは `execution/training-loss-events.csv`、実行ログは `train-0000-0500.log`、`train-0500-1000.log`、`train-1000-10000.log`。
TRAIN欄は最後のsampled batchのtoken lossで、全TRAIN平均や同じ難度のlossではない。
全TRAINと開発の同一尺度gapを測っていないため、過学習は未判定。
step10,000の加重値がstep9,500より約0.000029高いことだけで過学習とは判断しない。

## 無修正の自己回帰生成

旧はRound 10採用export、新は実10,000更新終了後に選択したstep9,500 export。
同じ17書き出し、greedy/full vocabulary、max192新token、EOS停止、Python1 threadで生成した。
反復penalty・出力修正・検索・テンプレート・teacher/API生成・外部学習済み重み/tokenizerは使っていない。
旧17件はprefix/text/token/EOS/validityが歴史的保存結果と全件一致したことを確認してから既存手動判定を再結合した。
新17件は全文を読んでassistantが手動判定した。独立・blindな人間評価ではない。

| モデル/範囲 | 初文合格 | 非ループ全文 | 意味の通る全文 | 言語ゲート |
|---|---:|---:|---:|---|
| 旧 expanded17 | 3/17 | 2/17 | 0/17 | false |
| 新 expanded17 | 4/17 | 4/17 | 0/17 | false |
| 旧 parent13 | 3/13 | 2/13 | 0/13 | false |
| 新 parent13 | 4/13 | 4/13 | 0/13 | false |
| 旧 original9 | 2/9 | 1/9 | 0/9 | false |
| 新 original9 | 3/9 | 4/9 | 0/9 | false |

narrative初文は0/3→1/3、modern初文は3/14→3/14。全文意味は両群とも0。
各範囲・各群で初文80%、非ループ90%、全文意味80%を必要とする既存ゲートは変更していない。
初文の各項目0–2点、合計9以上・grammar/connection各2・文の閉じ・valid tokenの条件も元のreview.pyをそのまま使用した。

新モデルの4非ループ出力はmic03/mic04/jma07/jma08の有限なEOS出力だが、全件が文法・意味・接続に失敗する。
局所的な冗長句を含む短い有限文と、同一節を延々重ねる循環を区別した。
EOSだけで非ループと判定していない。mdn-new-00/stat-new-01はEOSでも長い反復があるためループと判定した。

全文と全token IDは `execution/{old,new}-validation.json` とJS対応JSON、
無省略の比較は [FULL_GENERATIONS.md](execution/FULL_GENERATIONS.md)、
全件の判定理由とSHAは `execution/{old,new}-manual.json` / `*-review.json`。
`score_new.py`はこの生成SHAだけに結合した手動判定記録であり、未来のcheckpointへ流用できる自動採点器ではない。

主な失敗:

- `aozora-00`: 「のぼりはじめま」→「した。」は自然。しかしおじょうちゃん/おじさんの所有関係を連ね、虫の話を継続できない。
- `aozora-01/02`: 「いつものの」「もう一度もなくなってしまいました」を反復し、動作・参照・文間の接続が崩れる。
- `jma-07`: 「お知らせるおそれが著しく大きな噴石」「避難をとるべきとって」は活用・主述・修飾関係が不成立。EOSで止まっても自然な説明ではない。
- `jma-08`: 解析雨量が発表状況や基準を満たしたものだという不明な関係から参照指示へ移る。短い2文でも全文意味に失敗。
- `mdn-new-02`: インターフェイ→スの局所補完後、Formation/Format/PromissionやASCII点列へ崩れる。
- `stat-new-01/bunka-new-01`: 品質管理・文化観光から資源循環・化学物質管理へ話題が飛び、定型句を反復する。

1,000更新時点の188全角空白反復は採用step9,500では消えたが、意味のない所有関係の反復に変わった。
TRAIN原文の連続全角空白は最大12文字（8文字以上は7unit）であり、188文字列の丸写しではなかった。
`execution/train-space-diagnostic.json`は元のall-fold unitsファイルからTRAINだけを分析し、held textを統計・訓練・選択に使っていない。
`generation-granularity.json`では追加word token割合が20.25%→22.63%、出力characters/tokenが1.326→1.349。
単にGlyphしか生成しなくなった、または生成枠の文字範囲が大幅に短くなったという説明はこの17件では支持されない。
これらは診断であり、独立した因果証明ではない。架空数値・図表・技術名の事実性は認定しない。

これは既に閲覧された書き出し・旧validation文書の**開発診断**で、新しいTEST結果ではない。
未見文章への一般化は実証していない。TESTをtoken化・生成・学習・選択に使っていない。
ただし前回のgeneration-policy全体の確認で同ファイル内の保存済みTEST参照文がツール出力に表示された。
評価者がTEST内容を全く未閲覧だとは主張しない。言語ゲート不合格のためTEST生成・instruction tuningへ進まない。

## 推論の数値検証

| モデル | Python/JS全文一致 | 最初の4書き出しの最大logit誤差 | 2e-4参照許容値 |
|---|---:|---:|---|
| 旧 | 16/17 | 1.144409e-5 | pass |
| 新 採用step9500 | 17/17 | 1.049042e-5 | pass |

旧`validation-jma-08`はindex75で分岐する失敗を再現した。
今回の同一prefix上のPython「場合」と「１」の差は1.907349e-6、JSはtieで小さいIDを選ぶ。
歴史的Round 10記録の差9.536743e-7とは今回のPyTorch環境でわずかに異なるが、生成全文・分岐位置・選択tokenは再現した。
今回の共通prefix最大logit誤差は7.033348e-6。参照許容値内でも全文一致ではない。
`old-numerical-divergence.json` と共通prefixの全logitを保存し、元の厳格なJS evaluator終了statusは旧1、新0として残す。

正式比較は両言語が同じ7桁丸めexportを読む既存手順。
丸め前の採用FP32重みとexportも17/17全文一致、最初の4書き出しの最大logit差は2.574921e-5。
`execution/export-rounding.json` に無修正の全文・全tokenを保存した。
このprobe以外での普遍的数値一致を保証しない。出力やtie規則を修正してゲートを通したことにしていない。

## 原因の切り分けと次の実験

| 仮説 | 根拠と限界 | 分離する条件・測定 |
|---|---|---|
| 容量不足 | 4.66Mで主述・意味保持に失敗するが、サイズ対照がなく容量原因と断定できない | 同尺度TRAIN/開発gapや文長別の失敗を先に診断。今は大規模化しない |
| 原文不足/ジャンル偏り | 約504万文字・2,209 TRAIN文書。TRAIN文字のMDN約49.1%、Aozora約30.9%で約80%を占める。定型句の反復・分野をまたぐ混同が継続 | TRAINの定型notice/重複/ジャンルを監査。分割効果を分離後、モデル/語彙を固定し原文ジャンル構成だけ変える対照を優先 |
| 分割/文字境界 | Glyph NLLは26.30%改善、通常は0.61%、文字境界は1.34%。局所補完1件は改善しても全文0/17 | 同じ親重み/seed/FP32/optimizer/LRでrandomCharacterCutsだけを外す対照を事前固定。今回とRound 10の差を純粋な分割効果と断定しない |
| LR/optimizer | counter・RNG・momentは正常で全10,000更新実行。fresh optimizer/seed/activation精度がRound 10とは異なる | 分割対照で他条件を固定。LR変更は別実験で一因子だけ変更。有限lossだけでLR最適とは言わない |
| context256/lookback32 | 枠で途切れる例があるが、初文や早期の活用・主述にも失敗し、EOSで閉じた出力も意味不合格 | 文長/反復開始位置・長距離参照を診断。早期の失敗はcontext延長だけでは説明できない |
| 学習不足/過学習 | 予定の全更新を完了。開発値は後半も下がったが全文意味0。全TRAIN gap未測定 | 単純に同じrunの更新を足さない。末尾500更新の微小悪化だけで過学習とは言わない |
| 数値誤差 | 旧にnear-tie分岐、新は17/17一致なのに全文意味0 | 数値一致/言語能力を別に評価。旧分岐を隠さず、精度変更や出力修正で合格にしない |
| 評価の欠陥 | exposed17件、assistant判定・非blind、既存短文共有56種/定型noticeの限界。全文ゲートは初文/EOSだけの見かけ改善を拒否 | 判定SHA・全文・各範囲/群のゲートを維持。未見/独立評価は開発ゲート合格後に別途固定 |

**次の実験はrandomCharacterCuts混合比だけを変える対照を推奨する。**
TRAIN比率を通常/Glyph/文字境界=0.7/0.3/0.0とし、Glyph比率0.3は保つ。
共通のRound 10親、語彙、原文、分割fold、FP32/compileなし、seed、LR、batch、context、更新budget、
共通3ビューの開発選択指標（0.4/0.3/0.3）と厳格な生成条件を固定する。
これで「文字境界ビューを追加する効果」をGlyph効果から分ける。新しいrun/policyとして凍結し、完了済みRound 11を編集しない。
既存Round 10は初期点/seed/optimizer/精度も異なるため、この一因子対照の代用ではない。
これは効果を分離する別branchの提案であり、今回さらに訓練したとは記録しない。

対照で全文改善がないなら、次は原文ジャンル構成だけを変え、現代日本語の独立した人間の原文を増やす。
利用条件・source/group分割を固定し、他モデルの生成文章を使わない。モデル大規模化や同じrunへの単純な更新追加を先に選ばない。

## 保存・再現

リポジトリrootで環境をそろえ、保存成果を検証する（optimizer更新0）。

```sh
python -m pip install torch==2.14.1+cpu --index-url https://download.pytorch.org/whl/cpu
python -m pip install numpy==2.3.5
python training/language/round11/execution/verify_manifest.py
python training/language/round11/test_preflight.py
node --test tests/raw-language-round11-source.test.mjs
```

実行済みの再開commandは `bash training/language/round11/execution/resume.sh`。
同じ `--steps 10000 --seed 2049 --merges 512 --dim 192 --layers 8 --heads 4 --batch 8 --threads 2 --lr 0.00015 --validation-every 500 --precision float32 --run continue-10000 --resume`でstep1,001から進んだ。
完了済みなので今は再開不要。10,000更新を再現するために保存stateを上書きしたり、`--steps 9000`や新しいseedへ変えてはいけない。
過去の中断snapshotはpartialRunGitCommitから取り出せる。新しい継続実験は別のprospective policyが必要。

評価の再実行は `bash training/language/round11/execution/compare.sh`、数値分岐は `diagnose_parity.py`、
丸め影響は `check_export_rounding.py`、元のsamplerの再現は `replay_sampler.py`。
生成JSONの時間/環境情報もSHAに含むため、再生成後は過去の手動判定SHAを無条件に使わない。
全文/token/条件の一致を検証し、不一致なら再読・再判定してから `summarize.py` と `freeze_results.py` を更新する。

保存物:
`continue-10000/checkpoint.pt` は最新step10,000の重み・optimizer・RNG・historyと選択beststateを含む。
`checkpoint-0.pt` は新規optimizer空の初期状態、`selected-weights.pt`/`model.js` は採用step9,500、
`config.json`/`metrics.json`/`result.json` は条件・履歴・実完了数を含む。
採用step9,500の重みとstep10,000 optimizerを混ぜて再開してはいけない。
全成果と使用コード・データ・旧モデルのSHAは `execution/artifact-manifest.json`。
元のsource-manifestは結果を加えて再凍結せず、準備時の証拠として保持した。
