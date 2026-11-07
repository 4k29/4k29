"""Combine completed controls and continuation without conflating model lineages."""
import pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent
read=lambda p:json.loads(p.read_text())
rows=[]
for n in (13,14,15,16):
 p=BASE/f'round{n}';a=read(p/'execution/optimizer-audit.json');c=read(p/'execution/comparison.json')
 assert a['actualCompletedUpdates']==10000 and a['completedRun']
 m=c['models']['new'];rows.append(dict(round=n,retainedAdditionalUpdates=10000,selectedStep=a['selectedStep'],latestWeightLineageUpdates=a['latestWeightLineageUpdates'],selectedWeightLineageUpdates=a['selectedWeightLineageUpdates'],optimizerCounters=a['optimizerCounters'],bestCommonDevelopmentNll=a['bestWeightedDevelopmentNllPerByte'],firstSentence=m['firstSentencePasses'],nonLoop=m['nonLoopOutputs'],fullMeaning=m['meaningfulFullOutputs'],strictGate=m['gatePassed'],pythonJavascriptMatchingSequences=m['matchingSequences'],parentRound=11 if n==16 else 10))
goal=read(ROOT/'execution/progress-goal.json');total=sum(r['retainedAdditionalUpdates'] for r in rows);assert total==40000
out=dict(retainedNewOptimizerUpdatesAcrossFourExperiments=total,rounds=rows,progressCriterionMet=goal['progressCriterionMet'],controlBestCommonDevelopmentNll=goal['controlBestCommonDevelopmentNll'],newTestGenerated=False,publicModelReplaced=False,uncheckpointedDiscardedUpdatesBeforeRound14Termination='unknown',note='Three siblings from Round10 plus one optimizer-aligned continuation of Round11. Summed experiment updates are not a single-model lineage.')
(ROOT/'FOUR_ROUND_COMPARISON.json').write_text(json.dumps(out,indent=2)+'\n')
table='| 実験 | 親 | 実保持更新 | 採用追加step | 共通開発NLL/byte | 初文 | 非ループ | 全文意味 | Python/JS |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
for r in rows:table+=f"| Round{r['round']} | {r['parentRound']} | {r['retainedAdditionalUpdates']:,} | {r['selectedStep']} | {r['bestCommonDevelopmentNll']:.9f} | {r['firstSentence']}/17 | {r['nonLoop']}/17 | {r['fullMeaning']}/17 | {r['pythonJavascriptMatchingSequences']}/17 |\n"
text=f'''# Round 13–16 実学習の全体結果

**4実験をそれぞれ実10,000更新、保持した系譜で計{total:,}更新を完了。** NLLまたは既存言語ゲートという反復進捗基準={goal['progressCriterionMet']}。自然な日本語生成の合否は個別ゲートと全文意味を参照し、NLL改善だけで合格にはしない。公開モデル・Webサイトは変更していない。

{table}
共通対照Round 11は採用9500のNLL **{goal['controlBestCommonDevelopmentNll']:.9f}**、初文4/17・非ループ4/17・全文意味0/17。各モデルの無修正全文、token、手動理由、全scope/groupの厳格なゲートを各executionに保存した。新しいTESTや独立人間評価、未見一般化の実証ではない。

Round13–15は同じRound10採用重みからの兄弟対照。既存TRAINのAozora行確率のみ45%→35/25/15%へ変更し、MDN15%を保持した。原文は増やしていない。Round16は別系統で、Round11最新重み・optimizer・両RNGを整合した状態のまま継続し、既存終端LRを保持する追加区間の規則を事前固定した。追加学習を選んだ根拠はRound11の7000→9500の共通NLL改善と3本の再配分対照の失敗。単一モデルへ40,000更新を追加したと記録しない。各モデルの最新/採用系譜とoptimizer counterをJSONと個別RESULTSに保存した。

Round14は保存step6400から同一条件で再開した。終了原因と停止直前の未保存・喪失更新の回数は不明。合計40,000は最終checkpointで確認できる保持系譜の数で、未保存計算を含む物理的総更新数を推定していない。

## 保存と再現

各roundのpolicy/source-manifestは最初の更新前に固定。checkpointには最新model・optimizer・Torch/Python RNG・実step・target数を保持し、採用FP32/model.jsを別保存した。全loss・全文・旧比較・SHA/サイズ・初期一致・sampler replay・丸め/JS診断を保存した。未完了のcheckpointからだけ同じrun.shに--resumeを付ける。完了済みを再開して成果物を上書きしない。

- 3ジャンル対照・8原因仮説: `../round13/THREE_ROUND_RESULTS.md`
- 追加学習・NLL/言語分離・全失敗理由: `RESULTS.md`
- 4実験の実更新数と比較: `FOUR_ROUND_COMPARISON.json`
- 各runの全生成: `execution/FULL_GENERATIONS.md`とJSON
- 各SHA検証: `execution/verify_manifest.py`

Python/JSの既知のRound10 near-tie分岐も旧記録に残し、今回の一致で隠していない。許容誤差と厳格なsequence比較を変えていない。外部学習済み重み/Tokenizer、生成API、生成教師文、検索・固定回答、生成後の修正は使っていない。

## 次に切り分けること

容量、データ量/偏り、境界分割、LR/optimizer、context、学習不足/過学習、推論誤差、評価の欠陥という8仮説の証拠と限界は上記2報告に分けて記録した。今回NLL基準だけを満たした場合、語彙確率の改善に留める。次の言語対照には、人間の現代日本語段落の質・文間接続・多様性を一因子として追加し、モデル/語彙/ビュー/LR/初期状態/更新予算を固定することを推薦する。まずTRAINの定型節重複を監査し、利用条件とfold分離を保ち、独立評価と未露出holdoutを事前固定する。この原文追加実験は未実行。
'''
(ROOT/'ROUND13_16_RESULTS.md').write_text(text)
print(json.dumps(out))
