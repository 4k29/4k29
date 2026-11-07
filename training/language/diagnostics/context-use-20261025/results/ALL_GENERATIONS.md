# Fixed-checkpoint raw generations

Python raw FP32 only. Full prefixes and all continuations shown without repair. Mechanical repetition is not semantic quality onset.

## train-realpersona-01 / correct

Split: TRAIN; source: realpersona

Full prefix:

```text
そうですか。じゃあ、私も無理かもです。
焼きそばよりラーメンのが美味しい気がします

```

Continuation:

```text
おお！ありがとうございます！
```

EOS: True; generated non-EOS IDs: 13

Token IDs including EOS when emitted:

```text
[653, 653, 1323, 642, 639, 630, 627, 635, 823, 946, 619, 5036, 1323, 2]
```

## train-realpersona-01 / mismatched

Split: TRAIN; source: realpersona

Full prefix:

```text
今年はなにか夏らしいことはしましたか？
久々に花火を見に行きました。あなたは？

```

Continuation:

```text
花火が好きですね。花火が好きですね。
そうですね。花火が好きなので好きなので好きですか？
```

EOS: True; generated non-EOS IDs: 38

Token IDs including EOS when emitted:

```text
[1150, 1028, 630, 992, 649, 5096, 749, 623, 1150, 1028, 630, 992, 649, 5096, 749, 5029, 5040, 5096, 749, 623, 1150, 1028, 630, 992, 649, 625, 616, 629, 992, 649, 625, 616, 629, 992, 649, 5096, 632, 1004, 2]
```

## train-realpersona-01 / none

Split: TRAIN; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-realpersona-02 / correct

Split: TRAIN; source: realpersona

Full prefix:

```text
出てくる蒸気の音とかちょっと怖いですよね
そうそう、爆発するんじゃないかって、へっぴり腰で作ってます。

```

Continuation:

```text
そうなんですね、それは何か作るのが好きですか？
```

EOS: True; generated non-EOS IDs: 19

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 617, 4975, 628, 717, 632, 840, 626, 616, 630, 992, 649, 5096, 632, 1004, 2]
```

## train-realpersona-02 / mismatched

Split: TRAIN; source: realpersona

Full prefix:

```text
入りづらい雰囲気のところありますよねー
まぁ大阪来て3年目なんですがまだ慣れていないのもあります。

```

Continuation:

```text
そうなんですね。今は大阪のお話ありがとうございました！
```

EOS: True; generated non-EOS IDs: 22

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 623, 779, 628, 694, 1843, 616, 653, 863, 4969, 630, 627, 635, 823, 946, 619, 5415, 1323, 2]
```

## train-realpersona-02 / none

Split: TRAIN; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-realpersona-03 / correct

Split: TRAIN; source: realpersona

Full prefix:

```text
雨の日が交互に来られるときついです。
気圧変化が激しそうです

```

Continuation:

```text
気象庁ホームページでは、気象庁ホームページに掲載されていますか？
気象庁ホームページでは、気象庁ホームページの気象庁ホームページでは気象庁ホームページでは気象庁ホームページでは気象庁ホームページで気象庁ホームページでは気象庁ホームページで気象庁ホームページでは気象庁ホームページで気象庁ホームページで気象庁ホームページでは気象庁ホームページで気象庁ホームページで気象庁ホームページで気象庁ホームページで気象庁ホームページで気象庁ホームページで気象庁ホームページで気象庁ホームページ
```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[687, 899, 1260, 1125, 648, 805, 5250, 629, 628, 617, 687, 899, 1260, 1125, 648, 805, 5250, 618, 1926, 1557, 5169, 5036, 632, 1004, 16, 687, 899, 1260, 1125, 648, 805, 5250, 629, 628, 617, 687, 899, 1260, 1125, 648, 805, 5250, 616, 687, 899, 1260, 1125, 648, 805, 5250, 629, 628, 687, 899, 1260, 1125, 648, 805, 5250, 629, 628, 687, 899, 1260, 1125, 648, 805, 5250, 629, 628, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 628, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 628, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 628, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250, 629, 687, 899, 1260, 1125, 648, 805, 5250]
```

## train-realpersona-03 / mismatched

Split: TRAIN; source: realpersona

Full prefix:

```text
あら？鶏肉がない感じですか？
今冷蔵庫の中すっからかんです。

