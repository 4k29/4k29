# TRAINから組み立てる文字単位Transformer

round4の生成は開発一文1/9にとどまり、反復8/9、不正UTF-8が1件あった。生成文の補修・tokenフィルターで隠さず、原文の表現単位を変える比較を実施する。外部重み・既成Tokenizer・生成API・Wikipedia・teacher文章・QA／instructionを使わない。

同じround3のTRAIN4,498単位、2,702,074文字から4,259文字種と頻度を取得する。UTF-8 byteの組み立て規則を、prefix長／TRAIN頻度／byte列の順で4,503個構成し、元のown byte-BPE／JS推論と同じ形式で文字を表す。語のmergeは0個。語彙4,765には6special、256byte fallbackと文字・中間prefixを含む。TRAINの正例は一文字で完結するglyphだけで、中間prefixの選択を推論時に禁止してはいない。知らないheldの文字も元のbyte fallbackのまま保存し、語彙へ追加しない。

全TRAINのtokenが原文の一文字ずつに一致し、Unicode位置で切ったprefix／suffixの独立符号化が全文と一致することを検証する。原文・分割・引用・本来のBOS／EOS・全対象の被覆は維持する。TRAINの2,706,572対象は原文文字＋4,498 EOSで、新しい独立した文章は増えていない。VAL203,967、TEST286,375対象には未知文字のbyte分割も含む。

新しい語彙なので以前の重みを読み込まず、seed1629で新しい4層／dim192／4heads／hidden768／context256のモデルを初期化する。本学習は10,000更新、batch8、CPU2threads、LR0.0005、BF16 activationのみで重み・optimizer・検証・最終推論はFP32。raw文字予測のみ。学習中のコード・データを変更しない。実更新数はcheckpoint／optimizer／resultで確認する。

文学55%、情報通信10%、環境10%、気象15%、MDN5%、農林水産省5%の抽出を維持。長さ64／128／256の条件付きbatchで周辺行確率を保持するが、batch内相関は変わる。lookback32は今回32文字前後となり、以前の32word-BPE tokenと同じbyte文脈長ではない。語彙・規模・文脈の長さ・露出token数が変わるため一変数の因果比較としない。

1,000更新の実物snapshotと、10,000更新後にcanonical VAL NLL/byteだけで選ぶ最終候補を同じ文字単位設定で比較する。開発生成を観察する前に重みを固定する。新規TEST24件はまだ開かず、日本語の基準が成立するまでQAを再開しない。開発9件・TEST24件の文書・prefix・採点基準はround3のものを保持する。

文字単位では同じ128tokenが以前より短い文になるため、生成を最大192新token（常にcontext256以内）と学習前に固定する。全語彙greedyで、文章修正・反復penaltyを使わない。このtoken上限と語彙は以前のモデルと異なる。公平なsnapshot比較は今回の同一語彙・同一4層モデルの1000／最終間で行い、以前の生成長との違いを性能と混同しない。第一文の文法2・接続2・合計9以上、有効token・終止と、文学／現代説明文の各80%以上・全文非ループ90%以上の基準は緩めない。

```sh
python training/language/round5/prepare_characters.py
python training/language/round5/test_data.py
python training/language/round5/test_batching.py
python training/language/round5/train.py --merges 4503 --steps 10000 --dim 192 --layers 4 --heads 4 --batch 8 --threads 2 --seed 1629 --validation-every 1000 --run characters-10000 --compile --precision bfloat16
```

以前の206／145／88／55ファイルの実験と公開回答モデルを保持する。予定の更新数を実完了として数えず、文字語彙への変更が会話能力・事実の正確性を保証するとは主張しない。
