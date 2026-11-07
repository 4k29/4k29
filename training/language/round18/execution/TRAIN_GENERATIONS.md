# Posthoc TRAIN raw generations — not unseen or language-gate evidence

Frozen at logged5400 before generation, after training started. Old/new greedy full vocabulary, max192, true EOS, Python1thread. No source lookup enters generation, no output repair. These three short TRAIN sources are excluded from gate and weight/hyperparameter selection.

## train-diagnostic-0

https://www.maff.go.jp/j/kids/agri/ine/i03.html

Opening:

```text
平成元年～6年にかけておこなわれた「スーパーライ
```

old full continuation:

```text
)」を「スーパーソナー」ということがあります。
このように、「スケール」のスケールは、スケールのスケールを使用して、スケールがスケールに変換されることができます。
このスケールは、スページのスコードのスタイルストアーケーションを使用して、スページのストリームのスタイルを使用して、スタイルを使用して、スペースのストリームに使用することができます。
このスタイルストリームのスタイルを使用
```

new full continuation:

```text
ス」の「スーパーソナス」のスケールがスケールになってしまいます。 ここでは、スケールのスケールがスケールにあることから、スケールのスケールがスケールにスケールに変わることができます。
この場合、スケールはスケールによって異なる URL があります。 この場合、この例では、 URL が URL と URL と同様に異なる URL が含まれています。
```

## train-diagnostic-1

https://www.maff.go.jp/j/kids/agri/ine/i04.html

Opening:

```text
分げつがでそろったら、「中干し」といって、田んぼ
```

old full continuation:

```text
はいっぱいにしてしまった。
「ああ、ここへ行ってるかい。」
と僕はいつまでも、僕はいっぱいに言いながら、いつまでも、僕の心持ちをつけて、僕の心をひとりとりあがりました。
「ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、ああ、あ、ああ、あ、あ、ああ、あ、ああ、あ、あ、あ、あ、あ、ああ、あ、あ、あ
```

new full continuation:

```text
がいっぱいとこにいました。
「いや、いや、いや、いやだ、ここにいくらかないか。」
とおじいさんが、かわらいました。
「いや、いや、いや、いや、いや、いや、いやだよ。」
といいました。
「いや、いや、いや、いや、いや、いやだ、いやだ、いやだよ。」
といいました。
「いや、いや、いや、いやだ、いやだ、いやだ、いいだ、いやだ、いやだ、いやだ、いやだ、いやだ、いやだ、だ、だ、だ、いやだ、だ、だ、いやだ、だ、だ、だ、だ、だ、だ、だ、だ、だ
```

## train-diagnostic-2

https://www.maff.go.jp/j/kids/agri/ine/i01.html

Opening:

```text
イネは、中国南部の雲南～ラオス、タイ、ビルマ周辺
```

old full continuation:

```text
の大規模な地震の被害をもたらした現象に基づく数値が10万人以上に高い状況となります。このような状況を「昭和21年（1946年）」、「昭和21年（1946年）」、「昭和11年（1946年）」の合計した現象を比較して19年）の平均で最大の比率が高く、次のとおりです。
```

new full continuation:

```text
の広い範囲で大規模の推定されることが分かると考えられています。このため、最大クラスの平均気温は平均気温が平均で最大風速となることがあります。このため、平均気温が日本に影響する可能性があるため、平均気温が平均気温が平均気温が高くなることが分かったことが分かったことが分かったことが分かったことから、その中で風速く、高気温が高かったことから、平均気温が高くなることが分かったことが分かるのですが、このような場合には、平均気温が高くなっています。このため、気温が高いと言います。このため、気温が日本にあると言います。このような場所で気温が日本にあった
```