```

Continuation:

```text
そうですね。私も好きなんですか？
```

EOS: True; generated non-EOS IDs: 13

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 699, 638, 992, 649, 625, 643, 5096, 632, 1004, 2]
```

## train-realpersona-03 / none

Split: TRAIN; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-realpersona-04 / correct

Split: TRAIN; source: realpersona

Full prefix:

```text
こんばんは！
好きな食べ物は何ですか？

```

Continuation:

```text
好きですね。お好きなんですか？
```

EOS: True; generated non-EOS IDs: 13

Token IDs including EOS when emitted:

```text
[992, 649, 5096, 749, 623, 653, 992, 649, 625, 643, 5096, 632, 1004, 2]
```

## train-realpersona-04 / mismatched

Split: TRAIN; source: realpersona

Full prefix:

```text
ああ、そういえば好きです
いいですよね！声が。

```

Continuation:

```text
そうなんですね。私も好きなので好きなんですか？
```

EOS: True; generated non-EOS IDs: 20

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 992, 649, 625, 643, 5096, 632, 1004, 2]
```

## train-realpersona-04 / none

Split: TRAIN; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-realpersona-05 / correct

Split: TRAIN; source: realpersona

Full prefix:

```text
そこまでオープンにできないですよね
これが数十年連れ添った夫婦なら別なのかもしれないですけどね

```

Continuation:

```text
そうですね、それは大変ですね。それは大変ですね。
そうなんですね。それは大変ですね。
```

EOS: True; generated non-EOS IDs: 31

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 617, 4975, 628, 694, 787, 5096, 749, 623, 4975, 628, 694, 787, 5096, 749, 5029, 5040, 625, 643, 5096, 749, 623, 4975, 628, 694, 787, 5096, 749, 623, 2]
```

## train-realpersona-05 / mismatched

Split: TRAIN; source: realpersona

Full prefix:

```text
ギャグ系は無心で見れるので私も大好きです。
しょうもない事で笑いたい日なんかは最高ですよね！

```

Continuation:

```text
そうなんですね。私も好きなので。
そうなんですね。私も好きなので好きなので。
そうなんですね。私も好きなので好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。

```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029]
```

## train-realpersona-05 / none

Split: TRAIN; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-realpersona-06 / correct

Split: TRAIN; source: realpersona

Full prefix:

```text
全然です。サスペンダーつけてやろうかと思うくらいダサいです。
我が家は中学３年と１年で男女なので制服×２セット全て買いました。

```

Continuation:

```text
そうですね。それは一番ですね。それは一番ですか？
```

EOS: True; generated non-EOS IDs: 18

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 4975, 628, 661, 1251, 5096, 749, 623, 4975, 628, 661, 1251, 5096, 632, 1004, 2]
```

## train-realpersona-06 / mismatched

Split: TRAIN; source: realpersona

Full prefix:

```text
ふふふ。でも、夢ってたしか、浅い眠りのときに観るっていいますよね
そうなんですか？深い眠りの時は脳もネンネしてるのかな？

```

Continuation:

```text
そうですね、今はまだまだまだまだまだまだまだまだまだまだなと思ってますね。
そうなんですね。私もそこまで寝てるのが好きなんですよね。
そうなんですね。私も最近は何かお好きなんですか？
```

EOS: True; generated non-EOS IDs: 78

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 617, 779, 628, 633, 645, 633, 645, 633, 645, 633, 645, 633, 645, 633, 645, 633, 645, 633, 645, 633, 645, 633, 645, 625, 627, 720, 4950, 5036, 749, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 641, 640, 5103, 1214, 621, 626, 616, 630, 992, 649, 625, 643, 5096, 647, 749, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 871, 972, 628, 717, 632, 653, 992, 649, 625, 643, 5096, 632, 1004, 2]
```

## train-realpersona-06 / none

Split: TRAIN; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-jmrd-01 / correct

Split: TRAIN; source: jmrd

Full prefix:

```text
海と船のシーンが満載で、それらが好きな方にはお薦めの映画です
なるほど

