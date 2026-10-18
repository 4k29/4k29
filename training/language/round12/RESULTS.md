# Round 12 結果 — 文字境界混合の一因子対照

**実10,000 optimizer更新を中断せず完了。全文意味はRound 11の0/17から0/17のまま。厳格な言語ゲートは不合格。** 初文合格は4/17→5/17、非ループは4/17→4/17。自然な日本語全文生成・未見一般化の改善は実証できなかった。公開モデル/Webサイトは変更していない。

## 実験と事前固定条件

前回RESULTS.mdの推奨に従い、TRAINの通常BPE/Glyph BPE/ランダム文字境界BPE比率だけを40/30/30→70/30/0へ変更した。完了したRound 11への単純な更新追加ではなく、**同じRound 10親の採用重み（系譜39,000）から始める兄弟対照**。これにより初期重みの変更と分割変更を同時に行わない。Round 11の元コード・データ・重み・評価結果を上書きしていない。

共通条件: 完全独自8層dim192/heads4/hidden768/context256/dropout0.1、4,655,808パラメータ、独自Glyph＋word BPE語彙5,455/merges512、原文と文書fold、seed2049、fresh AdamW/weight_decay0.05/clip1、batch8、CPU2スレッド、FP32/compileなし、lr最大0.00015、warmup250＋10,000更新cosine/下限15%、500更新ごとの検証。共通checkpoint選択は**通常/Glyph/文字境界=40/30/30の開発NLL/元UTF8 byte**の最小値。TRAIN側を変えても選択・生成条件・合格閾値は変えていない。

`policy.json`と`source-manifest.json`はoptimizer更新前に凍結。Round 11のprepared multiviewを読み取り専用で再利用し、原文/語彙/token streamを再作成しない。preparedデータの元policy SHAと今回の実験policy SHAを別々に結合した。TRAIN-only原文の利用条件と既存group分割を継承し、QA・他モデルの生成文・外部学習済み重み/Tokenizer/APIは不使用。

実行前に既存checkpointのない新規runを確認。Round 11成果115ファイルのSHA検証、既存データ完全性3テスト、今回の入力SHA/親checkpoint一致、全パラメータの有限かつ非ゼロ勾配（optimizer更新0）を確認した。更新前の3ビュー・全siteの開発測定はRound 11初期値と完全一致。サンプラーの周辺確率は通常0.7/Glyph0.3/文字境界0、ジャンル比率も不変 (`sampling-marginals.json`)。

## 実行と保存state

| 項目 | 実測 |
|---|---:|
| 予定/実完了optimizer更新 | 10,000 / **10,000** |
| 破棄・重複再実行更新 | 0 |
| 採用/最新step | **10,000 / 10,000** |
| 採用/最新重み系譜 | 49,000 / 49,000 |
| optimizer内部counter | 全パラメータ10,000 |
| 処理target tokens | 15,437,798 |
| 処理target UTF8 bytes | 54,537,810 |
| 訓練checkpoint経過秒 | 5723.48 |
| 最終exportまでの経過秒 | 5,728.90 |
| sampled rows | 80,000 |
| 通常/Glyph/文字境界実行rows | 56,089 / 23,911 / **0** |

Python3.12.14、PyTorch2.14.1+cpu、NumPy2.3.5、GPUなし。通常/Glyphの実行行割合は70.11125%/29.88875%（確率70/30の有限サンプル）。`sampler-replay.json`では全10,000回のdrawをforward/backwardなしで再生し、末尾Python RNG・target token/byte数をcheckpointと完全照合した。再生によるoptimizer更新は0。重み/AdamW momentsの有限FP32、RNG復元、初期親重みの一致、beststateと7桁丸めexportの全パラメータ一致を`optimizer-audit.json`に記録した。

Round 11も同じ10,000更新だが、target tokens15,422,254/bytes54,017,389だった。今回tokensは約0.10%、bytesは約0.96%多い。固定したのはoptimizer更新budgetで、等byte学習の対照ではない。分割混合変更で行選択・長さbucket・batch軌跡も変わる。この単一seed対照だけで普遍的因果効果や統計的有意性を主張しない。

