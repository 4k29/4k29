# 原文日本語の再学習 round2

PR36の実験を変更せず、現代日本語の分布と自作語彙を見直す実験。Wikipedia、外部の学習済み重み・Tokenizer・生成API、teacher文章、QA／instruction、生成出力の補修を使用しない。

総務省の情報通信白書と環境省の環境・循環型社会・生物多様性白書（令和6〜8年版）から、原文の本文段落を追加。図表・脚注・ナビゲーションを除き、レイアウトの空白を正規化。脚注参照番号を除くが、文の表現は作り直さない。原文本文の図表参照などは残る。

出典：各文書に記録した総務省・環境省のURL。加工して学習データを作成したもので、両省が作成・承認したモデルではない。公共データ利用規約（第1.0版）に従う。出典・利用条件・取得日時・HTML／本文SHAは `modern-sources.json`、`modern-documents.jsonl`、`source-credits.json` に保存。以前の443文書の出典・個別ライセンスは親ディレクトリの `DATA-LICENSE.md` と `source-credits.json` に従い、その記録も保持する。

新規原文は571文書、1,276,513文字、3,621,018 UTF-8 bytes。既存原文を含め1,014文書、4,190,519文字。同一段落が複数年度に存在することを考慮し、80文字以上の段落が一つでも一致する新規文書を同じ分割グループへ置く。以前の分割は変更しない。以前から開示されているMDNの共有段落1件は残るが、新規文書の長い段落の分割間重複は0件。新しい評価書き出しはTRAIN内に存在しない。

古いTEST22・VAL9を見た文書から新しい生成プローブを選ばない。TEST24件（文学8、情報通信8、環境8）をTokenizer学習前に固定。過去のTEST22は今後は開発診断用。重みは新たに乱数初期化し、最初の6層モデルは過去の学習済みモデルを親として読み込まない。続くprefix-view実験は、このround2の原文モデルだけを親として使い、optimizerと乱数を新しくする。

独自byte-BPEをTRAINのみの抽出段落から学習し、同じ8,192規則の前半4,096規則と比較。完全な原文段落のcausal next-token predictionで学習する。段落の末尾だけをEOSとし、長い段落にはcontext=256／masked overlap=32を適用。TRAINには同じ原文のcanonical BPEと独自merge dropout 0.15／0.30の表現を作る。これらは同じ原文の再符号化であり、新しい文章ではない。

学習時の抽出比率は文学30%、情報通信30%、環境30%、MDN7.5%、気象庁1.25%、農林水産省1.25%。新規データ量だけでなく、学習中の現代日本語の比率も調整する。byte正規化VAL損失で語彙・checkpointを選び、固定TESTでの生成全文を最後に評価する。語彙によって一更新で読むbytesとembeddingパラメーター数が変わるため、損失差を語彙だけの効果とは断定しない。

語彙比較は各1,000更新、合計2,000更新を完了。byteあたりの検証損失は4,096規則で1.476292、8,192規則で1.417185となり、後者を選択した。本学習は4,341,888パラメーター、6層、dim192、seed929で10,000更新を完了。最良のcanonical VAL byte損失は1.098933、選択checkpointは10,000更新。開発用VAL9件の生成は厳しい文法・意味・つながりの採点で1件のみ合格。5,000更新時点の実物snapshotでも1/9だった。損失が下がっても、自然な日本語を安定して生成できるとは判断できない。全文・全token・採点・Python/独自JSの一致検証を保持する。

固定256token・batch8の同じ新アーキテクチャをCPU2コアで比較すると、FP32の中央値0.544091秒に対してBF16は0.365415秒。順番はFP32／BF16／BF16／FP32とし、各回5更新のwarmup＋10更新を測定。60更新は全て破棄し、採用モデルの学習数に加えない。BF16のactivationを使い、重み・optimizer・最終推論はFP32。これは固定形状の計算速度の比較であり、回答速度や日本語の質の証明ではない。

本学習は長さ64／128／256のbatchにまとめ、未来の不要なpaddingを減らす。全ての元の対象トークンを保持し、因果的なlogitと対象ラベル、元のrowの抽出確率が保たれることを検証。batch内の長さの相関と更新の軌跡はpilotと異なる。canonical／dropoutの別表現や文書間の同じ段落を、新たな原文量として数えない。段落インスタンス数と重複除外した段落の文字数は `corpus-distribution.json` で区別する。

```sh
python training/language/round2/collect.py
python training/language/round2/prepare.py
python training/language/round2/prepare_paragraphs.py --merges 4096
python training/language/round2/prepare_paragraphs.py --merges 8192
node --test tests/raw-language-round2-data.test.mjs
```

計算環境はCPU2コア・8 GiB、PyTorch2.6.0+cpu。PyTorchは計算に用い、自作decoderの重み・語彙・推論に外部の学習済みモデルを使わない。

TRAINの原文だけに4種類の途中位置を設け、prefix/suffixを別々に独自BPE符号化する追加実験を実行。単語・文字・文を作り直さず、途中にEOSや区切り記号を入れない。元の全角空白も保持する。73,760個の追加表現は同じ18,440段落の再符号化であり、新規原文ではない。canonical／dropout0.15／dropout0.30／prefix-viewの抽出比率は50%／10%／10%／30%。語彙と全てのheldデータはbyte単位で同一。seed1229、学習率0.00025、追加10,000更新を予定し、完了後のVAL byte損失だけで親／追加モデルを選択してから、固定した新しいTEST24件と旧原文モデルの同一書き出しで比較する。TESTの文章も合格基準も変えない。

追加実験の5,000更新時点でも開発VALは1/9合格。中間診断のsnapshotは原文モデルの親10,000更新＋追加モデルの選択5,000更新の系譜で、診断として5,000更新をもう一度加算しない。`prefix-validation-5000` にgzipの実物重み・全文生成・採点・JS一致を保存する。snapshotは共通の固定exporterを使うためversion文字列が他の診断と一致する場合があるが、モデルの識別はSHAと `training.run` で行う。