```

Continuation:

```text
海外の海外の海外の海外の海外の海外の海外の海外の海外の海外の海外の海外海の海岸に海岸に海岸に海岸に海岸に沿って海岸に沿って海岸に沿って海岸に沿って海岸に沿って海岸に沿って海岸に沿って海岸に沿いきます。海岸の岸の岸に沿いき、海岸の岸の岸に沿岸に沿いき、海岸の岸の岸近くに沿いき、海岸の岸の岸近くの岸近くに地盤が出てきてしまうことがあります。
海岸の岸の岸の岸の岸近くに沿岸岸近くに沿岸近くに沿岸岸の岸近くに沿岸近くなって
```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[824, 810, 616, 824, 810, 616, 824, 810, 616, 824, 810, 616, 824, 810, 616, 824, 810, 616, 824, 810, 616, 824, 810, 616, 824, 810, 616, 824, 810, 616, 824, 810, 616, 824, 810, 824, 616, 824, 1489, 618, 824, 1489, 618, 824, 1489, 618, 824, 1489, 618, 824, 1489, 618, 1515, 4950, 824, 1489, 618, 1515, 4950, 824, 1489, 618, 1515, 4950, 824, 1489, 618, 1515, 4950, 824, 1489, 618, 1515, 4950, 824, 1489, 618, 1515, 4950, 824, 1489, 618, 1515, 4950, 824, 1489, 618, 1515, 619, 649, 4944, 824, 1489, 616, 1489, 616, 1489, 618, 1515, 619, 649, 617, 824, 1489, 616, 1489, 616, 1489, 618, 1515, 1489, 618, 1515, 619, 649, 617, 824, 1489, 616, 1489, 616, 1489, 972, 644, 618, 1515, 619, 649, 617, 824, 1489, 616, 1489, 616, 1489, 972, 644, 616, 1489, 972, 644, 618, 681, 1390, 630, 664, 621, 649, 621, 5138, 635, 4951, 5045, 4954, 824, 1489, 616, 1489, 616, 1489, 616, 1489, 616, 1489, 972, 644, 618, 1515, 1489, 1489, 972, 644, 618, 1515, 1489, 972, 644, 618, 1515, 1489, 1489, 616, 1489, 972, 644, 618, 1515, 1489, 972, 644, 625, 4950]
```

## train-jmrd-01 / mismatched

Split: TRAIN; source: jmrd

Full prefix:

```text
知らないです。ぜひお願いします。
ミッキーなどは出てきませんが、一応ディズニー映画です

```

Continuation:

```text
そうですね。あなたは何かお好きなんですか？
```

EOS: True; generated non-EOS IDs: 18

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 642, 625, 620, 628, 717, 632, 653, 992, 649, 625, 643, 5096, 632, 1004, 2]
```

## train-jmrd-01 / none

Split: TRAIN; source: jmrd

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-jmrd-02 / correct

Split: TRAIN; source: jmrd

Full prefix:

```text
こんにちは
タイトルタイタニック

```

Continuation:

```text
最近は、最近のゲームを使ってたのですか？
```

EOS: True; generated non-EOS IDs: 19

Token IDs including EOS when emitted:

```text
[871, 972, 628, 617, 871, 972, 616, 1820, 648, 805, 624, 814, 4950, 620, 616, 629, 634, 632, 1004, 2]
```

## train-jmrd-02 / mismatched

Split: TRAIN; source: jmrd

Full prefix:

```text
こんにちは、よろしくお願いします

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-jmrd-02 / none

Split: TRAIN; source: jmrd

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-jmrd-03 / correct

Split: TRAIN; source: jmrd

Full prefix:

```text
おはようございます。
こんにちは。よろしくどーぞ。

```

Continuation:

```text
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
お願いします。
今日は何を食べましたか？
```

EOS: True; generated non-EOS IDs: 82

Token IDs including EOS when emitted:

```text
[653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 653, 1752, 619, 5024, 779, 708, 628, 717, 624, 1011, 798, 5415, 632, 1004, 2]
```

## train-jmrd-03 / mismatched

Split: TRAIN; source: jmrd

Full prefix:

```text
迫力のある戦闘シーンが見どころです。
そうなのですね

```

Continuation:

```text
そうですね。あなたはどんなものがあって。
そうですね。あなたはどんなものが多いですか？
```

