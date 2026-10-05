# 原文から日本語を学ぶ独自Transformer

本人QAより、日本語を安定して続けられることを先に検証する実験。既存の学習済み重み・モデル・トークナイザー・生成AI APIを使わない。自作byte-BPE、自作decoder、乱数初期化、原文のcausal next-token cross entropyだけを使う。PyTorchは数値計算・自動微分のための依存ライブラリ。既存の公開モデルは比較用として維持する。

## 原文と分割

443文書、**2,914,006文字／8,457,912 UTF-8 bytes**。青空文庫の著作権が消滅した日本語原著168作品、MDN140、農林水産省115、気象庁20ページ。以前の生の原文80文書約23万文字から約12.5倍。著者・底本・入力者・校正者、利用条件・加工内容・URL・HTMLと本文のSHAを保存。[DATA-LICENSE.md](DATA-LICENSE.md) に利用条件を記載。全件の出典表示は `source-credits.json`。

青空文庫は「新字新仮名」だが古い文学の文体を含む。現代口語ばかりのコーパスではない。説明文と物語の生成を分けて評価する。Wikipedia・保護された作品・翻訳・生成AIの作成した文章・本人QAは含めない。

全文書を先にTRAIN354／VAL45／TEST44に固定。同作品の別版・長い段落の強い重複を連結し、438グループを分割。短い定型句の一致まで新規性を主張しない。TRAINとTESTの別文書に104文字の同一段落が1件残ることは `data-audit.json` に開示する。テストの生成書き出し22件はすべてTRAIN本文に存在しない。

初期の収集物に残ったMDNブラウザー互換性の共通案内文を、VAL生成を見て除去した。全MDNに同じ抽出規則を適用し、本文を補作文・修正文へ差し替えていない。文書分割とTEST22件の書き出しは維持。修正前の1,000更新と中断238更新は `abandoned-boilerplate/` に保管し、修正後の結果と混ぜない。

## トークナイザーと学習

TRAIN段落だけの約48万文字から独自byte-BPEを学習し、2,048／4,096 merges（語彙2,310／4,358）を比較。最大piece18 bytes。VAL・TESTを語彙作成に使わない。4096 merge規則の最初の2048を小語彙として使い、同じアルゴリズム・サンプルの比較にする。

本物の文書境界だけにBOS/EOSを入れ、context256・lookback32の連続windowで学習する。重なるlookbackはlossから除く。全文書の各バイトと本物の末尾EOSが一度だけ評価されることを、トークン列を復元して確認する。固定幅へ足したPADもlossから除く。

各語彙のpilotは同じdim128・3層・4heads・MLP512で1,000 optimizer更新。語彙選択は全文書VALのNLL／UTF-8 byteだけを使う。語彙間でtoken lossやtoken perplexityを直接比較しない。埋め込みのパラメーター数、文字で見たcontext長、更新中に見たバイト数も異なるため、語彙サイズ単独の効果と断定しない。

次のdecoderはdim192・4層・4heads・MLP768、数百万パラメーターへ拡張する。元の重みの流用はせず乱数から学習する。原文だけを10,000 optimizer更新する。文書windowのsource samplingは文学50%、MDN35%、気象庁7.5%、農水省7.5%で、少ない現代説明文も学習に使う。合成文は作らない。全VAL本文のbyte正規化損失が最小のcheckpointを選び、TESTは選択に使わない。

## 再現と評価

必要環境はPython、PyTorch2.6.0、NumPy。GPU不要。使用環境は2CPU、8GiB、CPU計算。

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

## 保持した既存実験

`../dialogue/owner-aligned-suspended/checkpoint.pt` は本人回答の追加実験の中断時点7,500更新（原文1,000、対話6,500）のoptimizer/RNGを保持する。選ばれた対話重みは7,000更新時点。未完了の11,000更新とは表示しない。既存の `switch-candidate.js` と公開サイト、過去の対話評価は保持して比較する。

実際の新しい学習結果と未見生成の採点は、実行完了後の `RESULTS.md` に記録する。
