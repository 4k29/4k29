# 日本語候補原文パイプライン（モデル学習なし）

原文出典/権利と、モデルへ学習投入してよいという判断を分離する。今回取得したJaQuAD TRAIN・Wikibooks・Wikivoyageは全て **candidate-not-admitted**。量を満たしても人間原文性、自然な日常日本語、利用条件を満たす学習資料の確保に成功したとは言わない。optimizer更新0、モデル作成0、Tokenizerfit0、upstream DEV/TEST取得0。

## 実際の処理結果（最終v3）

| 項目 | TRAIN | DEV | reserve |
|---|---:|---:|---:|
| 文書（TRAIN欄の括弧内は本文非空） |16966（16884）|2515|521|
| 保持段落 |146119|11204|4262|
| 現独自3997語BPEの本文tokens |20262193|2407757|681308|

全split計23,351,258 body tokens。TRAINは23,128,010文字、約1.14文字/token。これは各保持段落を独立に符号化した合計で、人工的な段落結合LF、BOS/EOS、QA質問やspan回答は含まない。将来の文書streamで `BOS + encode(段落間2LFで結合) + EOS` とした実target数とは異なる。**重複除去後本文が空の82 TRAIN文書を学習例にしない。**

現BPEではTRAIN段落のtoken長p50=82/p90=276/p99=867、256超16168/146119、512超4610、1024超1047。全保持本文のbyte復元に合格。TRAIN未知glyph119,836出現/320,465 UTF8bytesは既存のbyte fallbackで扱う。fallback件数は未知文字とword-BPE前のglyph組立token数を別記し、ASCIIのbyte語彙を全て未知文字と誤計数しない。

2022年より前の最終revisionかつ最後のcontributor名にbotがないWiki TRAINだけでは816,149tokens（本文非空603文書）。**この条件でも人間だけの執筆や全履歴を証明しない。** 日常/旅行らしいtitle keyword群は一部で、法令条文・技術/専門分野が多く、約半分はgenre未分類。keyword分類やCJK文字率は、日本語の自然さ・人間執筆・ジャンルの人手確認ではない。

## 原文と派生物

JaQuADは固定dataset revisionの30個のTRAIN JSONを読み、原文context、question/answer、original offset、source shardを保持。691記事/9713段落/31748人手QA。記事titleでshard間を統合する。Wikipedia contextの人間/bot執筆は保証しない。

Wikiは公式XML bz2のSHA256/公式SHA1を原典側で記録。namespace0の全raw wikitextとpage/revision/contributor metadataを `raw-pages.jsonl.gz` に保持する。元XML自体にも全wikitextがある。本文は **mwparserfromhell0.7.2で生成した派生plain text** で、原文そのものと呼ばない。templates/code/math/table/mediaを含むblockを除外、ref注記を除外、list行・短すぎるblock・残留markup/URLを除外する。LLMによる修文/補完/回答生成はない。正しく読めないblockを語句の継ぎ合わせで自然文に見せない。

normalizationは別fieldにNFCとCRLF/CR→LFのみ。NFKC、言い換え、原文上書きはしない。raw/normalized/空白除去canonicalのSHAを分ける。rawCharactersというreceipt項目はJaQuADでは原context文字、Wikiではparser後・NFC前の派生段落文字であり、元wikitext文字数ではない。元wikitext文字数はadapter receiptに別記する。

MITの構文parserは `/dev/shm/foundation-parser` のみへinstallした。学習済みモデル/Tokenizerではない。wheel名・SHA・license・再現setupはparser-dependency.json/MWPARSER_LICENSE.txt。新たな環境では同じwheelを検証してからinstallする。

## 重複・family・split

raw exact3343段落、NFC/空白canonicalで追加96段落、検証済みnear696段落を候補本文から除外。全原文とwitnessはarchiveに残る。近重複はcharacter5gramのCRC32最小16個を候補検索し、2個以上共有/長さ比0.8以上/真のJaccard0.85以上を検証する。293,758比較・2,657 near pairs、頻出postingを53,954回skipしているので **完全な近重複/意味family監査ではない**。exact/near linkとsource familyをunionしてからsplitする。

`SHA256('foundation-data-split-v1|' + component内の最小family)` mod100が <10 DEV、10–14 reserve、それ以外TRAIN。既存RP187,667発話とのcanonical exact一致を調べ、RP DEV一致なら隔離、RP TRAIN一致ならTRAINへ固定する。今回一致は0。段落exactが0でも意味・部分転載・話題の独立性は証明しない。

Wikibooksは `/` より前をbook familyとし、さらに `^(.+?)第[数字]+条` という明確な条番号chapterも親prefixへまとめる。v1では法名の条番号pageを別familyにした実装上の問題があり、v2の法名限定fixでも施行規則/令を取りこぼした。rootの原文品質読解で見つかり、**モデル出力を見る前に** v3でboundedなfamily修正を行った。9206 section pages/309親prefixに対するcrosssplitは最終0。全JaQuAD691記事のsplitはv1→v3で不変。法律以外も含む完全な意味family/旅行地域hierarchy分離を主張しない。

v1/v2の実行codeはbuild-v1.py/build-v2.py、receiptとsplitはartifacts/*v1/v2*へ保存。元のfull出力はtmpfsのcombined-v1/combined-v2、最終はcombined。歴史receiptの絶対pathは実行時の記録なので、移動後のsnapshotを検証する際はversion directory＋basenameに読み替える。以前の不適切なsplitを合格記録へ改変していない。reserveはpipelineが全payloadを扱っており、**封印TESTではない**。

## 再現/成果物

1. source担当manifestを使って原典を取得・SHA確認する（`sources/`参照）。既存の公式dumpやTRAIN shardを再利用できるなら再取得しない。
2. `wiki_adapter.py --manifest <source manifest> --output <new tmpfs output>` を実行。rawと派生物/削除統計を分けて保存。
3. `build.py --manifest <JaQuAD manifest> --generic <Books derived gzip> --generic <Voyage derived gzip> --output <new output>`。新規directoryのみ許可。既存Tokenizer/readmeの重みは変更しない。
4. `post_audit.py --input <final output> --output <new post output>` でpre2022等のsubset、source-balanced PF16窓、品質読解候補を生成。
5. `verify_inputs.py --input <final output> --output <verification.json>` で32raw source files、全raw/derived archives、context/QAoffset/normalizer/重複/family/token集計をread-only検証。
6. `python -m unittest discover -s .../pipeline -p 'test_*.py'`。7テストで正規化、transitive family、near false match、原典破損/QAoffset、template/ref除去、条番号familyを確認。

最終compressed corpusとraw sourceのGit保存はroot担当。tmpfsはhost消失時の永続保存を保証しない。各sourceは異なるCC版/権利状態を持ち、一括licenseへ潰さない。データ投入・8k/16k語彙fit・context変更・本学習はこのpipeline実行に含まない。