EOS: True; generated non-EOS IDs: 32

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 642, 625, 620, 628, 660, 5098, 4988, 630, 642, 4950, 5029, 5040, 5096, 749, 623, 642, 625, 620, 628, 660, 5098, 4988, 630, 825, 619, 5096, 632, 1004, 2]
```

## train-jmrd-03 / none

Split: TRAIN; source: jmrd

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-jmrd-04 / correct

Split: TRAIN; source: jmrd

Full prefix:

```text
篠原涼子
ストーリーは

```

Continuation:

```text
今日は、今日は、今日はお昼ご飯を食べてみたいな。
お昼ご飯は食べてみたいですね。
そうですね。お昼は食べてみたいですね。
そうですね。今日は食べてみたいな。
そうですね。今日は食べたいですね。
そうですね。今日は食べたいですね。
そうですね。今日は食べたいですね。
そうですね。お昼は食べたいですね。
そうですね。今日は食べたいですね。
そうですね。お昼は食べたいですね。
そうですね。今日は食べたいですね。
そうですね。今日は食べたいですね。
そうですね。今日は食べたい
```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[779, 708, 628, 617, 779, 708, 628, 617, 779, 708, 628, 653, 1695, 823, 1435, 624, 1011, 798, 621, 692, 620, 619, 625, 5029, 653, 1695, 823, 1435, 628, 1011, 798, 621, 692, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 653, 1695, 628, 1011, 798, 621, 692, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 779, 708, 628, 1011, 798, 621, 692, 620, 619, 625, 5029, 5040, 5096, 749, 623, 779, 708, 628, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 779, 708, 628, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 779, 708, 628, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 653, 1695, 628, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 779, 708, 628, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 653, 1695, 628, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 779, 708, 628, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 779, 708, 628, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 779, 708, 628, 1011, 798, 620, 619]
```

## train-jmrd-04 / mismatched

Split: TRAIN; source: jmrd

Full prefix:

```text
こんにちは。
お願いします。

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-jmrd-04 / none

Split: TRAIN; source: jmrd

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-jmrd-05 / correct

Split: TRAIN; source: jmrd

Full prefix:

```text
ファンタスティック・ビーストと魔法使いの旅をご紹介します。
観たことがないのですが、どんな感じのお話ですか？

```

Continuation:

```text
はい、最近はどんなものを使ってたのでしょうか？
```

EOS: True; generated non-EOS IDs: 18

Token IDs including EOS when emitted:

```text
[628, 619, 617, 871, 972, 628, 660, 5098, 4988, 624, 814, 4950, 620, 616, 629, 5189, 632, 1004, 2]
```

## train-jmrd-05 / mismatched

Split: TRAIN; source: jmrd

Full prefix:

```text
あまりみません。アニメであれば見ますが。
アクションでもダイハードは入門編としてご紹介したいと思いますがいかがですか。

```

Continuation:

```text
アニメはアニメはアニメはありますか？
```

EOS: True; generated non-EOS IDs: 13

Token IDs including EOS when emitted:

```text
[5418, 849, 628, 5418, 849, 628, 5418, 849, 628, 4969, 5036, 632, 1004, 2]
```

## train-jmrd-05 / none

Split: TRAIN; source: jmrd

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## train-jmrd-06 / correct

Split: TRAIN; source: jmrd

Full prefix:

```text
ある日、時空を超えて再び２体のターミネーターが送り込まれる。
２体なんですね。

```

Continuation:

```text
そうですね。今日はどこまで行ってみたいです。
そうなんですね。今日は行きたいと思いますか？
```

EOS: True; generated non-EOS IDs: 34

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 779, 708, 628, 660, 640, 5103, 674, 4950, 692, 620, 619, 5129, 5040, 625, 643, 5096, 749, 623, 779, 708, 628, 674, 649, 620, 619, 5230, 619, 5036, 632, 1004, 2]
```

## train-jmrd-06 / mismatched

Split: TRAIN; source: jmrd

Full prefix:

```text
ふむふむ。
パンドラの地下には、希少鉱物アンオブタニウムの莫大な鉱床が眠っています。

```

Continuation:

```text
アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アン・アンアン・アン・アン・ア
```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711, 655, 711, 655, 691, 711, 655, 691, 711, 655, 691, 711]
```

## train-jmrd-06 / none

Split: TRAIN; source: jmrd

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## content-native-00 / correct

Split: exposed-DEV; source: realpersona

Full prefix:

```text
私もウォーキングを始めましたよ！
同じですね！これまでの経験上、歩くことが健康によいと感じています。

