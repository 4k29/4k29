# 原文・加工資料の帰属と利用条件

この研究ディレクトリの収録原文を、リポジトリのコードライセンスだけで再許諾したものではない。`corpus.jsonl.gz`、原典snapshot、引用するDEV原文は、各recordの`provenance`と元資料の条件を保持する。正規化・許諾された抽出・token化・window化を行った加工資料であり、原著者がこのモデルや研究を推奨したと表示しない。

|出典|帰属・ライセンス|元資料と加工情報|
|---|---|---|
|JaQuAD/Wikipedia context|JaQuAD作成者・各Wikipedia記事の寄稿者、CC BY-SA3.0 https://creativecommons.org/licenses/by-sa/3.0/ |記事URL、dataset revision、family、原文SHAはrecordに保存。元datasetと記事履歴も参照する。抜粋を文書全体と偽装せずEOSを足さない。|
|日本語Wikibooks/Wikivoyage|各ページ寄稿者、CC BY-SA4.0 https://creativecommons.org/licenses/by-sa/4.0/ |各recordの版指定URL、履歴URL、revision、元dumpSHAと抽出履歴を保持。過去に採用した部分集合のみ再利用。|
|RealPersonaChat|Sanae Yamashita et al., RealPersonaChat (PACLIC2023), nu-dialogue/real-persona-chat、CC BY-SA4.0 |https://github.com/nu-dialogue/real-persona-chat 。recordの固定commit/会話URL、元SHA、匿名source speaker IDsを保持。原文の順序と人間話者・発話境界を保持し、AI自身の個人経験へ変換しない。|
|JMA FAQ|気象庁 https://www.jma.go.jp/jma/kishou/know/faq/ 、公共データ利用規約PDL1.0|https://www.jma.go.jp/jma/kishou/info/coment.html / https://www.digital.go.jp/resources/open_data/public_data_license_v1.0 。画像・ロゴ・第三者等の例外は別。FAQの見出しと全回答段落を原順序で抽出した研究用sectionで、気象庁作成のモデルではない。取得URL/日時/版の限界/SHAはACQUISITIONと各recordに保存。|

CC BY-SAの加工本文を再配布する際も、該当ライセンスの表示・帰属・変更表示・継承条件を維持する。各資料の条件を一括して消さない。学習済み重みと原文の法的関係・第三者権利・将来の商用公開条件を、この研究のモデル不採用判断で解決したと主張しない。

Wiki本文の人間執筆性を完全に確認したわけではなく、botやAI由来の寄稿が含まれる可能性がある。外部生成APIや学習済み言語モデルから教師を作成してはいない。`provenance.admission`等に残る古いcandidate状態は元のPR94取得時の履歴であり、現在の採否はPR103承認原文、現在のQUALITY_REVIEW/CORPUS_AUDITに従う。原典履歴を現在の採否に合わせて書換えない。

JMRDの保留本文、raw knowledge、MAFFの未採用候補、KokoroChat/ETC等をこのTRAINのライセンス表示で承認しない。採用・保留と人間執筆の確証を混同しない。第三者申立てや個人情報の問題が生じた場合はsource ID/familyから隔離し、データと派生実験を再構築する。Gitからの完全削除や既学習重みのunlearningを保証しない。詳細はRIGHTS.mdとFAILURES.jsonを参照する。
