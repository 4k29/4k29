# Round35 — human utterance-end EOS auxiliary

実学習を継続中。事前検証は完了し、固定条件の10,000更新を実行している。PR #76にはactual5,000の完全なmodel/Adam/RNG checkpointと、その時点までの観測済みlossを保存した。これは完了数10,000の主張ではない。稼働中の実数はexecution/train.logとcheckpoint監査、完了時はresult.jsonを参照する。全文の意味は未評価で、公開モデル・サイトは変更していない。

Round34との兄弟比較で、同じaligned Round28 model/Adam20000/Torch/privatePython RNG、weight lineage59000から開始。唯一の学習変更は、human TRAINの真の発話末尾で元のunmasked正解tokenがstandalone改行16の場合に、coefficient1.0のEOS2補助CEを加えること。batchの元のvalid target数で正規化し、元の改行CEは残す。R34の自己負例prefix境界条件は維持する。独自8層×192、既存5455語彙・BPE40/30/30、data/抽出/LR/seed/他の損失・推論・純CE選択基準は固定。

全147,986 TRAIN行の対象位置、元の正解とデータの保存、27 tests、実データの有限・非ゼロ勾配、親Adam/RNG、初期DEV全view完全一致を検証した。actual200・1,000・5,000でもR34と正例量・乱数・負例prefix入力が一致。訓練用生成でEOS終了は増えているが、終了や短さだけで日常会話の意味改善とは判断しない。

比較曲線は観測地点だけを載せる。最終selected/terminalの同一入力全文、Py/JSとraw/export一致を確認し、実際の全文読解後に厳格ゲートを適用する。露出済みDEVであり新TESTではない。[EVALUATION_LIMITS.md](EVALUATION_LIMITS.md)、[NUMERICAL_LIMITS.md](NUMERICAL_LIMITS.md)、[Round34 context補足](execution/ROUND34_CONTEXT_CORRECTION.md)も参照。