```

Continuation:

```text
そうなんですね！私も行きたいと思います！
```

EOS: True; generated non-EOS IDs: 16

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 1323, 699, 638, 674, 649, 620, 619, 5230, 619, 5036, 1323, 2]
```

## content-native-00 / mismatched

Split: exposed-DEV; source: realpersona

Full prefix:

```text
R指定さんは聞いたことあります！すごいですよね！
めっっちゃ強いんですよー！もう引退しましたが、、

```

Continuation:

```text
そうですね！
```

EOS: True; generated non-EOS IDs: 4

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 1323, 2]
```

## content-native-00 / none

Split: exposed-DEV; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## content-native-01 / correct

Split: exposed-DEV; source: realpersona

Full prefix:

```text
そうなんですね！バイクが子供みたいなかんじですかね？
そうですね！高校生の時に買ったバイクが実家に残っててそれをレストアしてのってます！

```

Continuation:

```text
そうなんですね！それはあまり買ってみたいですね！
```

EOS: True; generated non-EOS IDs: 19

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 1323, 4975, 628, 642, 633, 639, 1379, 4950, 692, 620, 619, 5096, 749, 1323, 2]
```

## content-native-01 / mismatched

Split: exposed-DEV; source: realpersona

Full prefix:

```text
夢中になってた一人です。最近久しぶりにネットフリックスで見ましたが、良かったですよ。
なんか童心に帰りますね。私の子どもの頃はバビル2世かな？

```

Continuation:

```text
そうですね。それはあまり見てみたいな感じですね。
そうなんですね。私も子供の子供の子供が好きなので。
そうなんですね。子供の子供が好きなので。
そうなんですね。子供が好きなので。
そうなんですね。子供が好きなので。
子供が好きなのでしょうか？
```

EOS: True; generated non-EOS IDs: 102

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 4975, 628, 642, 633, 639, 670, 621, 692, 620, 619, 625, 952, 685, 5096, 749, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 709, 943, 616, 709, 943, 616, 709, 943, 630, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 709, 943, 616, 709, 943, 630, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 709, 943, 630, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 709, 943, 630, 992, 649, 625, 616, 629, 5029, 709, 943, 630, 992, 649, 625, 616, 629, 5189, 632, 1004, 2]
```

## content-native-01 / none

Split: exposed-DEV; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## content-native-02 / correct

Split: exposed-DEV; source: realpersona

Full prefix:

```text
おはようとこんにちは、その切替はいつからなのかなって
うーん、それは難しいですよね。こんばんはは、５時頃からって認識してますが。

```

Continuation:

```text
そうなんですね。今日は何かおすすめの時期はありますか？
```

EOS: True; generated non-EOS IDs: 23

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 623, 779, 708, 628, 717, 632, 653, 634, 634, 659, 616, 701, 961, 628, 4969, 5036, 632, 1004, 2]
```

## content-native-02 / mismatched

Split: exposed-DEV; source: realpersona

Full prefix:

```text
それが一番の対策なのかもです。暑さもすごいですし。
暑いですよね。自分は基本仕事がテレワークなので、家から出ずに済んで助かってます。

```

Continuation:

```text
そうなんですね。今は何をしてますか？
```

EOS: True; generated non-EOS IDs: 14

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 623, 779, 628, 717, 624, 4946, 5036, 632, 1004, 2]
```

## content-native-02 / none

Split: exposed-DEV; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## content-native-03 / correct

Split: exposed-DEV; source: realpersona

Full prefix:

```text
おお、いいですね。どれが効くとかですか？味ですか？
サジーっていうやつなんですけど、酸っぱいので美味しく飲める方法を探してます。

```

Continuation:

```text
そうなんですね。おいしいですね。おいしいですね。
```

EOS: True; generated non-EOS IDs: 18

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 623, 653, 619, 5035, 5096, 749, 623, 653, 619, 5035, 5096, 749, 623, 2]
```

## content-native-03 / mismatched

Split: exposed-DEV; source: realpersona

Full prefix:

```text
隔離とマスクは大事だと思いました。でも、あんまり気にしても仕方ないとも思ってましたよー
そうですよね。症状は軽症程度ですんだんですか？

```

Continuation:

