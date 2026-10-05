# 原文から日本語を学ぶ独自Transformer

本人QAより、日本語を安定して続けられることを先に検証する実験。既存の学習済み重み・モデル・トークナイザー・生成AI APIを使わない。自作byte-BPE、自作decoder、乱数初期化、原文のcausal next-token cross entropyだけを使う。PyTorchは数値計算・自動微分のための依存ライブラリ。既存の公開モデルは比較用として維持する。

**現状は言語段階の基準未達。** 原文10,000＋追加10,000更新は完了したが、最良の追加モデルの未見第一文は3/22合格で、安定した自然さには達していない。全件の出力と採点、損失、速度は [RESULTS.md](RESULTS.md)。この原文モデルを公開回答モデルへ置き換えず、QA追加学習も再開していない。

## 原文と分割

443文書、**2,914,006文字／8,457,912 UTF-8 bytes**。青空文庫の著作権が消滅した日本語原著168作品、MDN140、農林水産省115、気象庁20ページ。以前の生の原文80文書約23万文字から約12.5倍。著者・底本・入力者・校正者、利用条件・加工内容・URL・HTMLと本文のSHAを保存。[DATA-LICENSE.md](DATA-LICENSE.md) に利用条件を記載。全件の出典表示は `source-credits.json`。

青空文庫は「新字新仮名」だが古い文学の文体を含む。現代口語ばかりのコーパスではない。説明文と物語の生成を分けて評価する。Wikipedia・保護された作品・翻訳・生成AIの作成した文章・本人QAは含めない。

全文書を先にTRAIN354／VAL45／TEST44に固定。同作品の別版・長い段落の強い重複を連結し、438グループを分割。短い定型句の一致まで新規性を主張しない。TRAINとTESTの別文書に104文字の同一段落が1件残ることは `data-audit.json` に開示する。テストの生成書き出し22件はすべてTRAIN本文に存在しない。

初期の収集物に残ったMDNブラウザー互換性の共通案内文を、VAL生成を見て除去した。全MDNに同じ抽出規則を適用し、本文を補作文・修正文へ差し替えていない。文書分割とTEST22件の書き出しは維持。修正前の1,000更新と中断238更新は `abandoned-boilerplate/` に保管し、修正後の結果と混ぜない。

## トークナイザーと学習

TRAIN段落だけの約48万文字から独自byte-BPEを学習し、2,048／4,096 merges（語彙2,310／4,358）を比較。最大piece18 bytes。VAL・TESTを語彙作成に使わない。4096 merge規則の最初の2048を小語彙として使い、同じアルゴリズム・サンプルの比較にする。

本物の文書境界だけにBOS/EOSを入れ、context256・lookback32の連続windowで学習する。重なるlookbackはlossから除く。全文書の各バイトと本物の末尾EOSが一度だけ評価されることを、トークン列を復元して確認する。固定幅へ足したPADもlossから除く。

各語彙のpilotは同じdim128・3層・4heads・MLP512で1,000 optimizer更新。語彙選択は全文書VALのNLL／UTF-8 byteだけを使う。語彙間でtoken lossやtoken perplexityを直接比較しない。埋め込みのパラメーター数、文字で見たcontext長、更新中に見たバイト数も異なるため、語彙サイズ単独の効果と断定しない。

decoderはdim192・4層・4heads・MLP768、2,665,728パラメーターへ拡張した。元の重みの流用はせず乱数から学習し、原文だけを10,000 optimizer更新した。文書windowのsource samplingは文学50%、MDN35%、気象庁7.5%、農水省7.5%で、少ない現代説明文も学習に使う。合成文は作らない。全VAL本文のbyte正規化損失が最小のcheckpointを選び、TESTは選択に使わない。

## 再現と評価

必要環境はPython、PyTorch2.6.0、NumPy。図の再生成はMatplotlib3.10.8。GPU不要。使用環境は2CPU、8GiB、CPU計算。

```sh
python training/language/prepare.py
python training/language/audit_data.py
python training/language/train.py --merges 2048 --steps 1000 --run pilot-2048 --compile
python training/language/train.py --merges 4096 --steps 1000 --run pilot-4096 --compile
python training/language/choose_vocabulary.py
# vocabulary-choice.jsonのselectedMergesを指定する
python training/language/train.py --merges 4096 --steps 10000 --dim 192 --layers 4 --run raw-million --compile
python training/language/evaluate.py --model training/language/raw-million/model.js --partition test --likelihood --reference --out training/language/raw-million/test.json
node training/language/evaluate_js.mjs "$PWD/training/language/raw-million/model.js" training/language/raw-million/test.json training/language/raw-million/test-js.json
```

既存の凍結原文で再現する場合、ネットから再取得する必要はない。`collect_sources.py` の再取得は現在のサイト内容・取得日時を反映するため、元のSHAを再現する操作とは異なる。

各実行の設定・原文／分割／語彙SHA・乱数・PyTorch optimizerとRNG・実際の更新数・最良VAL時点・ログを保存。`--resume` は同じ設定・原文・語彙だけを受け入れる。原子置換checkpointと中断時保存で、実行していない更新を回数に足さない。

自由生成は `[BOS]+書き出し` を入力して全語彙のgreedyで128 tokens生成。QAの役割tokenを付けない。検索・テンプレート・固定回答・外部API・出力の文法修正・反復penaltyで補わない。最初の句点までの観察と全文出力を保存し、句点の後の反復も隠さない。停止はEOSまたはtoken/context上限。異常UTF-8と制御tokenも記録する。

