# 次の実験用のMDN日本語原文

新規1,457文書、2,557,215文字、6,450,761 UTF-8 bytesの原文説明文を保存した。Wikipedia、外部モデル、既成Tokenizer、生成API、teacher文章、QAを使わない。**未分割・未学習**であり、実行中のround6には追加していない。文書数や文字数を学習回数や能力の向上として数えない。

MDN contributorsの日本語ページから、40文字以上で自然な句点等で終わる元のp段落を選ぶ。headings、lists、code、tables、navigation、browser-supportの定型案内を除く。既存のown HTML parserがlayout whitespaceを正規化するが、日本語を書き換えたり生成したりしない。元のblock indexを保存する。記事全文ではなく原文の段落抽出であり、画像・表・code等を除いた段落が単独で意味を保つとは保証しない。

出典URL、最終URL、著者、取得日時、title、原文text SHA、完全HTML SHA、gzip archive SHA、加工内容、利用条件を各recordに残す。全1,457 HTML archiveを展開して同じparserで再抽出し、段落とtextの一致を確認した。既存round3にあるcanonical URLは新規文書として採用していない。exact source URL／textの重複を除いた。80文字以上の共通段落による連結を追加監査し、新規文書を含む1,344 group、旧TRAINに連結する新規5文書、旧non-TRAINに連結する新規0文書を確認した。13,669種類の長い段落のうち124種類は新規文書間で重複する。fuzzy／80文字未満の重複はこの監査では測っていない。分割を作る段階でこのgroupと旧所属を引き継ぐ必要がある。

## 出典と利用条件

本文の出典はdeveloper.mozilla.orgの各日本語記事、著者はMDN contributors。source-discovery/copyright-policy.htmlに保存した[MDNの著作権方針](https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Attrib_copyright_license)は、本文についてCC BY-SA 2.5とlater-version allowanceを示す。抽出した段落は、元の出典・著者・加工内容を維持して[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)で扱う。upstream-LICENSE.mdには本文／codeの元のlicense全文を保存している。各利用条件・robotsの原文snapshotとSHAも保持する。

URL発見にはmdn/translated-contentのcommit d039df688593089a43fb7cdca456567549bca360、ja/web tree 8274461d1b970489e87afd32a4c4eef43fa96769を使った。これは**発見用indexのcommit**であり、取得したHTMLの版と同一commitとは主張しない。HTML自身は個別のbyte SHAと実物archiveで固定する。公開Webのrobotsを確認し、アクセス制限を回避しない。新規sourceの取得だけで外部の学習済みモデルは読み込まない。

## 収集後の監査処理の修正

1,500 URLの取得loopとrecords／creditsの保存後、parser source SHAの出力で誤ったpathを参照し、元collectorの最後のmetadata生成が失敗した。実際に実行したsourceをcollector-executed-before-metadata-fix.py.txtに保持する。collect_mdn.pyではそのpathを修正し、verify_collected.pyで保存済み全HTMLと未変更textを照合してmdn-sources.jsonを完成させた。

失敗／skipの個別attempt詳細は元のprocess内だけにあり失われたので、空配列で「失敗なし」と偽らずnull／attemptFailureAndSkipDetailsNotRetainedとして記録する。成功数は検証できた1,457実物だけ。原文の再取得や書き換え、Tokenizer fitting、optimizer更新をこの修正で行っていない。

最初の途中収集では、canonical URLへ転送される別URLのarchive名の衝突を避けるため、最終保存前に停止した。途中archiveと旧sourceはworkspaceの別ディレクトリーに隔離し、今回の成功数・本文・学習には含めていない。修正後の実行では入力URL SHAをarchive名に加えた。

## 次の分割・学習前に必要な確認

親のTRAIN／held境界を維持し、新規文書のcanonical identityと80文字以上の共通段落からgroupを作る。既存heldに連結するgroupを新規TRAINへ入れず、TRAIN／heldに跨がるgroupは隔離する。新しいheldの文字・prefix・生成文を語彙作成、重み選択、学習ラベルへ使わない。原文の文書・段落・引用の連続性と全対象を検証してから、新しい実験の設定と厳格な言語評価を固定する。基準成立まではQA学習と公開回答モデルへの移行をしない。