```text
そうですね。それは大変ですね。今は大変ですね。
そうですね。今は今は一番好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんです
```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 4975, 628, 694, 787, 5096, 749, 623, 779, 628, 694, 787, 5096, 749, 5029, 5040, 5096, 749, 623, 779, 628, 779, 628, 661, 1251, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096]
```

## content-native-03 / none

Split: exposed-DEV; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## content-native-04 / correct

Split: exposed-DEV; source: realpersona

Full prefix:

```text
おおぉ。ちなみに最近の気温は何度位ですか？
33～36度が続いてました　昼間はできるだけ外に出ないようにしてます

```

Continuation:

```text
そうですね。今日はもう少し暑いですね。
そうですね。今日は暑いので。
そうですね。暑いので暑いので暑いので。
そうなんですね。暑いのは暑いので暑いので。
そうなんですね。暑いのは暑いので。
そうなんですね。暑いのは暑いので暑いので。
暑いのは暑いので暑いので暑いので。
暑いのは暑いので暑いので暑いので。
暑いのは暑いので暑いので暑いので暑いので。
暑いのは暑いので暑いので暑いので暑いので暑いので。
暑いのは暑いので暑いので暑いの
```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 779, 708, 628, 5274, 828, 622, 2121, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 779, 708, 628, 2121, 619, 616, 629, 5029, 5040, 5096, 749, 623, 2121, 619, 616, 629, 2121, 619, 616, 629, 2121, 619, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 2121, 619, 616, 628, 2121, 619, 616, 629, 2121, 619, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 2121, 619, 616, 628, 2121, 619, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 2121, 619, 616, 628, 2121, 619, 616, 629, 2121, 619, 616, 629, 5029, 2121, 619, 616, 628, 2121, 619, 616, 629, 2121, 619, 616, 629, 2121, 619, 616, 629, 5029, 2121, 619, 616, 628, 2121, 619, 616, 629, 2121, 619, 616, 629, 2121, 619, 616, 629, 5029, 2121, 619, 616, 628, 2121, 619, 616, 629, 2121, 619, 616, 629, 2121, 619, 616, 629, 2121, 619, 616, 629, 5029, 2121, 619, 616, 628, 2121, 619, 616, 629, 2121, 619, 616, 629, 2121, 619, 616, 629, 2121, 619, 616, 629, 2121, 619, 616, 629, 5029, 2121, 619, 616, 628, 2121, 619, 616, 629, 2121, 619, 616, 629, 2121, 619, 616]
```

## content-native-04 / mismatched

Split: exposed-DEV; source: realpersona

Full prefix:

```text
あーパサパサ感が？
小学校の頃給食で出たツナがあまりに美味しくなさすぎて、それで食べれなくなりましたね。

```

Continuation:

```text
おお！おお！おいしそう！
```

EOS: True; generated non-EOS IDs: 11

Token IDs including EOS when emitted:

```text
[653, 653, 1323, 653, 653, 1323, 653, 619, 622, 5040, 1323, 2]
```

## content-native-04 / none

Split: exposed-DEV; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## content-native-05 / correct

Split: exposed-DEV; source: realpersona

Full prefix:

```text
ドラマとか沢山出ておられる！
はい、女優さんです！お芝居も好きですし、お顔やスタイルも大好きです！

```

Continuation:

```text
あなたは？
```

EOS: True; generated non-EOS IDs: 5

Token IDs including EOS when emitted:

```text
[642, 625, 620, 628, 1004, 2]
```

## content-native-05 / mismatched

Split: exposed-DEV; source: realpersona

Full prefix:

```text
今もやってますがスマホゲームと読書でしょうか。
読書ですか！私も好きです。どんな本を読んでいるんですか？

```

Continuation:

```text
読書館で読んでるんですね。読書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書書
```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[1053, 807, 1805, 629, 1053, 5144, 626, 643, 5096, 749, 623, 1053, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807, 807]
```

## content-native-05 / none

Split: exposed-DEV; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## content-native-06 / correct

Split: exposed-DEV; source: realpersona

Full prefix:

```text
ストックの層ってところですかね。
はい、どんどん上に積み重なっていくので。何を入れたか、メモするようにしています。