文法・意味・接続・反復・破綻の5項目各0〜2を、明示した基準で全TEST生成に採点する。文法2、接続2、合計9以上、物語と説明文の各群で成功率80%以上、全文の非ループ率90%以上が段階1の合格条件。点検は実装者であるアシスタントによるもので、独立した人による盲検採点ではない。原文の正解続きを丸暗記して出すことは要求しない。

学習前に `generation-policy.json` へ書き出しと合格条件を固定している。損失低下・学習回数・パラメーター数の増加だけを、日本語生成の合格や対話性能向上とは扱わない。言語段階が合格するまでinstruction／QA学習は進めない。

今回の最終TEST結果を確認した後は、その22件を次の改善の開発診断として扱う。次に重み・語彙・学習データを改善する場合は、別の未見文書から新しい最終評価を学習前に固定する。同じ22件を繰り返して、未見の性能が向上したとは主張しない。

## 保持した既存実験

`../dialogue/owner-aligned-suspended/checkpoint.pt` は本人回答の追加実験の中断時点7,500更新（原文1,000、対話6,500）のoptimizer/RNGを保持する。選ばれた対話重みは7,000更新時点。未完了の11,000更新とは表示しない。既存の `switch-candidate.js` と公開サイト、過去の対話評価は保持して比較する。

実際の新しい学習結果と未見生成の採点は、実行完了後の `RESULTS.md` に記録する。`raw-million/learning-curves.svg` は実測VAL損失から作る図で、`figure-sources.json` に入力SHAを記録する。曲線を平滑化したり、損失を自然さの得点へ読み替えたりしない。

途中1,000更新の診断重みは `raw-million/validation-1000-model.js.gz` に保存。解凍したモデルSHA、独立したPyTorchの生成全文・token列、各生成の手動点検を残す。診断はVALのみであり、完了した10,000更新の結果とは区別する。

CPUのスレッド数・FP32/BF16も数値グラフの速度として試した。タイミング専用の重みは破棄し、本学習へ使っていない。実際のコンパイル後比較ではBF16が速くならなかったため、本学習はFP32を維持する。テスト生成や回答精度を使って精度・速度の設定を選んでいない。

## 追加の原文学習：段落と単語途中のつながり

全文書ストリームのVAL生成で、見出し・レイアウト空白・公式連絡先の反復と、BPEの単語途中からの接続の崩れが残った。既存の凍結ストリーム・重み・失敗結果は残し、次のraw-only実験を行った。原文全文と同じTRAIN／VAL／TEST文書分割を使い、元の完結した段落から40文字以上の文章を選ぶ。文章を修正・補完せず、レイアウト空白のみ除去し、見出し・連絡先・未閉鎖の引用を除外する。残る欄外案内115行は `residual-layout-audit.json` に開示する。

TRAIN13,447段落、元の約198万文字を使う。独自BPEのmergeを15%／30%の確率で省く固定の別表現も作り、単語の途中のpieceからの継続を学ぶ。語彙は再学習しない。別表現も完全に同じ原文バイトへ復元でき、3種類の表現を新しい文字数へ足さない。VAL／TESTはcanonical表現のみであり、別表現作成や重みの更新に使わない。

この実験のBOS／EOSは**元の完結した段落という文章単位**の始点・終点。長い段落は連続windowとmask付きlookbackを使い、文の途中にEOSを入れない。前の実験の全文書末尾EOSとは単位が異なるため、両実験のPPLを直接比較しない。

親は自分で乱数から原文のみ10,000更新したcheckpointのVAL最良重み。既存のQA／instructionモデルは親へ使わない。同じ自作語彙・構造・原文SHAを照合し、親の実行更新数・選択更新時点・SHAを記録する。AdamWは新しく初期化する。追加も原文のcausal next-tokenだけで10,000更新し、canonicalなVAL段落のbyte正規化損失で選ぶ。

入力長64／96／128／192／256のbucketで、短い文章に必要な計算を減らす。source／viewの重みは各bucketで利用可能な行に対する条件付きのsampling重みであり、全体の厳密な文字割合とは扱わない。検証用の書き出し9件と、最終22件・合格基準は維持する。追加学習の生成へ検索・固定回答・文法修正・外部APIを足さない。

```sh
python training/language/prepare_paragraphs.py
python training/language/train_paragraphs.py --merges 4096 --steps 10000 --dim 192 --layers 4 --batch 8 --threads 2 --seed 729 --lr 0.0003 --validation-every 500 --run paragraph-million --compile --own-initial-checkpoint "$PWD/training/language/raw-million/checkpoint.pt"
```

追加も10,000更新を完了し、VAL最良の9,500更新時点を採用した。実行結果・全未見生成は `paragraph-million/` と [RESULTS.md](RESULTS.md)。これはQA／instruction追加学習ではない。

最終のPyTorch評価は `--threads 1`（既定値）を使用する。2CPU上で複数の評価を同時に2threadsずつ実行すると、CPU quotaを取り合って遅くなったためであり、重み・評価問題・生成規則は変えていない。中断したログと一致確認は `evaluation-thread2-partial/`。最終の全22件は独立JavaScript実装とも全文・全tokenが一致する。

結果の再集計・図・ファイルSHAの再作成：

```sh
python training/language/plot_results.py
python training/language/build_report.py
python training/language/reproduce_manifest.py
```