checkpoint SHA: `1766ad1086170304e6b2e1bc25cc2a4bf37281f2f45b9da75b3d0310d84ca84b`
採用weights SHA: `079207f86b16c11acdda58e6457333ef9d58342222919bfc36fcdbe65ea0a5f8`
model.js SHA: `7970a0fb6cce936da0d0983e1fb56f3bf3f7f6d359cf67d192e318e5e9fdfa7e`
親checkpoint SHA: `9e29821c608a49e4aa2ac90619a84e574454390481c89f3e063e1e009ae62bc0`

## 開発loss

すべて過去に閲覧済みのdevelopmentであり、新しいTEST評価ではない。3ビューは同じ原文bytesの別符号化で独立した追加文章ではない。

| モデル/step | 通常BPE | Glyph | 文字境界 | 共通加重NLL/byte |
|---|---:|---:|---:|---:|
| 共通親/0 | 0.966512 | 1.351240 | 0.999763 | 1.091906 |
| Round 11採用/9500 | 0.960596 | 0.995816 | 0.986356 | **0.978890** |
| Round 12採用/10000 | **0.960240** | 0.999588 | 0.997570 | 0.983243 |

Round 12の共通指標は親から約9.95%改善する一方、Round 11採用より**約0.445%悪い**。通常BPEは約0.037%だけ良いが、Glyphは約0.379%、文字境界は約1.137%悪い。通常側を70%に増やした結果だけで全文能力改善とは判断しない。

通常BPEのsite別では、Round 11→12でMDN0.799942→0.797479、stat1.002071→1.000532が改善。一方aozora1.186049→1.187176、jma0.976719→0.977649、env0.792475→0.793581、mic0.829058→0.830803、bunka0.897013→0.901036は悪化した。局所的な損失改善が全ジャンルに広がったとは言えない。

全21回の検証と100更新ごとのsampled train lossを `loss-history.csv` / `training-loss-events.csv`、詳細site値を `metrics.json` / `train.log` に保存。sampled batchのtrain lossと全開発byte lossは同尺度のgapではない。

### 補助TRAIN/開発gap（採用後の診断、選択には不使用）

`diagnose_gap.py`はseed3132で通常BPEの共通7siteから最大32行/site/fold、各fold計211行を固定し、3モデルに同じ行を測定した。共有文書IDはなく、TESTは読まない。元ジャンル比率を共通siteへ正規化したbyte NLL:

| モデル | TRAINサンプル | 開発サンプル | 開発−TRAIN |
|---|---:|---:|---:|
| Round 10親 | 0.795346 | 1.018948 | 0.223602 |
| Round 11 | 0.767786 | 1.016398 | 0.248612 |
| Round 12 | 0.759721 | 1.017475 | 0.257754 |

TRAINはさらに下がるが、この開発サンプルではRound 11より悪化し、gapが広がった。訓練文章への適合と全文一般化の改善が同じではないという診断根拠になる。**全TRAIN lossではなく、行長・prefix分布も完全一致しない有限サンプル**。既存の短文共有56種の限界も残る。過学習・容量・ジャンル偏りの原因を単独で証明する測定ではない。

## 自己回帰全文評価

旧=Round 11採用step9500、新=Round 12採用step10000。両方同じ17書き出し、Python1スレッド、全語彙greedy/max192 new tokens/真EOS停止、修正・検索・テンプレート・反復penaltyなし。Round 11も再生成し、保存済み全文・全token・入力・EOS/validityの17/17一致を確認してから既存手動判定を引き継いだ。Round 12全17件は全文を読み直し、生成SHAに結合した判定理由を保存した。

| 開発17件 | Round 11 | Round 12 |
|---|---:|---:|
| 初文合格 | 4 | 5 |
| 非ループ | 4 | 4 |
| 意味の通る全文 | **0** | **0** |
| 有効token出力 | 17 | 17 |
| 厳格な言語ゲート | fail | fail |

