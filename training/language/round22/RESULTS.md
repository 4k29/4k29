# Round22 結果 — 人間原文のカバレッジ追加

実際のoptimizer更新 **10,000/10,000**。optimizer counter [20000]、最新重みの系譜 59,000 更新。DEV NLLで選択した重みは追加9,500更新時。経過8323.6秒。

最良weighted DEV NLL/UTF-8 byte **0.971461170063259**。事前閾値Round19 **0.972624845997683**、NLL成功条件=True。初期値0.978919000749818。NLLは分割法を混ぜた診断であり、独立した文章の確率でも自然な日本語の証明でもない。

| 同条件の露出済みDEV17件 | Round19対照 | Round22 |
|---|---:|---:|
| 初文合格 | 7/17 | 6/17 |
| 長いループなし | 4/17 | 4/17 |
| 全文意味成立 | 0/17 | 0/17 |
| 全scope/group言語ゲート | False | False |

## 対照とデータ

PRの基底はRound21だが科学的対照は通常CEのRound19。UL係数を強めたRound21からの延長ではない。同じRound11最新model/AdamW/Torch/private Python RNGを復元し、8層192次元・context256・独自5455語彙・40/30/30・ジャンルmass・LR・更新数・生成条件を維持。変更は新しい人間原文TRAINの追加だけ。

45単位23,961文字（JMA38単位20,908文字、MAFF7単位3,053文字）を追加。新しい予約文書7件はencode・loss・生成に使用しない。本文の見出し・段落を保ち参考資料より前で閉じ、従来のRound3 chainsで単位化した。旧TRAIN prefix/行/文書とvalidation・tokenizerの同一性、全135追加viewのmask-once、非ゼロ有限勾配、親checkpoint/model/optimizer/RNG一致を実更新前に検証した。

収集・準備の不成立/品質修正4attemptも保存。既知URLの除外、JMA knowledgeリンクとMAFF kids探索を調整し、最終前attemptの段落だけの抽出が見出しを落とす問題を修正した。いずれもモデル更新・生成・lossを見る前。30単位15,000文字2sites等の採用下限は緩和していない。原HTML、現行公共データ利用規約snapshot、出典・著者・加工内容とSHAを保持し、画像や第三者リンク資料を採用しない。

旧非TRAIN627文書・既存予約原文・新予約原文への64文字重複、旧TRAINとの重複、新TRAIN内部重複を監査・除外。TEST本文を重複監査のみに使用し、TESTをencode・評価・生成・重み選択には使用していない。近似・言い換え重複不存在は保証しない。追加量は既存約500万文字の約0.5%、政府2ドメインに限る。追加で長さ・sampler経路・実exposureも変わるため、純粋な意味カバレッジの因果効果や統計的有意差とは主張しない。

実target exposureは15,543,567 token / 54,500,806 UTF-8 bytes。500更新ごとの対照比較では19/20回でRound19を下回った。paired-loss-comparison.jsonとloss-history.csvに全点を保存。

## 生成評価と数値一致

FULL_GENERATIONS.mdとold/new-validation.jsonに同じ17入力への全文・全tokenを無加工で保存。greedy full vocabulary、最大192新token、真EOS、Python1thread。文法・主述・修飾・文中意味・文間接続・反復・途中崩壊を全文読解し、理由をSHA結合したmanualに残した。未知固有名や未確認の事実だけでは失格にせず、APIの正確性も認定しない。独立/盲検の人間評価ではない。

従来の初文80%・非ループ90%・全文意味80%をexpanded17/parent13/original9と各groupで同時に求めるゲートを変更しない。17件は既存の露出済みDEVで、新TEST結果ではない。evaluation-sensitivity.jsonに曖昧な局所反復の扱いも記録。

Python/JavaScriptの全文列一致は旧17/17、新17/17。reference最大絶対誤差は旧1.04904174805e-05、新9.53674316406e-06。許容差0.0002を変更しない。FP32/7桁exportの比較はexport-rounding診断、全分岐はnumerical-divergence.jsonに保存。既知Round10のJMA08 near-tieによる16/17一致も残す。許容差内でも自己回帰列が常に一致する保証にはならない。

生成4-gram反復率は旧55.594528%→新64.074074%、EOS終了は4→4。これは補助的な事後診断で言語ゲートの代用ではない。

## 原因の切り分け