```

Continuation:

```text
そうなんですね。それはどんなものが多いですか？
```

EOS: True; generated non-EOS IDs: 17

Token IDs including EOS when emitted:

```text
[5040, 625, 643, 5096, 749, 623, 4975, 628, 660, 5098, 4988, 630, 825, 619, 5096, 632, 1004, 2]
```

## content-native-06 / mismatched

Split: exposed-DEV; source: realpersona

Full prefix:

```text
まあやってない人からすればそうですよね、私も分からないです
実際に音楽が流れる感じなんですか？

```

Continuation:

```text
そうですね、音楽が好きなので好きなので好きなんですよね。
そうなんですね、音楽が好きなので好きなので好きなんですか？
```

EOS: True; generated non-EOS IDs: 51

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 617, 1012, 1274, 630, 992, 649, 625, 616, 629, 992, 649, 625, 616, 629, 992, 649, 625, 643, 5096, 647, 749, 5029, 5040, 625, 643, 5096, 749, 617, 1012, 1274, 630, 992, 649, 625, 616, 629, 992, 649, 625, 616, 629, 992, 649, 625, 643, 5096, 632, 1004, 2]
```

## content-native-06 / none

Split: exposed-DEV; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## content-native-07 / correct

Split: exposed-DEV; source: realpersona

Full prefix:

```text
パスタは簡単でおいしいのでいいです！
ほんとに！食べたくなってきましたー。明日はパスタになる予感がしますよ。

```

Continuation:

```text
そうですね。おいしいですね！
```

EOS: True; generated non-EOS IDs: 10

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 653, 619, 5035, 5096, 749, 1323, 2]
```

## content-native-07 / mismatched

Split: exposed-DEV; source: realpersona

Full prefix:

```text
勉強が関係なくなると、色々興味が出てきたりしますよね。
そうそう、勉強だと思うとやりたくないんですよねー。

```

Continuation:

```text
そうですね。それはどんな感じですか？
```

EOS: True; generated non-EOS IDs: 13

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 4975, 628, 660, 5098, 952, 685, 5096, 632, 1004, 2]
```

## content-native-07 / none

Split: exposed-DEV; source: realpersona

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## fresh-mrmp-00 / correct

Split: exposed-DEV; source: mrmp

Full prefix:

```text
どんな仕事内容か聞いたりしたことありますか？
帰って来るとポップコーンの香りがしました

```

Continuation:

```text
おお！おお！おお！おお！お願いいたします！
```

EOS: True; generated non-EOS IDs: 19

Token IDs including EOS when emitted:

```text
[653, 653, 1323, 653, 653, 1323, 653, 653, 1323, 653, 653, 1323, 653, 1752, 619, 5071, 622, 5036, 1323, 2]
```

## fresh-mrmp-00 / mismatched

Split: exposed-DEV; source: mrmp

Full prefix:

```text
そうです、シンプルで遊びやすかった記憶があります。
なるほど、バトル系がお好きですか？

```

Continuation:

```text
そうですね。あなたはどんなものが好きですか？
```

EOS: True; generated non-EOS IDs: 17

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 642, 625, 620, 628, 660, 5098, 4988, 630, 992, 649, 5096, 632, 1004, 2]
```

## fresh-mrmp-00 / none

Split: exposed-DEV; source: mrmp

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## fresh-mrmp-01 / correct

Split: exposed-DEV; source: mrmp

Full prefix:

```text
自分の子育てはたいへんだけど
赤ちゃん連れのお母さんもいらっしゃるのは癒されますね

```

Continuation:

```text
そうですね、お母さんはお母さんの子供の子供の子供がお母さんの子供の子供の子供の子供の子供の子供の子供の子供が子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供子を子にしております子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供の子供たちが子供の子供の子供の子供の子供の子供の子供の子供
```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 617, 653, 911, 5086, 628, 653, 911, 5086, 616, 709, 943, 616, 709, 943, 616, 709, 943, 630, 653, 911, 5086, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 630, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 709, 624, 709, 618, 4946, 653, 639, 5036, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 620, 663, 630, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943, 616, 709, 943]
```

## fresh-mrmp-01 / mismatched

Split: exposed-DEV; source: mrmp

Full prefix:

```text
人ごみのストレス的にもコロナ的にもですよね。
そうそう。コロナでますますあの混雑が嫌になりました。

```

Continuation:

```text
そうですね。それはどんなものが好きなので。
そうですね。私も好きなので。
そうですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなので。
そうなんですね。私も好きなの
```

