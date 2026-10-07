# 原文の語途中境界へ集中する追加学習

round3の5,000更新の開発診断で、語の途中の入力を自然に継続できず、反復へ陥る例を観察した。出力の補修をせず、同じ原文と独自TokenizerでTRAINだけの符号化・学習マスクを変える比較を準備する。準備の完了をモデルの学習や品質向上の達成とは扱わない。実完了更新は各runのcheckpoint／optimizerとresultで確認する。

canonical全文の全対象tokenを保持し、4,498原文単位ごとに4個のUnicode切断位置をseed1529で選ぶ。入力と続きは独立にBPE符号化し、元の連続した原文と完全にbyte一致する。追加17,992ビューは原文を繰り返した表現で、新規作品や文章ではない。追加行は原文入力をマスクし、最大32個の実際の続きを教師信号とする。全文のtoken列を保存しているが、追加行は全文の全対象を再び学習するものではない。canonical行との抽出重みはそれぞれ50%。途中に新しいEOS・区切り・質問回答・teacher文章を足さない。dataの元statsはcanonical親データの統計であり、追加行の対象数はfocusedLabelTokensに別記する。

独自Tokenizer、VAL／TESTのtoken/index、原文文書・文書グループ分割はround3の実物を変更せず使う。以前の曝露した原文モデルは読み込まない。round3の新規乱数初期化8層モデルが実際に10,000更新を完了した後、その同じTRAIN／held／TokenizerのVAL選択beststateだけを親にする。親checkpoint SHA、全optimizerカウンター10000、モデル構成、trainer SHAと原文・分割・語彙SHAを照合し、別の親を拒否する。optimizerとseedはリセットする。PyTorchは数値計算だけに使用し、既成重み・Tokenizer・外部生成API・Wikipediaを使わない。

最初の比較は追加2,000更新、dim192／8層／4heads／batch8／CPU2threads、seed1529、LR0.0002、BF16 activation／FP32重み・optimizer・検証・推論とする。更新数、パラメーター、入力数、canonical検証損失、開発VAL9件の原文自己回帰生成を記録する。親の同じVAL結果と比較し、単純な一変数の因果比較とは主張しない。開発の採点基準・全語彙greedy生成・最大128新tokenはround3と同じで、基準を下げない。開発の生成を十分な日本語と確認するまで未見TESTを開かず、QA学習を再開しない。

```sh
python training/language/round4/prepare_boundary_focus.py
python training/language/round4/test_data.py
# 親の完了と開発評価を確認してから。既に同じrunを実行中なら重ねない。
python training/language/round4/train.py --merges 8192 --steps 2000 --dim 192 --layers 8 --heads 4 --batch 8 --threads 2 --seed 1529 --lr 0.0002 --validation-every 1000 --run boundary-focus-2000 --compile --precision bfloat16
```

語の途中の接続へ学習を集中させることで改善するかは、実際の生成評価で確認する仮説。全文の反復や意味の破綻まで解消できるとは事前に保証しない。

実際の追加2,000更新を完了し、canonical VAL損失で2,000更新の重みを選択した。開発一文は親0/9から1/9になったが、全文非ループは2/9から1/9、有効token出力は9/9から8/9へ悪化し、言語段階は不合格。`RESULTS.md`、実物checkpoint、採点、JS照合と監査で確認する。終端診断は同じ選択重みなので追加の学習・独立した品質改善とは数えない。再評価時は別のoutファイルを使い、計時値の変化で保存済み採点SHAを上書きしない。
