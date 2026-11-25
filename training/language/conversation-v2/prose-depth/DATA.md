# データの出典・帰属・分割

TRAINはPR #105の採用済み原文集合を親にした。権利確認は [親のLICENSE_NOTICE](../modern-corpus/next-foundation/LICENSE_NOTICE.md) と [データ監査](../modern-corpus/next-foundation/DATASET_AUDIT.json) を継承する。STAIRはSTAIR Labの人手caption本文のみ（CC BY 4.0）。JaQuAD由来本文は元のCC BY-SA 3.0、WikibooksとWikivoyageはCC BY-SA 4.0、気象庁原文には確認済みの条件と例外がある。TRAIN_INDEXの原典IDを親原文に照合できる。Global Voices・RealPersona・画像・外部生成文は今回のTRAINに含まれない。

50万・100万を初めて越えるバッチ境界を評価点に固定した。50万点は492更新・500,229教師、終端は985更新・1,000,985教師。教師には実原文位置だけを割り当てた。元の文章内の順序は各窓に保存し、窓のバッチ提示順はシャッフルした。教師位置の延べ数と独立数はどちらも1,000,985。27,490のEOS、4,036のLF、212,183の右PADがあり、右PADは分母から除外した。親の真正な終端だけを使用する。本文の切り出し開始が文書先頭より後にある場合、その直前の1 tokenを保持する。

|出典|教師|原文単位|
|---|---:|---:|
|STAIR|500,609|27,335|
|JaQuAD由来本文|408,758|1,768|
|Wikibooks|61,362|463|
|Wikivoyage|27,710|194|
|気象庁|2,546|17|
|計|1,000,985|29,777|

独立パネルの日本語Wikipedia本文は元の固定版、履歴URL、抜粋SHA、BPE列をDEV.jsonに記録した。本文は元の導入冒頭3文。原文中の文を追加・修正していない。ライセンスは [公式CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.ja)。SOURCE_SNAPSHOTSに取得時点の版と抽出本文、WIKIMEDIA_RIGHTSに公式のサイト情報を保存した。既知のTRAINとの文書名と連続12-token一致は合計8アーカイブで確認した。別名転載・意味的近重複・学習履歴の完全な網羅は保証しない。従来DEVとcaptionの画像ID・原典familyを除外した。過去に固定された封印TESTは参照しなかった。

日本語記事の候補と採否は学習前に固定した。選ばれた24件は家庭用品・文化・手工芸・遊びの説明が中心。ジャンル全般や著者が独立した無作為標本を代表しない。NLLは与えた原文の第一文と統合した後続二文の本文のみを測る。固定・追加DEVの文書でcontext256を超える後続だけは同じ規則で切り、採点中のモデル出力に合わせて選び直さない。
