# 原典と加工の帰属

データ：JMultiWOZ: A Large-Scale Japanese Multi-Domain Task-Oriented Dialogue Dataset。作成者：大橋厚元、平井龍、飯塚慎也、東中竜一郎。公式配布元 https://github.com/nu-dialogue/jmultiwoz 、revision `a78dd334b907e12318b76bb23d0a9ed1498b8d15`。論文 https://arxiv.org/abs/2403.17319 。確認日2026-10-28。

データセットのライセンス：Creative Commons Attribution-ShareAlike 4.0 International https://creativecommons.org/licenses/by-sa/4.0/ 。原ライセンス全文は `sources/jmultiwoz-LICENSE`、根拠READMEと取得SHAは同sources内に保存。原典READMEは、訓練モデルをデータセットの直接的な複製/派生とみなさないと明記している。ここではデータ加工物自体についてCC BY-SA 4.0の帰属・継承を保持する。

加工：宣言TRAINから業務施設の原子fieldを抽出、施設重複除去、旧23DEV施設の除外、entity SHA分割、token長フィルタ、プログラムによる質問/教師文構成。料金/設備の反実仮想は入力に「仮定」を表示する。`data.json`、`contrast-data.json`、その入力に依存する診断質問は変更を伴うデータ加工物としてCC BY-SA 4.0で提供する。人物の原文返答を再公開しておらず、人間執筆の正解とも称さない。モデルによる生成全文はモデルの無修正出力であり、原典の正解文ではない。

第三者サイトの文書・画像・電話・住所・個人属性はこの加工に含めない。個別権利の包括的な法的判定や、原典収集時点からの情報更新は行っていない。権利申立て時はprovenanceのobject SHA/会話/turn/施設で該当加工例を特定し、公開データと将来のscheduleから隔離する。公開済みモデルの学習効果を個別に消去できるとは約束しない。正式提供者同意を新たに取得した実績は0。
