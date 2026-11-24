"""Aggregate audited completed sibling experiments; never substitute planned counts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent
def read(p):
    return json.loads(p.read_text())

rows = []
for n in (13, 14, 15):
    p = BASE / f'round{n}'
    a = read(p / 'execution/optimizer-audit.json')
    c = read(p / 'execution/comparison.json')
    r = read(p / 'continue-10000/result.json')
    assert a['actualCompletedUpdates'] == c['actualCompletedUpdates'] == r['completedSteps'] == 10000
    assert a['completedRun'] and r['completedRun']
    metric = next(h['validation'] for h in r['history'] if h['step'] == r['bestStep'])
    rows.append(dict(round=n, actualUpdates=a['actualCompletedUpdates'], selectedStep=r['bestStep'],
                     weightedDevelopmentNll=metric['nllPerUtf8Byte'],
                     aozoraSampling=read(p/'policy.json')['genreSampling']['aozora'],
                     targetTokens=a['seenTargetTokens'], targetBytes=a['seenTargetUtf8Bytes'],
                     elapsedSeconds=a['elapsedTrainingSeconds'], siteWeightedDevelopmentNll={site:sum(w*metric['views'][str(k)]['sites'][site]['nllPerUtf8Byte'] for k,w in [(0,.4),(1,.3),(2,.3)]) for site in metric['views']['0']['sites']}, **c['models']['new']))
total = sum(r['actualUpdates'] for r in rows)
assert total == 30000
out = dict(actualOptimizerUpdatesAcrossThreeSiblings=total, rounds=rows,
           sameParentRound=10, controlRound=11, singleModelAdditionalUpdates=10000,
           uncheckpointedDiscardedUpdatesBeforeRound14Stop="unknown",
           developmentOnly=True, newTestGenerated=False, publicModelReplaced=False)
(ROOT/'COHORT_COMPARISON.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
control = read(BASE/'round11/continue-10000/result.json')
cv = next(h['validation']['nllPerUtf8Byte'] for h in control['history'] if h['step']==control['bestStep'])
control_metric = next(h['validation'] for h in control['history'] if h['step']==control['bestStep'])
control_sites = {site:sum(w*control_metric['views'][str(k)]['sites'][site]['nllPerUtf8Byte'] for k,w in [(0,.4),(1,.3),(2,.3)]) for site in control_metric['views']['0']['sites']}
site_table = '| 開発site | Round11 | Round13 | Round14 | Round15 |\n|---|---:|---:|---:|---:|\n'
for site in sorted(control_sites):
    site_table += '| '+site+' | '+' | '.join(f'{v:.6f}' for v in [control_sites[site],*(r['siteWeightedDevelopmentNll'][site] for r in rows)])+' |\n'
table = '| モデル | Aozora行確率 | 実更新 | 採用step | 共通開発NLL/byte | 初文 | 非ループ | 全文意味 | Python/JS |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
table += f'| Round 11 対照 | 45% | 10,000 | 9500 | {cv:.9f} | 4/17 | 4/17 | 0/17 | 17/17 |\n'
for r in rows:
    table += f"| Round {r['round']} | {r['aozoraSampling']:.0%} | {r['actualUpdates']:,} | {r['selectedStep']} | {r['weightedDevelopmentNll']:.9f} | {r['firstSentencePasses']}/17 | {r['nonLoopOutputs']}/17 | {r['meaningfulFullOutputs']}/17 | {r['matchingSequences']}/17 |\n"
outcome = ('3本とも既存の厳格な開発言語ゲートは不合格。自然な日本語生成の改善を実証できなかった。' if not any(r['gatePassed'] for r in rows) else '開発ゲートの各合否は下表と個別結果を参照。新しいTESTでの一般化は未実証。')
text = f'''# Round 13–15: 三つの実学習の比較

**3本それぞれ実10,000更新、保持した学習系譜で合計{total:,} optimizer更新を完了。** 同じRound 10採用重みから始めた兄弟実験であり、一つのモデルへ30,000更新を継続した結果ではない。{outcome} 公開モデルとWebサイトは変更していない。各モデルの合否は次表および個別RESULTS.mdに保存した。

{table}
通常/Glyph/ランダム文字境界BPE40/30/30、モデル8層dim192、独自語彙、元文章とfold、seed、fresh optimizer、LR、context256、更新予算、共通開発選択を固定した。変更した一因子は既存TRAIN原文のジャンル行サンプル確率。Aozoraの減少分をMDN以外の既存現代説明6siteへ比例配分し、MDN15%を固定した。THREE_ROUND_POLICY.jsonは最初の更新前に固定している。新規原文や独立した3因子を追加した実験ではない。

Round 14は実行プロセス終了後にstep6400のatomic checkpointから同じoptimizer・RNG・学習率scheduleで再開した。原因は未確認。停止直前のcheckpoint未保存・喪失更新の有無と回数も不明であり、0と推定していない。合計は保存済みの保持系譜の更新数で、未保存の計算量を含めた物理的な総更新数ではない。更新前後のログとresume-record.jsonを保存し、サンプラー再生で最終RNG・target数を確認した。実際の更新数を予定数から推定していない。

## ジャンル別の同条件loss診断

{site_table}
各siteで通常/Glyph/文字境界40/30/30を適用したNLL/byte。モデルの採用やmanual判定には使わない事後診断。全体のlossと特定ジャンルのlossの変化を分けるために併記する。MAFFには開発データがなく、この表や17件生成での一般化を認定できない。

## 評価の範囲

同じ既存開発17書き出し、greedy全語彙、max192、真EOS停止による自己回帰生成を無修正で全文保存した。各ラウンドexecution/FULL_GENERATIONS.mdおよびJSONには全文とtokenがある。全文意味・初文・長い反復を別々に判定し、既存のexpanded17/parent13/original9と各ジャンル群の厳格なゲートを変更していない。全件の個別理由は各RESULTS.md/new-manual.jsonにある。

これらは既に露出した開発診断で、新しいTEST結果ではない。未見一般化を実証していない。旧policyに保存された過去のTEST参照文が閲覧可能であったことも、新しい未露出評価と区別する。判定はassistantによる非blindの手動評価で、未知の固有名詞や主語省略について不確実性がある。MAFFは開発生成と固定gap標本の対象にない。閾値の緩和や生成後の修正で改善を作っていない。

## 原因の切り分けと次の実験

1. **容量**: 約466万パラメータのまま、ジャンル構成だけを比較した。容量の因果効果は測っていないため、大規模化を必然とはしない。
2. **データ量・偏り**: 約504万TRAIN文字の同じ原文を再配分した。定型句・法令番号・API説明や節の反復が残る。新しい文体や文章関係の多様性を増やした対照ではないため、再配分と新規高品質原文の効果を混同しない。
3. **分割と文字境界**: 今回は全3ビューを固定した。Round 12で文字境界ビューを除いても全文意味0/17だったため、文字境界だけを唯一の原因とはできない。粒度の診断は各generation-granularity.jsonに保存した。
4. **LR・optimizer**: 同じschedule、有限勾配・moment、実step一致と正確な再開を確認した。数値的健全性は最適なLRの証明ではない。今回LRを同時変更していない。
5. **context**: 256tokenは長い説明の制約となり得る。短い初文内でも助詞・活用・修飾が壊れるため、長いcontextだけで全問題を解決できる証拠はない。
6. **学習不足・過学習**: 各loss-history.csvと同一固定TRAIN/dev標本のtrain-development-gap.jsonを参照する。loss低下は全文の意味成立を保証しない。標本は全TRAINではなく、長さやprefix条件も異なるのでgapから単独で過学習や容量不足を断定しない。単純な更新数追加を次の既定策にしない。
7. **推論誤差**: 各export-rounding.jsonとnumerical-divergence.jsonにFP32/7桁export/Python/JSの全文一致とlogit誤差を保存した。Round 10の既知の気象書き出しのnear-tie分岐は旧記録に残り、今回の一致で過去の分岐を消していない。現在の言語失敗と数値分岐を分ける。
8. **評価**: 単一seed、開発17件、非blind判定、既存短い重複、genre coverageの限界がある。独立した人間評価と新たに固定した未露出holdoutが必要。未知名詞・省略主語だけを不合格の自動条件にしない一方、旧閾値は維持する。

次は、同じモデル・語彙・BPE比率・LR・初期重み・更新予算を保ち、利用条件を確認した人間の現代日本語段落の質と原文の多様性を一因子として比較することを推奨する。まず定型節の重複と文間接続のある原文の割合を監査し、TRAINだけを調整する。今回の結果を根拠なく成功と呼んだり、追加更新・大規模化を自動実行したりしない。この推薦実験は未実行。

## 再現と保存

各roundのpolicy.json/source-manifest.jsonに固定設定と入力SHA、continue-10000/checkpoint.ptに最新重み・optimizer・Python/Torch RNG・実更新数、selected-weights.ptとmodel.jsに採用重みを保存した。execution/optimizer-audit.json、sampler-replay.json、全loss履歴、初期状態一致、全文評価とartifact-manifest.jsonを併せて参照する。

新規実行は各execution/run.sh、既存checkpointからは同じcommandに--resumeを付ける。完了済み実験を新規実行で上書きしない。3本合計と各モデルの系譜をCOHORT_COMPARISON.jsonで区別した。外部学習済み重み・Tokenizer・生成AI API・別モデルの生成教師文・検索回答は使用していない。
'''
(ROOT/'THREE_ROUND_RESULTS.md').write_text(text)
print(json.dumps(out, ensure_ascii=False))
