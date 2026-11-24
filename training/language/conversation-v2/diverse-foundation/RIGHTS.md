# 原典と利用範囲（2026-10-29確認）

本系列は隔離された探索的な日本語言語モデル研究。公開回答モデルの採用ではない。原文の話者の体験・職業・映画推薦者という役割をAI自身の属性へ変更しない。

- **PR103の2,045,786本文tokens**：`pretraining-scale/corpus-clean.jsonl.gz`のみ。既存のCC BY-SA3.0 JaQuAD、CC BY-SA4.0 WikiBooks/Voyage、原典URL/revision/帰属/加工履歴、除外familyを継承。未審査の20.26M候補を一括承認しない。JaQuAD抜粋にEOSを追加しない。
- **RealPersona**：既存`data/train.docs.jsonl`のみ。CC BY-SA4.0、Yamashita et al./nu-dialogue。原著者の匿名化・倫理除外と既存TRAIN/DEV話者分割を維持。取得/権利/品質の過去監査はPR92/98/99のまま。既存の人間A/B role3/4・発話末EOSを保持。固定20会話の読解を再利用する。個人経験は人間会話の引用的言語資料でありAI応答の事実教師ではない。公開化されていても匿名性の完全保証はない。
- **JMRD**：Kodama, Tanaka, Kurohashi / ku-nlp、commit `a20b0a89b4cf6ce1db320039f6e27df10604bf4c`、CC BY-SA4.0。既存公式TRAINを同じSHAで再取得し話者順序を復元する。新規独立原文量には加算しない。`dialog[].text`だけを候補にしknowledge/review/questionnaireを教師へ入れない。checked_knowledgeから40文字以上そのまま写した可能性がある場合と連絡先検出時は映画family全体を隔離。固定標本を原文で読む。映画に関する発話の事実正確性や全第三者権利を機械判定だけで証明しない。映画内容を知らないと答えられない発話はassistantの根拠付きQA教師とは扱わない。永続worker IDがなく話者独立性は不明。公式valid/TESTを取得・閲覧しない。生のknowledge等を含む再取得ファイルはGitへ入れない。
- **気象庁の一般向けFAQ**： https://www.jma.go.jp/jma/kishou/info/coment.html により、別表記のないコンテンツは公共データ利用規約PDL1.0。 https://www.digital.go.jp/resources/open_data/public_data_license_v1.0 。原典の出典表示、加工の明示、第三者権利・ロゴ等の除外、政府作成を装わない条件を守る。15ページへの低頻度単発取得、認証/制限回避なし。公式robots.txtは404。図、引用、外部資料に依存する候補を保留し、残る固定標本を読む。動的な予警報配信や予報事業ではない。HTMLから見出しと本文を原順序で抽出し、原典FAQの質問と全回答段落を独立sectionタスクとする。文書末尾を偽装せず、このタスクの真の終端にEOSを置く。TRAINと新DEVはページfamilyで事前分離。取得URL/日時/HTTP snapshotSHAをACQUISITIONへ保存。HTMLの案内/画像/広告は学習しない。
- **KokoroChat**： https://github.com/UEC-InabaLab/KokoroChat 。CC BY-NC-ND4.0。学術論文で学習例が示されても、本研究の加工データ・将来公開モデルへ制限なく適用可能とは解釈しない。ND/NCと相談領域の条件を確認し、今回は本文取得・学習とも保留。README/LICENSEのみ保存。GPT-4o-miniによるtopicラベルは人間原文と別であり採用しない。
- **ETCDataset**： https://github.com/UEC-InabaLab/ETCDataset 。CC BY-NC4.0、人間crowdworker997会話という原典説明を確認。非商用研究と将来公開の条件整理、人物属性を保存しない取得契約、公式splitの個別取得が未準備。今回は本文を取らず保留。量を満たすため採用しない。
- MRMPCの3話者、JMultiWOZの旧DEV接続隔離、OASST29件の条件付き審査を変更しない。ライブSNS、NC/ND資料、未許諾原文を追加しない。

CC BY-SA原文とPDL原文の帰属を単一licenseで消さず、個々のprovenanceを維持。加工本文は原文検索による再識別や第三者権利の残存リスクがある。申立て時はsource ID/familyとcheckpointの系譜から対象を特定し、原文と派生corpusを再構築する。Gitからの完全消去・既学習重みのunlearningは保証しない。正式採用/本番公開は従来ゲートが未達の間No-Go。