EOS: False; generated non-EOS IDs: 192

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 4975, 628, 660, 5098, 4988, 630, 992, 649, 625, 616, 629, 5029, 5040, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616, 629, 5029, 5040, 625, 643, 5096, 749, 623, 699, 638, 992, 649, 625, 616]
```

## fresh-mrmp-01 / none

Split: exposed-DEV; source: mrmp

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## fresh-mrmp-02 / correct

Split: exposed-DEV; source: mrmp

Full prefix:

```text
お土産屋さんとかに売ってるんてますかね
そうなんですね！ロープウェイにのって行かないと無いのかと思ってた笑

```

Continuation:

```text
そうですね、今はどんな感じですか？
```

EOS: True; generated non-EOS IDs: 13

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 617, 779, 628, 660, 5098, 952, 685, 5096, 632, 1004, 2]
```

## fresh-mrmp-02 / mismatched

Split: exposed-DEV; source: mrmp

Full prefix:

```text
練習したのはだし巻きとオムライスですね。
オムライスは自分で作ったことないですね。親子丼とかはどうでしょうか？

```

Continuation:

```text
そうですね。それはあまり作るので作るので作るので。
そうですね。あなたは何か作るのが好きですか？
```

EOS: True; generated non-EOS IDs: 41

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 623, 4975, 628, 642, 633, 639, 840, 626, 616, 629, 840, 626, 616, 629, 840, 626, 616, 629, 5029, 5040, 5096, 749, 623, 642, 625, 620, 628, 717, 632, 840, 626, 616, 630, 992, 649, 5096, 632, 1004, 2]
```

## fresh-mrmp-02 / none

Split: exposed-DEV; source: mrmp

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## fresh-mrmp-03 / correct

Split: exposed-DEV; source: mrmp

Full prefix:

```text
わあ・・
スカイダイビング人生に一回はしてみたいです

```

Continuation:

```text
そうですね、今日は何を食べたいですか？
```

EOS: True; generated non-EOS IDs: 16

Token IDs including EOS when emitted:

```text
[5040, 5096, 749, 617, 779, 708, 628, 717, 624, 1011, 798, 620, 619, 5096, 632, 1004, 2]
```

## fresh-mrmp-03 / mismatched

Split: exposed-DEV; source: mrmp

Full prefix:

```text
そうですね。食べず嫌いもありますし。
例えば何だったんですか？

```

Continuation:

```text
食べたいですね。食べたいですね。食べたいですね。
そうですね。食べたいですね。食べたいですね。
そうですね。食べたいですね。食べたいですね。
そうですね。食べたいですね。食べたいですね。
そうですね。食べたいですね。食べたいですね。
そうですね。食べたいですね。食べたいですね。
そうですね。食べたいですね。
```

EOS: True; generated non-EOS IDs: 122

Token IDs including EOS when emitted:

```text
[1011, 798, 620, 619, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 5029, 5040, 5096, 749, 623, 1011, 798, 620, 619, 5096, 749, 623, 2]
```

## fresh-mrmp-03 / none

Split: exposed-DEV; source: mrmp

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

## fresh-mrmp-04 / correct

Split: exposed-DEV; source: mrmp

Full prefix:

```text
我が家は洗面所問題で
あったとしてもどうでも良くなっちゃいます

```

Continuation:

```text
今日はお仕事をしてもらうのですか？
```

EOS: True; generated non-EOS IDs: 15

Token IDs including EOS when emitted:

```text
[779, 708, 628, 653, 984, 671, 624, 4946, 638, 636, 635, 616, 5096, 632, 1004, 2]
```

## fresh-mrmp-04 / mismatched

Split: exposed-DEV; source: mrmp

Full prefix:

```text
こんばんわ。よろしくお願いしますね。
こんばんは。お願いします。

```

Continuation:

```text
今日は何を食べましたか？
```

EOS: True; generated non-EOS IDs: 10

Token IDs including EOS when emitted:

```text
[779, 708, 628, 717, 624, 1011, 798, 5415, 632, 1004, 2]
```

## fresh-mrmp-04 / none

Split: exposed-DEV; source: mrmp

Full prefix:

```text

```

Continuation:

```text
こんにちは！
```

EOS: True; generated non-EOS IDs: 6

Token IDs including EOS when emitted:

```text
[640, 643, 618, 663, 628, 1323, 2]
```

