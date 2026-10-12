# Round 11 — 実1,000更新の中断結果（10,000更新は未完了）

**自然な日本語生成の改善は実証できなかった。Round 11全体は未完了。**
2026-10-12、固定された10,000更新スケジュールの最初の1,000更新を実行した。
全AdamW counterは1,000。残り9,000更新を実行済みとは記録しない。
重み・moment・CPU PyTorch RNG・専用Python sampler RNGを保存し、500更新から同一設定で実際に再開した。
採用stepは加重開発NLL/byteだけで選んだ1,000であり、公開モデルの採用を意味しない。

CPU2・GPUなし。学習・検証のcheckpoint内実測時間は690.41秒、export等を含む終端ログは695.77秒。
最初の500更新の学習前/後検証込み約410秒、続く500更新は約286秒で、10,000更新には概ね1.5–2時間の継続CPU実行が見込まれる。
このセッションでは1,000で**運用上の安全中断**を選んだ。ハードウェア障害・強制時間切れを観測したわけではなく、10,000更新が実行不可能だと実証したわけでもない。
この成果を依頼全体の完了や10,000更新実験の最終結論として扱わない。無人学習は残していない。

## 実行した範囲と固定条件

- 既存Round 11のprepare/train/initialization/batching/policy/source-manifestを変更していない。既存の準備済みデータをそのまま使用。
- 自作Round 10採用checkpointから完全一致で初期化。親SHA `9e29821c608a49e4aa2ac90619a84e574454390481c89f3e063e1e009ae62bc0`。新規Round 11 checkpointは開始時になかった。
- 8層、dim192、heads4、hidden768、context256、dropout0.1、独自語彙5,455、4,655,808パラメータ。
- 通常BPE0.4、Glyph BPE0.3、8–24文字の固定ランダム境界BPE0.3。原文を増やした実験ではない。
- seed2049、batch8、threads2、LR上限0.00015、fresh AdamW、weight_decay0.05、clip1.0、既存250更新warmup/10,000更新cosineスケジュール。500更新ごとの固定検証。
- Round 11既存CLI既定のFP32、compileなしを最初の更新前に記録。途中変更なし。Round 10の訓練activationはBF16だったため、跨Round差を分割だけの因果効果と断定しない。
- Python3.12.14、PyTorch2.14.1+cpu、NumPy2.3.5。環境情報・CPU・SHAは `execution/preflight-runtime.json` と `execution/cpu.txt`。
- 事前3テスト、ソース固定テスト、全原文/ターゲット復元、親重み一致、各ジャンル×ビューのsampling mass、全パラメータの有限非ゼロ勾配を確認。検証はoptimizerを更新していない。
- NumPyはmemmap/配列処理だけで乱数を使わない。訓練で使用するPyTorch CPU RNGと専用Python RNGをcheckpointに保存。

最新checkpoint SHA: `6e7afeb834c9af8c44bbe5d1ea8994275828d1845d06c756b1631196ae5487ff`。
初期checkpoint SHA: `edb7861aea2d622e64195dc587a3c6d45bd647a16f89c02a7b589ec038f62fa9`。
選択済み重み系譜は39,000+1,000=40,000更新。これはプロジェクト全生涯の物理更新数ではない。
今回の1,000更新に巻き戻し・破棄はなく、500更新から正確に継続した。
`execution/optimizer-audit.json` が全counter、有限FP32重み/moment、初期optimizer空、RNG復元、exportとbeststateの対応を監査する。

## 開発loss — 言語能力とは別の測定

| 実step | 通常BPE NLL/byte | Glyph NLL/byte | 文字境界BPE NLL/byte | 0.4/0.3/0.3加重値 |
|---:|---:|---:|---:|---:|
| 0 | 0.966512 | 1.351240 | 0.999763 | 1.091906 |
| 500 | 0.994360 | 1.080771 | 1.018737 | 1.027596 |
| 1000 | 0.995598 | 1.064362 | 1.020057 | 1.023565 |

加重値は約6.26%低下したが、通常BPEは約3.01%悪化、文字境界BPEも約2.03%悪化。
Glyphの約21.23%改善が加重値を押し下げた。通常BPEの生成能力向上を表す値ではない。
各ビューは同じ原文bytesを別のtoken列で予測するため、この和を独立した追加文章の確率と解釈しない。
`continue-10000/metrics.json` に全ビュー・サイト別の測定、`execution/loss-history.csv` に検証推移、
`execution/training-loss-events.csv` に100更新ごとの実測sampled TRAIN batch lossを保存した。
TRAIN欄は最後のsampled batchのtoken lossであり、全TRAIN平均やビュー間で同じ難度のlossではない。
全TRAINと開発の同一尺度のgapを測っていないため、過学習の有無は未判定。

## 無修正の自己回帰生成

