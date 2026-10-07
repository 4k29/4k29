# 原文の短い台詞と文脈を残す日本語学習

過去のround2は未見24件中3件しか一文の文法・意味・接続の基準を満たさず、日本語段階を達成していない。その実物と採点は変更せず、原文の扱いと新しい乱数初期化モデルを実験する。QA／instruction、Wikipedia、teacher文章、既成Tokenizer、外部学習済み重み・生成APIは使わない。

気象庁から利用条件を確認して78文書、94,513文字、276,910 UTF-8 bytesの説明文を追加した。出典・取得・加工・本文SHA・HTML SHA・利用条件を `weather-sources.json` と `weather-credits.json` に保存する。出典：気象庁ホームページの各URL。公共データ利用規約（第1.0版）に沿って本文段落を加工して作成し、気象庁が作成・承認したモデルではない。FAQの質問見出しやQAラベルを付けず、元の説明本文の完全なp段落を保存する。元の原文と個別の出典は各文書から確認できる。

青空文庫の新規取得は、利用条件ページがproxy tunnel 502、indexと作品ページが403で失敗した。アクセス制限を回避せず、新規作品は0件。失敗と試行時コードSHAを `literature-source-failure.json` に記録する。既存の許諾付き文学は、以前に保存した原文と利用条件の実物を使う。既存全1,014文書の出典・利用条件はround2と親ディレクトリのライセンス・source-creditsを保持する。

全原文は1,092文書、4,285,032文字。以前の40文字未満の段落を落とす処理では短い台詞が除かれていたので、原文の連続した行を512文字以上かつ引用・括弧・文が閉じた時点まで蓄積する。最終の短い完全な連結も保持する。単語・改行・元の表記を作り直さず、スキップした見出しや連絡先を越えて文章をつながない。原文の連続した部分とbyte単位で一致することをテストする。TRAINでは短い台詞4,038段落を保持する。同じ原文を新しい語彙で表現したもので、独立した新規作品数として数えない。

80文字以上の段落が一つでも一致する文書と同じ作品名をグループ化する。以前の分割で複数partitionにまたがっていたMDN2文書は今回のモデルから隔離し、原文と過去の実験は残す。以前のVAL/TESTは損失全体も既に測定したので、プローブ以外の文書も開発用へ回す。新しい検証・TESTは以前のTRAINの文書グループから退役させ、新規気象庁のグループも分割する。このため、以前のモデル重み・Tokenizerは新しいheldへ露出している。今回へ読み込むことも未見baselineと扱うことも禁止し、新しいTRAINだけからTokenizerを学習しモデルは乱数初期化する。過去の原文・分割・206ファイルとround2の145ファイルは変更しない。

分割はTRAIN748文書、VAL67、TEST73、開発用202、隔離2。新しいTRAINは4,498連結単位、2,702,074文字、7,801,819 bytes。新規VAL9件・TEST24件をBPE学習前に固定し、前の生成評価文書と現在のTRAINのprefixを除く。TESTは文学8、情報通信6、環境6、気象4。文字の途中の書き出しも含む。文法・意味・接続・反復・破綻を0〜2で厳しく点検し、各文学／現代説明文の一文合格80%以上、全文非ループ90%以上の基準を維持する。

独自byte-BPEをTRAINの約70万文字だけから8,192規則まで学習し、同じ規則の前半4,096と比較。各1,000実更新のpilotを完了し、canonical VAL NLL/byteは4,096規則1.481589、8,192規則1.452002。後者を採用する。パラメーター数と一更新で読むbytesが違うので、差を語彙だけの因果効果とは扱わない。TESTは語彙や重みの選択に使わない。

本学習はseed1429、dim192、8層、4heads、5,231,616パラメーター、context256、causal lookback32、追加QAのない原文next-token prediction。CPU2コア・8 GiB、PyTorch2.6.0+cpuを計算に使う。activationはBF16、重み・optimizer・検証・最終推論はFP32。genre抽出は文学55%、情報通信10%、環境10%、気象15%、MDN5%、農林水産省5%。原文単位をcanonicalに符号化して、同じ対象tokenを長さ64／128／256のbatchで保持する。

本学習の10,000更新を完了し、両pilot各1,000更新を合わせ計12,000実更新を保存した。最終のcanonical VAL NLL/byteは1.186713で10,000更新のbeststateを選択。開発VAL9件の自然な一文は1,000更新snapshot／最終候補とも0/9、文学0/3、現代説明文0/6で言語段階は不合格。両モデルの全文非ループは2/9。新規TEST24件は生成していない。学習中に `main_train.py` と `batching.py` を変更しない。実物の1,000更新checkpointも保存し、全学習後に最終候補をVAL byte損失だけで選ぶ。まず同じ開発VALの1,000更新snapshotと最終候補を生成し、自然さ・破綻・ループを手動採点する。開発生成の基準が十分に成立するまで新規TESTを開かず保持する。基準が成立した後に、同じ新規TESTのsnapshotと最終候補を比較する。旧モデルの露出したTESTで改善を主張しない。日本語の基準が成立するまでQAを再開しない。

```sh
python training/language/round3/collect_weather.py
python training/language/round3/prepare.py
node --test tests/raw-language-round3-data.test.mjs
python training/language/round3/test_batching.py
# configに記録した同じ設定で両pilotを各1000更新完了してから実行
python training/language/round3/run_experiment.py
```

`train.py` は比較学習当時の固定コード、`main_train.py` は1,000更新snapshot保存を追加した本学習コード。比較学習中にsnapshot機能を追加してしまった変更は、コードを元へ戻して別ファイルへ移し、両pilotの実行時trainer SHAと一致を確認した。pilotの実際の処理は変更していない。

本学習は1,000更新の保存後に実行環境が再起動し、一時領域のログ・依存ライブラリが失われた。保持されたcheckpoint、optimizer1000カウンター、モデル・Python/Torch RNG・設定とコードSHAを確認し、同じ自作runを `--resume` で再開。未保存の更新数は不明なので加算しない。復旧は `runtime-recovery.json` に記録する。依存ライブラリは持続する `/workspace/.4k29-torch-training` に配置。再コンパイルを伴う実行環境の変更を、未中断実行とのbit完全一致とは主張しない。初回の起動スクリプトは `.txt` のsource archiveとして保存し、現行 `run_experiment.py` は開発VALの生成までを行いTESTを開かない。既に実行中のrunへこの起動スクリプトを重ねて実行しない。

5,000更新の途中診断も一文0/9、全文非ループ1/9だった。`midpoint-5000/state.pt` はFP32重みだけを保持し、optimizerを含む再開用checkpointではない。`diagnose_checkpoint.py` で元の全9件の文章と全tokenが一致することを確認した。診断を追加5,000更新として数えない。実物・根拠は `RESULTS.md`、`optimizer-audit.json`、`comparison.json`、各runの検証生成・採点・JS照合で確認する。

保存済み結果の再評価では `evaluate.py --out` に別のファイルを指定する。生成文・全tokenは比較できるが、elapsedSecondsなどの計時値は変わるため、保存した生成JSONと手動採点SHAを上書きしない。全学習を再実行する場合も新しい作業コピーを使い、既存の実験記録を保持する。
