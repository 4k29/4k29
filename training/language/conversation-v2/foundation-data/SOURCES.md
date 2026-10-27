# 現代日本語基盤の原典・利用条件監査

目的は、説明・理由・手順・日常会話を理解し、内容のある自然な日本語を生成できる独自Transformerのための原典基盤を作ること。今回の取得量を言語能力や十分な学習量とは扱わない。本書は原典取得とlicenseの監査であり、学習admissionやモデル評価の合格ではない。

## 今回実際に取得した資料

| 原典 | 固定版 | 実取得payload | 原文の性質 | 状態 |
|---|---|---:|---|---|
| JaQuAD upstream TRAIN全30shards | HF `05600ff310a0970823e70f82f428893b85c71ffe` | 22,713,267bytes JSON | 9,713contexts、31,748人手QA。日本語Wikipediaからの説明文と人間annotatorが書いた質問/抽出回答 | 取得・全raw SHA検証済み、候補。DEV/TEST未取得 |
| 日本語Wikibooks公式articles dump | `20261001` | 29,978,542bytes bz2 | 教科書・解説・言語・技術・手順。raw XMLは全namespaceとmarkupを含む | 公式size/SHA1およびSHA256検証済み、候補 |
| 日本語Wikivoyage公式articles dump | `20261001` | 6,282,051bytes bz2 | 旅行・交通・地域生活情報。raw XMLはlistings・地名・数値・templateも含む | 公式size/SHA1およびSHA256検証済み、候補 |

取得payload計58,973,860bytes。これはJSON非圧縮とXML圧縮の混合量であり、独立した自然文の文字/token量ではない。JaQuADは同じcontextに複数QAが付くため、QA件数倍の原文量とは数えない。独立文章量・正規化後の重複・分割・token数はpipelineの実測を参照する。**10–30Mの資格確認済み人間TRAIN tokensを確保済みとは主張しない。**

原文は `/dev/shm/foundation-data-source/` に取得し、workspaceへ大きいraw作業コピーを作らなかった。JaQuADは30JSONを無修正でdeterministic tar.gzへ格納（5,092,060bytes、SHA256 `0e10537a635c02f9a4569257085b6f343bfa71109ea080f3440b9ee94c0e3be2`）。Wikiのbz2は再圧縮せず原典のまま。計41,352,653bytesのraw archiveを親エージェントへ引き渡した。**tmpfsの実在とGitへ永続収録済みであることは別**なので、最終保存のreceiptを併せて確認する。

取得/再取得/byte検証は `sources/replay_acquisition.py`。通常実行は既存payloadの検証のみ、`--fetch` を明示した場合だけ固定TRAIN/公式dump URLsを取得し、記録済みsizeとSHAを要求する。DEV/TEST・外部学習済み重み・Tokenizerは取得しない。再生成するJaQuAD archiveはnumeric shard順、tar mtime/uid/gid0、mode644、gzip mtime0/filename空で固定した。

## 利用条件の確認と残る懸念

### JaQuAD：CC BY-SA 3.0

原典GitHub commit `23f5d72cc273c49b35e2d9efe0f51757aa1770bd` READMEのLICENSE節に、datasetをCC BY-SA3.0とする明示を確認。全文licenseとREADMEをsourcesへ保存した。帰属は ByungHoon So, Kyuhong Byun, Kyungwon Kang, Seongjin Cho, *JaQuAD: Japanese Question Answering Dataset for Machine Reading Comprehension* (2022), SkelterLabsInc/JaQuAD。

質問と回答が人手annotationであることは原典の説明に基づく。Wikipedia由来contextの全執筆者が人間だけであることや、転載・第三者引用の権利を独立に証明したわけではない。記事title/元記事URLとdataset版・rawSHAを保持し、Wikipediaの元revision/帰属の対応と引用箇所を追加監査する。短いspan回答を自然なassistant全文の正解へ勝手に変更せず、AIで回答を言い換えて学習へ入れない。

### Wikibooks/Wikivoyage：CC BY-SA 4.0

