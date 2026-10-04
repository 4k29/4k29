# 質問から全文を生成する独自Transformerの実験

公開中の文型選択用Transformerとは別の、質問と直前の会話を入力し、回答文を最初から最後まで次トークン生成する実験。回答の検索、文型への値の挿入、外部API、学習済みモデル・外部トークナイザーは生成時に使用しない。重みを乱数から初期化し、実際のAdamW更新を10,000回ずつ2候補で実行した。

**公開モデルへは採用していない。** 自然に見える文でも質問と事実を取り違え、未知の情報を答えてしまう。現在の公開モデルv7は維持する。採用判断と次の条件は `decision.json`。

## 実装

- `tokenizer.py` / `tokenizer.mjs`: 独自のbyte-level BPE。訓練文字列だけで256 byte＋384 merges＋6制御トークン、646語彙を学習。最大12 byteのpieceとUTF-8 fallbackを使う。全文の回答を1トークンにする仕組みではない。NFKC・小文字化は質問のみ。
- `prepare.py`: 承認済み本人情報と公式仕様を直接参照した手書きの回答、言い換えの質問群、Python整数から作る正確な算数ラベル。公開対話エンジンや他モデルの出力は学習目標へ使わない。
- `train.py`: 自作causal decoder、2層・4 heads・64次元・MLP128次元・文脈128トークン、116,608パラメーター。位置埋め込み、LayerNorm、残差、tanh GELU、入力embeddingと共有する出力head。質問・履歴の部分を損失から除き、回答全体を学習する。既存の自作Blockコードを共有するが、既存の重みは読み込まない。
- `semantic-candidate.js`: 訓練専用の質問の種類の補助headを加えた118,038パラメーターの別候補。補助損失0.3。生成時は補助headを使用せず、入力から全文を自由なargmaxで生成する。
- `inference.mjs`: 外部ライブラリ不要のJavaScript推論、immutableなK/V状態、全文greedy生成。プロフィールや回答一覧は読み込まない。質問が文脈長を超える場合は、切り詰めずに拒否する。

## データと検証の区別

1,738例＝1,640訓練＋40検証＋58テスト。文型の異なる質問familyを分け、算数はoperand pair全体を分ける。BPEの学習は訓練文字列のみ。ラベルには同じ既知の回答が繰り返し現れるため、知識の汎化や一般会話能力の検証ではない。

最初の候補は40検証問の正答数、同点ならtoken損失でcheckpointを選び、固定後に58テストを初めて評価した。その後、失敗の診断を受けて補助headの候補を試したため、再利用した58問の結果は開発回帰である。両候補の重みとcheckpoint選択を固定した後に別の32問を作って評価した。この32問も小規模な作成者のprobeであり、一般的な性能の推定ではない。既存のサイト評価データは学習に使用していない。

| 確認 | 全文候補 | 補助head候補 |
| --- | ---: | ---: |
| 40検証問 | 32/40 | 28/40 |
| 58問（2候補目では開発回帰） | 47/58 | 45/58 |
| 固定後の別32問 | 18/32 | 17/32 |
| 別32問の本人情報15問 | 13/15 | 11/15 |
| 別32問の未知情報4問 | 0/4 | 0/4 |

実際の失敗には、MERの説明へイヤホンの再生時間を混ぜること、Headphone (1)の質問へ数値だけを答えること、0+0を1と答えることがある。訓練損失が約0.006まで下がっても、これらは解消していない。回数だけを増やして性能向上と主張しない。

初期候補のJavaScript全文生成も58問47/58でPyTorchと一致。4つの入力のlogits差は0.0002未満。60回答のCPU時間は中央値約2.69ms、p95約6.70msで、通信とUIの演出を含まない。速さよりも、事実保持・未知情報の境界・質問理解が採用の障害になっている。

## 再実行

訓練環境はCPU版PyTorch 2.6.0。PyTorchは訓練専用で、学習済みモデルではない。

```sh
python training/dialogue/prepare.py
python training/dialogue/train.py --steps 10000 --compile-loss \
  --output /tmp/dialogue-candidate.js --artifacts-prefix /tmp/dialogue
python training/dialogue/train.py --steps 10000 --compile-loss --intent-loss 0.3 \
  --version 2026-10-04.dialogue-experimental-2 \
  --output /tmp/dialogue-semantic.js --artifacts-prefix /tmp/dialogue-semantic
python training/dialogue/evaluate.py --model training/dialogue/candidate.js \
  --out /tmp/dialogue-test.json
python training/dialogue/evaluate.py --model training/dialogue/candidate.js \
  --corpus training/dialogue/fresh-probe.json --out /tmp/dialogue-fresh.json
node --test tests/dialogue-transformer.test.mjs
```

元のコーパスと候補を再現するには保存済み `corpus.json` を使う。profile変更後にprepareするとデータが変わる。チェックポイントは500更新ごとにmodel・optimizer・乱数・履歴を保存し、同じ設定の `--resume` に対応する。2候補は同じseedでも補助headの初期化で乱数の消費が変わるので、補助headだけの厳密な因果比較ではない。

## 次の段階

ChatGPT級の能力は未達。現在の環境はCPU3コア・約9.7GiBメモリーで、訓練データは有限の手書き1,640例。次はライセンスと出典を確認した多様な日本語の会話・指示データ、正しい拒否や境界の例、独立した対話・事実・推論評価、人による自然さの確認を整える必要がある。より大きい自作モデルの言語事前学習と指示学習には、適切な学習インフラを用意する。今回の評価から、一般的な対話や推論が実現したとは主張しない。
