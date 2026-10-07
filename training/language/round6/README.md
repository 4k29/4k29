# 自作文字モデルの原文追加学習

round5は10,000実更新で一文2/9→3/9となったが、全文の反復と意味の崩れで不合格だった。canonical VAL NLL/byteは最終まで低下したので、今回も教師文やQAを追加せず、同じ原文・文字語彙・4層モデルのまま、保存したown最良重みだけから追加10,000更新を試す。

予定回数は完了回数ではない。新規文書0件。親の実optimizerカウンター10000、ランダム初期化のown系譜、設定・TRAIN／held／Tokenizer・SHAを学習前に検証する。昔の別分割に露出した重み、外部モデル、Wikipedia、文章補修、反復penalty、QAは使わない。optimizerをリセットしseed1729、LR0.00015を使うため、追加露出だけの因果比較とはしない。

CPU2threads、batch8、4層／dim192／4heads／context256、BF16 activation、FP32重み・optimizer・検証・推論。canonical抽出・length bucket・lookback32・全原文ラベルを親と同じにする。停止／復帰は学習コードとデータの完全同一性を要求し、RNG・optimizerを保存する。

選択はcanonical VAL byte NLLだけ。親が最良なら子0更新重みのままと記録し、予定10,000を改善した系譜へ自動加算しない。開発9件は原文prefixから全語彙greedy最大192新token、第一文9点・文法2・接続2・終止・有効token、ジャンル別80%以上・全文非ループ90%以上を保持する。新規TEST24件は言語基準が成立するまで生成しない。QA・公開モデルへの移行もしない。

```sh
python training/language/round6/train.py --merges 4503 --steps 10000 --dim 192 --layers 4 --heads 4 --batch 8 --threads 2 --seed 1729 --lr 0.00015 --validation-every 1000 --run character-continue-10000 --compile --precision bfloat16
```

親の原文出典、利用条件、文字語彙テスト、監査記録はround3／round5に保存されている。親の61ファイルを変更しない。