両siteの公式 `meta=siteinfo&siprop=rightsinfo` が、CC BY-SA4.0とlicense URLを返すことを確認し、response bytes/SHA/取得時刻を保存。公式Wikimedia利用規約日本語版もHTTP200で取得した。過去の監査時の403を、今回も取得できなかったという事実へ流用していない。

規約7節は、原著作権を持つテキスト寄稿をCC BY-SA4.0/GFDLで許諾し、帰属の方法として記事URL（全寄稿者を示す履歴ページが存在するため）等を挙げる。再配布時は原典記事のURL/履歴、license、加工の明示、share-alike等を維持する。画像・音声・商標や第三者素材が全て一律CC4という意味ではない。今回取得したのはテキストXMLで、画像ファイル自体は取得していない。

rawの最新revisionは2026年版なので、人間・bot・生成AI由来の寄稿を混在させ得る。`latest revision timestamp < 2022-01-01` の部分集合はpost-2022編集への露出を減らす診断軸だが、**人間原文であることを自動認証しない**。rule-based bot、翻訳、古い自動生成、第三者からのimportもあり得る。page/revision ID・timestamp・contributorを保持し、bodyの自然文品質、引用、コード/数式/単語表/広告/案内一覧を別々に監査する。

Wikibooksの章を別partitionへ割らないよう、少なくともtitleの`/`前のbook familyをgroup化する。Wikivoyageは隣接地域・上位地域・同名地・交通案内の意味的重複があり、title hashだけでfamilyの独立性を証明しない。全namespace/全markupのraw量を、抽出済み自然文や学習可能量と混同しない。

**今回の3sourceはいずれもcandidate-not-admitted。** 原典の配布licenseの明示と、個々の文章の権利/人間原文性/品質/重複/分割のadmissionは区別する。機械の抽出・正規化に合格しただけでTRAINへ自動承認しない。

## 既存資産と、今回は取得しなかった候補

- 既存RP TRAIN：5,986会話/180,006発話/約2.457M本文tokensは保持するが、今回新規に集めた独立量へ足さない。永続speaker splitと旧DEV隔離を壊さず、`llm_dialogue_system` の別モデルログは人間原典に混ぜない。
- 既存JMRD TRAIN：4,575会話/103,444発話、原典CC BY-SA4.0。roleは実話者IDではない。映画title family分割が必要。以前のadmissionはdialog[].textのみで、knowledge/review/plot/questionnaireは正解対象外。人間の発話でも、提供された外部knowledgeを転載している可能性があり、新たに広く使用する前にcopy/引用監査が必要。今回は新規量に数えず、既存policyを勝手に緩めない。
- 日本語Wikipedia：公式20261001の統合multistreamは4,879,122,470bytes、indexも31,437,876bytes。dumpstatus metadataのみ取得し、本体は取得していない。将来100M tokens以上の拡張候補になり得るが、保存容量・抽出・人間原文性・genre分布を含む別admissionが必要。小さなrange取得やpre-2022 subsetを、全体の公式SHA検証/品質保証と同一視しない。
- MOJ/ISAの生活・就労ガイドとcopyright URLsはHTTP403、文化庁の旧候補URLは404。生活手順の用途は近いが、今回本文/利用条件を確認できず取得していない。政府文書を全て自由利用可能と推測しない。
- JDDは研究限定・chatbotサービス不可・再配布不可等があるため、公開目標への学習に自動投入しない。CEJCは申請/契約が必要。権利不明なWeb/CommonCrawl一括資料、既成LLMの生成回答は候補量を稼ぐために足さない。

## 収録物

`catalog.json` はsource別の利用条件・人間原文性の証拠水準・残るadmission条件を記録する。`sources/*acquisition.json` がURL/revision/raw bytes/SHA、`wikimedia-probes.json` が公式rights/terms/dumpstatusのHTTP取得receipt、`government-probes.json` が未取得の理由、`license-verification.json` が確認範囲を示す。原典rawは文章を生成修正していない。parserによる派生抽出はrawとは別の変換履歴・SHAとして管理する。