- データ不足・偏り：追加TRAINのteacher-forced NLLは旧1.006158203→新0.809066657。局所的な適合と全文意味・未見一般化は別。今回の小規模な政府原文追加だけで一般的な会話データ不足は解決していない。
- 容量不足：465万parameterの小モデルは候補だが、容量を変えた対照がないため主因とは断定しない。今回は容量を固定しデータの効果を先に測った。
- トークン・文字境界：独自BPE/語彙と40/30/30は固定。generation-granularity.jsonに語token比・同一token連続・全角空白を保存。境界方式別DEVは測るが、境界の因果効果を今回単独では測っていない。
- 学習率・optimizer：親latestの整合したmoment/RNGとFP32有限勾配、全parameterの実counterを監査。最適LRの比較ではない。Round20/21のUL強化はNLLと全文意味を改善しなかったので採用しない。
- 学習不足・過学習：固定された旧TRAIN canonical診断のNLL 0.754720803、DEV 1.009668492、差0.254947689。追加原文や全TRAINを代表する指標ではない。teacher forcingと自由生成の乖離を単純な更新不足と同一視しない。
- context長：256token固定。長い続きで崩れることは候補だが、contextを変えた対照や切り詰め別測定がないため原因確定ではない。
- 推論数値：Python/JSおよび丸め前後の全文一致と分岐診断を保存。同じ不自然さが一致した列でも起きれば数値誤差だけでは説明できない。既知near-tie分岐は隠さない。
- 評価方法：DEVへの繰り返し露出、1seed、assistant読解、短文/EOSと意味成立の取り違えに注意。全出力と個別理由を保存し、ゲートを緩めず不確実性を明記した。

## 次の実験への推奨

NLL条件は達成したが全文意味0/17、初文7→6、生成4-gram反復55.6%→64.1%のため、自然な日本語生成の改善・公開採用は見送る。追加TRAINではNLL1.006158203→0.809066657となった一方、生成の意味・反復は改善せず、局所的なteacher forcing適合だけでは課題を解消できなかった。

直ちに大規模化や更新数追加、UL再強化を選ぶ根拠は不足している。次は同じRound19対照とRound22追加コーパスのペアを、事前固定した別の学習乱数系列で再現し、NLL差の再現性と全文意味・反復への悪影響を確認することを優先する。変更するのは初期model/moment復元後の学習乱数系列だけとし、準備済みデータ・分割seedと、容量・context・分割・LR・採用閾値は変えない。今回のNLL勝利だけでさらに同種政府原文を大量追加する判断は保留する。新しい広い一般化の主張には、露出済みDEVとは独立した事前登録評価と、利用条件の明確な多様な人間原文が必要だが、今回のロックされたTESTを開けていない。

## 再現と保存

設定policy.json、collection-policy.json、source-manifest.jsonと生source snapshot、準備済みtrain/validation、全学習ログ/CSV、checkpoint-0.pt、checkpoint.pt、selected-weights.pt、model.jsを保存。checkpointは最新model/AdamW/Torch/private Python RNGと実counterを含み、選択best重みと最新momentを混ぜない。sampler-replay.jsonは実exposureと最終RNGを追跡する。launch.jsonに起動時commitを保存しartifact-manifest.jsonにコード・データ・評価・重みのSHA/sizeを記録。

完了済みのcontinue-10000を再更新しない。未完了checkpointだけ `bash training/language/round22/execution/run.sh --resume` で同一設定に復元する。今回の実完了数は10,000で、予定数の転記ではなくcheckpointと全parameter optimizer counterで検証した。persistent controllerはチャットと独立に実行し、機械成果を先に保存した。MECHANICAL_STATUS.mdとautomatic-publish-complete.jsonの意味評価pendingは自動保存時点の履歴であり、本報告・SHA結合manualが最終評価である。

外部学習済み重み/tokenizer、生成API、別モデル教師文章、固定回答、生成後修正は使用しない。公開モデル・Webサイトの挙動を変更せず、新TESTも生成しない。

機械評価と報告の再生成は学習を再実行せず、保存済み重み・生成を入力に行う:

```sh
python training/language/round22/execution/score_outputs.py
python training/language/round10/review.py --generation training/language/round22/execution/old-validation.json --manual training/language/round22/execution/old-manual.json --out training/language/round22/execution/old-review.json
python training/language/round10/review.py --generation training/language/round22/execution/new-validation.json --manual training/language/round22/execution/new-manual.json --out training/language/round22/execution/new-review.json
python training/language/round22/execution/summarize.py
python training/language/round22/execution/compare_loss.py
python training/language/round22/execution/measure_repetition.py
python training/language/round22/execution/measure_added_train.py
python training/language/round22/execution/verify_manifest.py
```

build_report.pyは数値の基本報告を生成する。次の実験の判断、検証結果、再現コマンドの本報告追記は実測後の記述であり、基本報告の再生成で上書きされる。

検証: Node既存テスト962/962、公開側評価2580/2580、docs/app.js構文検査成功。いずれも実験モデルの言語合格を意味しない。git差分はRound22配下のみ。SHA/size監査はartifact-manifest.jsonとverify_manifest.pyで再現可能。