旧モデルはRound 10採用export、新モデルはRound 11採用step1,000 export。
同じ17書き出し、greedy/full vocabulary、max192新token、EOS停止、Python1 threadで生成した。
出力修正・反復penalty・検索・テンプレート・teacher/API生成・外部学習済み重み/tokenizerは使用していない。
旧17件は今回の環境でも歴史的保存結果とprefix/text/token/EOS/validityが全件一致したことを確認してから既存手動判定を再結合した。
新17件は全文を読んでassistantが手動判定した。独立・blindな人間評価ではない。

| モデル/範囲 | 初文合格 | 非ループ全文 | 意味の通る全文 | 言語ゲート |
|---|---:|---:|---:|---|
| 旧 expanded17 | 3/17 | 2/17 | 0/17 | false |
| 新 expanded17 | 3/17 | 1/17 | 0/17 | false |
| 旧 parent13 | 3/13 | 2/13 | 0/13 | false |
| 新 parent13 | 3/13 | 0/13 | 0/13 | false |
| 旧 original9 | 2/9 | 1/9 | 0/9 | false |
| 新 original9 | 2/9 | 0/9 | 0/9 | false |

narrative初文は0/3→1/3、modern初文は3/14→2/14。全文意味は両群とも0。
各範囲・各群の初文80%、非ループ90%、全文意味80%を必要とする既存ゲートは変更していない。
初文の各項目0–2点、合計9以上・grammar/connection各2・文の閉じ・valid token条件も元のreview.pyをそのまま使用した。

全文と全token IDは `execution/{old,new}-validation.json` とJS対応JSON、
読みやすい無省略の比較は [FULL_GENERATIONS.md](execution/FULL_GENERATIONS.md)、
全件の判定理由とSHAは `execution/{old,new}-manual.json` / `*-review.json`。
全角空白の列もJSONに原形のまま保存している。

主な失敗は以下の通り。

- `aozora-00`: 「のぼりはじめま」→「した。」の活用補完は改善。しかし以降は全角空白の反復で物語が進まない。短い初文成功は全文成功ではない。
- `aozora-01/02`: 「そのまま」・読点を反復。「かんとんぼり」など意味不明の語、ぼく→私の突然の転換もある。
- `jma-07/08`: 「お知らせるおそれのある避難の判断」や「解析雨量は…ご覧ください」で活用・修飾・主述関係が崩れる。
- `mdn-new-00/02`: CS→CSS、インターフェイ→スなど局所補完はできても、CSS/DOM/配列を返す同じ命題の循環に入る。
- `stat-new-01`: EOSで一文が閉じるが、「客観的な管理や管理のための適切な管理のため」は意味が成立しない。非ループでも全文不合格。
- `bunka-new-01`: 文化観光法から化学物質管理法へ話題が飛び、法に基づきの句を反復する。日付・数値・架空技術名の事実性も認定しない。

これは既に閲覧された書き出し・旧validation文書による**開発診断**であり、新しいTEST結果ではない。
新規未見文章への一般化は実証していない。TESTをtoken化・生成・学習・選択に使っていない。
ただし今回のgeneration-policy全体の確認時、同ファイル内の保存済みTEST参照文もツール出力へ表示された。
評価者がTEST内容を全く見ていないという主張はしない。これをTEST測定とは扱わず、未見能力の主張には合格後の別途固定した新しい評価が必要。

## 推論の数値検証

| モデル | Python/JS全文一致 | 最初の4書き出しの最大logit誤差 | 2e-4参照許容値 |
|---|---:|---:|---|
| 旧 | 16/17 | 1.144409e-5 | pass |
| 新 step1000 | 17/17 | 8.583069e-6 | pass |

旧`validation-jma-08`はindex75で分岐する既知の失敗を再現した。
今回の同一prefix上のPython「場合」と「１」の差は1.907349e-6、JSではtieとなり小さいIDを選ぶ。
歴史的Round 10記録の差9.536743e-7とは今回のPyTorch環境でわずかに異なるが、生成全文と分岐位置・選択tokenは再現した。
今回の共通prefixの最大logit誤差は7.033348e-6。
`execution/old-numerical-divergence.json` に共通prefixの全logit、候補・差・誤差の参照を保存。
元の厳格なJS evaluatorの終了statusは旧1、新0。許容誤差内だから完全一致だと扱わない。
新17件で一致しても全入力の普遍的な一致を保証しない。

両言語の正式比較は同じ7桁丸めexport重みを読む既存手順。
丸め前の採用FP32 checkpointとの追加比較は `execution/export-rounding.json` に無修正の全文と全tokenを保存する。
丸め前FP32と丸めexportの全文も17/17一致し、最初の4書き出しの最大logit差は1.621247e-5だった。
この限られたprobe以外の丸め不変性は主張しない。公開推論・重み・Webの挙動は変更しない。

## 原因の切り分けと次の順序

