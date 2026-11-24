# Round35 — human utterance-end EOS auxiliary

実optimizer更新10000回を完了。selected8000/latest10000の新しい全文84件を実読解し、両状態とも従来の厳格言語ゲートは不合格。EOS終了と最小の相槌・確認質問には限定的な改善があるが、日常12全文意味0、共通/会話DEV NLLと従来17全文は悪化したため、係数1.0は不採用。公開モデル・サイトは変更していない。

変更は、human TRAINの真の発話末尾で元のunmasked正解がstandalone改行16の場合にEOS2補助CEをcoefficient1.0追加することだけ。元の正解とR34負例prefix条件を維持し、同じRound28 full model/Adam20000/RNGから10000更新する兄弟比較。[RESULTS.md](RESULTS.md)、[REPRODUCTION.md](REPRODUCTION.md)、[全168状態出力](execution/ALL_FOUR_STATE_GENERATIONS.md)、[比較曲線](execution/paired-development.png)、[最終判定](execution/final-assessment.json)を参照。

Py/JS・raw/exportは新84/84で全文一致。既知R10分岐はNUMERICAL_LIMITS.mdに残す。全checkpoint/moments/RNG/実数/SHAはpartsとmanifestで保存。次ラウンドはEOS係数だけ0.3へ下げ、データや推論を混ぜずに比較する。過去のmechanical pending記録は当時の状態で、この最終読解が後に追加された。新TEST・独立盲検の結果ではない。