expanded17: 4→5初文、parent13:4→4、original9:3→3。すべて全文意味0。物語初文1/3→2/3、現代説明文3/14→3/14。各範囲・各群の初文80%以上/非ループ90%以上/全文意味80%以上という既存ゲートを変更していない。

全文を省略せず `FULL_GENERATIONS.md` と `{old,new}-validation.json`/JS JSONに保存。全token ID・Unicode・prefixはJSONに保持。`{old,new}-manual.json` / `*-review.json` に構文・意味・接続・反復・breaksと全文判定の理由・SHAを保存。assistantの非blind手動判定で、独立人間評価ではない。

- **局所改善**: aozora-02の「葦が風のなかにかくれてしまった」は自然になったが、後続の「二人はもう一人」と村の村の反復で参照と意味が崩れる。bunka-new-01の初文は自然になったが、文化観光から締約国会議へ逸脱する。
- **局所悪化**: env-06はRound 11では自然な初文だったが、今回は「改正事業者の改正事業の改正」と法律名を重ね、主文が閉じない。
- **反復**: aozora-00のおじょうちゃんの所有関係、aozora-01の夜/夕方、mdn-new-00の配列の配列、stat-new-01の管理や管理/関係省庁と連携しつつが続く。
- **主述・修飾**: jma-07の「お知らせるおそれ」「旨を警戒を呼びかける範囲には」、jma-08の解析雨量が検討を行うという主述、bunka-new-00の参加を開催するという目的語・動作は不成立。
- **有限でも意味失敗**: mic-03、jma-08、mdn-new-02はEOSで短く止まるが、対象・動作・返却型が不明。Internationオブジェクトを返すことを自然な技術説明と認めない。
- **非EOSでも非ループ**: mic-04は短いMicrosoft反復・数値/対象の混同・末尾未完成があるが、長い同一節循環とは区別し非ループとした。非ループと全文意味を混同しない。EOSだけで分類していない。

出力のword token割合22.63%→20.68%、characters/token1.349→1.383 (`generation-granularity.json`)。分割変更後も局所補完はでき、Glyphだけになった/文字範囲が激減したという説明は支持されない。ただし17件の生成診断だけから原因は断定できない。

## 数値一致

Round 11/12ともPython/JavaScript全文**17/17一致**、最初の4書き出しの最大logit誤差は両方1.049042e-5（既存許容値2e-4不変）。厳格なJS evaluator終了値は旧0/新0。分岐診断のrowsは空で、出力修正やtie規則変更はしていない。

Round 12の丸め前採用FP32重み対7桁exportも**17/17一致**、最大参照logit差2.002716e-5。`export-rounding.json`に丸め前全文を保存した。これは有限probeの一致で、全入力への普遍的保証ではない。

本ラウンドの旧モデルはRound 11。さらに古いRound 10のjma-08は既知のPython/JS near-tie分岐（16/17一致、index75）があり、Round 11成果に無修正の全文・誤差・失敗statusを保持している。今回の17/17を、その既知の失敗が解消したという報告に置き換えない。凍結exporterのversion文字列は前回と同じ形式/既存日付を継承し、実験の同一性は上記model SHAとpolicy SHAで識別する。

## 原因の切り分けと次の推奨