| 仮説 | 今回/既存の根拠と限界 | 次に分離する測定・条件 |
|---|---|---|
| 容量不足 | 4.66Mパラメータで主述・長い意味が弱い。ただしサイズ対照がなく容量原因と断定できない | まず既定実験を完了し、同尺度TRAIN/開発gapと文長別の失敗を測る。現時点で大規模化しない |
| 原文量/ジャンル偏り | TRAINは約504万文字・2,209文書。3ビューは同じ原文。旧Round 10はaozora NLLがmodernより高く、定型句の反復も継続 | 凍結実験後、既存TRAINの定型句/ジャンル分布を監査。新実験では原文の分布だけを変え、モデル/語彙を固定 |
| 分割/文字境界 | Glyph NLLは大きく改善したが通常/文字境界BPEは悪化。局所活用補完は1例改善しても全文0/17 | 完了後、同じseed/optimizer/FP32/LRで通常BPEのみの対照を事前固定。今回とRound 10の差を分割の純粋効果と断定しない |
| LR/optimizer | 親とはfresh AdamW/seed/精度が異なる。有限loss・勾配・moment・counterは正常だが、LR適否は未判定 | 現runの途中でLRを変更しない。完了後に必要ならLRだけの対照。通常BPE悪化を即optimizerの不具合とは扱わない |
| context256 | 一部は枠で途切れるが、初文・空白反復も早期に失敗する。context不足だけでは説明できない。Glyphは同じtoken枠で原文の文字範囲が短くなる | 固定長の文長/ループ開始位置を診断。より長いcontextを選ぶのは、遠距離失敗を示した後の別実験 |
| 学習不足/過学習 | 予定の10%のみ。加重開発値はstep1000でも下がるが、通常BPEは悪化し、全TRAIN gap未測定 | 次の最優先は保存checkpointから残り9,000を**既定計画どおり**再開すること。新しい追加更新数の提案ではない。部分結果を全10,000の否定/成功と扱わない |
| 数値誤差 | 旧にnear-tie分岐、新17件は一致するのに全文意味0/17。少なくとも今回の失敗全部をJS誤差では説明できない | tie分岐は失敗として保存。精度変更・出力修正でゲートを通したことにしない |
| 評価の欠陥 | exposed17件、assistant判定、非blind、短い共有文/定型noticeなど既存corpusの限界。初文やlossだけでは見逃す反復を全文ゲートが検出 | 判定SHA・全文・各群ゲートを維持。開発ゲート合格後に新規未見/独立評価を固定。今はTESTやinstruction tuningへ進まない |

**次の実行は既定Round 11の正確な再開。** その前にモデル大規模化、データ変更、LR変更、追加の新しい更新計画は選ばない。
残りを終えた後の分割対照で、canonical劣化がmultiviewに起因するかを調べる。

## 再開・再現

リポジトリrootで、環境を同じversionにそろえる。

```sh
python -m pip install torch==2.14.1+cpu --index-url https://download.pytorch.org/whl/cpu
python -m pip install numpy==2.3.5
python training/language/round11/test_preflight.py
node --test tests/raw-language-round11-source.test.mjs
python training/language/round11/execution/verify_runtime.py
python training/language/round11/execution/verify_manifest.py
bash training/language/round11/execution/resume.sh
```

`resume.sh` は元と同じ `--steps 10000 --seed 2049 --merges 512 --dim 192 --layers 8 --heads 4 --batch 8 --threads 2 --lr 0.00015 --validation-every 500 --precision float32 --run continue-10000 --resume` を使用。
開始位置は保存step1,000で、次はoptimizer update1,001。`--steps 9000`に変更しない。
短い監視区間なら `bash .../resume.sh --pause-after 1500`（絶対step）を指定できる。
SIGINT/SIGTERMも既存trainerが次の安全な更新境界で受けてatomic保存する。
再開時はtrainerがsource/data/config/settings完全一致を検証し、optimizerとRNGを復元する。初期化やoptimizer resetで再開しない。

評価の再実行は `bash training/language/round11/execution/compare.sh`。
このスクリプトは旧JS失敗statusも別に保存して、新の結果を消さない。
生成JSONの時間/環境情報もSHAに含まれるため、再生成後は過去の手動判定SHAを無条件に再利用してはいけない。
`score_new.py` の判定はこのstep1,000の出力専用で、未来のcheckpointの自動採点器ではない。
新しい出力の全文を再読し、判定・比較・manifestを更新する。

保存物: `continue-10000/checkpoint.pt`（最新重み/optimizer/RNG/history）、`checkpoint-0.pt`、
`selected-weights.pt`（選択重み）、`model.js`（実験用推論export）、`config.json`、`metrics.json`、`result.json`。
全成果と使用したコード・データ・旧モデルのSHAは `execution/artifact-manifest.json`。
元のsource-manifestは結果を加えて再凍結せず、準備時の固定証拠として保持した。
