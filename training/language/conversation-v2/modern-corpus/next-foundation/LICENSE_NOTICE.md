# 原文の帰属と研究用途

新規のSTAIR Captions注釈本文は、STAIR Lab (Chiba Institute of Technology) によるSTAIR Captions1.2の公式TRAINから取得した。データセットの著者はYuya Yoshikawa, Yutaro Shigeto, Akikazu Takeuchi。原文は約2,100人のアルバイト・クラウドワーカーが記述したと論文が報告するが、各captionの執筆者IDや本TRAIN内の実人数は分からない。

- 公式配布元: https://github.com/STAIR-Lab-CIT/STAIR-captions/tree/6ac656e65d80cbe2c914d93626a1d5454e35a5d6
- 元ライセンス: CC BY4.0 https://creativecommons.org/licenses/by/4.0/legalcode
- 論文: Yoshikawa et al., “STAIR Captions: Constructing a Large-Scale Japanese Image Caption Dataset,” ACL2017, https://arxiv.org/abs/1705.00823
- 加工: 原文の部分集合選択、完全一致・近重複の除去、画像IDによるfamily分離、独自BPEでのtoken化。語句・句読点・誤字の修正や補完はしない。画像や提供済みtokenized版、論文中のモデル生成例は学習に使用しない。
- 原文SHA、archiveSHA、取得日時、固定commit、許諾根拠は親ディレクトリのSTAIR関連receiptと各recordに保持する。

画像のライセンスをcaptionのCC BY4.0で代用しない。MS-COCO画像ファイルは取得・学習しない。作成手順確認用の論文PDFは隔離し、図版やモデル生成例をTRAINへ入れない。captionは人間による場面説明の原文で、AIアシスタント自身の視覚・経験・属性ではない。この注釈から会話理解、画像認識、事実QAの正確性を獲得済みとは扱わない。

既存のPR104採用原文は元の利用条件と帰属を継承する。JaQuAD/WikipediaはCC BY-SA3.0、Wikibooks/WikivoyageおよびRealPersonaChatはCC BY-SA4.0、JMAは元規約・例外付きPDL1.0。各recordのprovenance、版指定URL、履歴、出典SHAを保ち、詳細は `../../diverse-foundation/LICENSE_NOTICE.md` を参照する。本文を一括してコードのライセンスで再許諾しない。人間A/Bのrole意味と発話順序を維持し、assistantの役割へ読み替えない。

Global Voicesの隔離本文、青空文庫の保留作品、MAFFの評価資料、権利不明・拒否された新規経路はTRAINへ含めない。独立した人間評価と画像の事実照合は未実施。正式モデルへの採用、公開サイトへの反映、将来の商用公開条件を、この研究用データ審査で解決したと主張しない。