| 仮説 | 今回の根拠と限界 | 次の判断 |
|---|---|---|
| 容量不足 | 4.66Mで全文意味0だが、容量対照なし。TRAINサンプルは下がり、開発gapは拡大 | 容量が唯一の原因とは言えない。大規模化を先に選ばない |
| 原文不足・偏り | 約504万TRAIN文字/2,209文書。原文文字はMDN約49.1%/Aozora約30.9%。ジャンルをまたぐ定型句混同が残る | 原文の重複/notice/現代日本語構成を監査し、利用条件を確認した人間の原文の構成だけを変える次実験を優先。実サンプラーはAozora45%/MDN15%なので原文文字比と勾配比を混同しない |
| トークン/文字境界 | cutsを外しても全文0。通常lossの改善は0.037%のみで共通lossは悪化 | 「文字境界混合を外せば解決」は支持されない。Round 11の40/30/30を次の基準とし、今回70/30/0を採用しない |
| LR/optimizer | counter/RNG/有限moments正常。両実験のoptimizer/LR同一 | 実装破損を示す証拠なし。最適性は未証明、LR対照は別の一因子実験として行う |
| context256 | 長い所有関係の循環だけでなく、初文・短EOSにも主述/意味不成立 | contextだけでは短文失敗を説明できない。延長を同時に追加しない |
| 不足/過学習 | 全10,000更新完了。TRAINサンプル適合が進む一方gap拡大・全文0。後半の共通lossはなお低下 | 単純な追加更新を成功の根拠にしない。有限gapだけで過学習とは断定しない |
| 推論誤差 | Python/JS/丸め前後17/17一致でも全文0 | 今回の失敗の主要説明として数値分岐は支持されない。Round 10既知分岐は保持 |
| 評価の欠陥 | exposed17件、assistant非blind、同じ開発指標で選択。有限seedとサンプル診断の限界 | 開発診断としてのみ報告し、全文SHA/閾値/全範囲を維持。独立・未見評価は未実施 |

**次はモデル・語彙・分割混合・optimizer・LR・contextを固定し、学習原文のジャンル構成だけを変える対照を推奨する。** 同じ初期checkpointと更新予算を使う対照を事前固定し、新規の人間の現代日本語原文の出典・利用条件・文書group分割を記録する。他モデル生成文を教師にしない。新しい親重みへの継続と原文変更を同時に行った場合、それを今回の純粋な原文対照と主張しない。今回、追加のRound 13訓練を実行したとは記録しない。

TESTはtoken化・生成・学習・選択に使っていない。以前Round 11作業でpolicy全体から保存済みTEST参照文が表示された履歴があるため、評価者がTEST全内容を未閲覧だとも主張しない。未見文章への一般化は未実証。ゲート不合格のためTEST生成・instruction tuning・公開モデル交換へ進まない。

## 再現と成果

環境: `torch==2.14.1+cpu`（公式CPU wheel index）、`numpy==2.3.5`。元のRound 11 preparedデータと親成果が必要。

```sh
python training/language/round12/execution/verify_manifest.py
python training/language/round11/test_preflight.py
python training/language/round12/execution/check_sampling.py
```

実行command: `bash training/language/round12/execution/run.sh`。完了済みrunは上書きしない。途中checkpointがある場合のみ同じcommandに `--resume` を付け、最新model/optimizer/torch RNG/専用Python RNGから正確に再開する。今回中断・再開はなく10,000更新を実行した。完了済みrunに更新を足す場合は別のprospective policy/runが必要。

`continue-10000/checkpoint.pt`: 最新step10000 model/optimizer/RNG/history/beststate。
`checkpoint-0.pt`: 親重み＋fresh optimizerの初期状態。
`selected-weights.pt` / `model.js`: 採用step10000の重み/推論export。
`config.json` / `metrics.json` / `result.json`: 設定・履歴・実完了数。
`execution/artifact-manifest.json`: 入力・コード・評価・重みのSHA/サイズ一覧。

評価再実行は `bash training/language/round12/execution/compare.sh`。その後 `rebind_old.py` はRound 11全文の完全一致を要求する。新しいJSONには時刻なども含まれるためSHAは変わり得る。`score_new.py`は今回の生成SHAに結合した手動記録で、別の生成/モデルへ無条件に流用しない。全文/条件の照合と再判定が必要。`diagnose_parity.py`/`check_export_rounding.py`/`replay_sampler.py`/`diagnose_gap.py`でそれぞれの診断を再現できる。凍結した元source-manifestは再凍結しない。

既存リポジトリのNodeテスト962/962、既存公開モデルの日本語チェック2580/2580、docs/app.js構文検査が通過。これは公開モデルの既存チェックで、Round 12の全文言語ゲート合格の証拠ではない。今回のデータ/サンプラー/勾配/optimizer/数値監査は上述の別記録で、検証commandと終了値を`execution/verification.json`に保存した。
