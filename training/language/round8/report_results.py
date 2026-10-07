"""Report real updates and strict development judgments without QA claims."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
 r=read(ROOT/'expanded-characters-10000/result.json');m=read(ROOT/'expanded-characters-10000/metrics.json');c=read(ROOT/'comparison.json');a=read(ROOT/'optimizer-audit.json');timing=read(ROOT/'performance.json')['runs']
 baseline=c['runs']['initial-0'];candidate=c['runs']['expanded-characters-10000'];initial=m['history'][0]['validation'];final=m['history'][-1]['validation'];selected=next(h['validation'] for h in m['history'] if h['step']==r['bestStep'])
 assert r['completedRun'] and r['completedSteps']==a['actualAdditionalOptimizerUpdates']==10000
 genre_rows='\n'.join(f"| {site} | {initial['sites'][site]['nllPerUtf8Byte']:.6f} | {selected['sites'][site]['nllPerUtf8Byte']:.6f} | {final['sites'][site]['nllPerUtf8Byte']:.6f} |" for site in initial['sites'])
 degradation=[site for site in initial['sites'] if selected['sites'][site]['nllPerUtf8Byte']>initial['sites'][site]['nllPerUtf8Byte']]
 warning='選択重みでも開始時より誤差が高い分野は '+', '.join(degradation)+'。全体平均だけで全分野の改善を主張しない。' if degradation else '選択重みの分野別誤差は開始時より低いが、文章の自然さを保証する結果ではない。'
 groups=[]
 for name,run in c['runs'].items():
  for scope,key in [('expanded13','groups'),('original9','coreGroups')]:
   for genre,v in run[key].items():groups.append(f"| {name} | {scope} | {genre} | {v['firstSentencePassed']}/{v['total']} | {v['fullOutputNonLoop']}/{v['total']} | {v['gatePassed']} |")
 speed='\n'.join(f"| {name} | {v['generatedTokenIds']:,} | {v['pythonGenerationSeconds']:.2f} | {v['javascriptGenerationMs']/1000:.2f} |" for name,v in timing.items())
 text=f'''# 原文追加・8層拡張モデルの追加学習

自作round6のVAL選択重みだけを基盤として、原文を追加し8層へ拡張したモデルの**追加10,000 optimizer更新**を完了した。実optimizerカウンターは10000。親の選択重みの系譜は18,000更新、今回の選択は{r['bestStep']:,}更新、選択された重みの系譜は{a['selectedWeightLineageUpdates']:,}更新。実行した回数と選択された重みの回数を区別する。round3以降の別初期化pilotを含む完了した実験の保存済み更新合計は44,000で、プロジェクトの全期間の合計や単一系譜の回数ではない。環境の再起動により、7,100更新までログが残った一方、復帰できたcheckpointは7,000更新だった。失われた100更新以上を別に記録し、同じoptimizer・RNG状態から再開した。物理的に実行した今回の更新は少なくとも10,100回で、そのほかの未記録の破棄更新数は不明。完了branchのカウンター10000へ破棄分を加算して選択重みの系譜とはしない。recovery.jsonと復帰checkpoint・停止前ログのSHAを保存した。初期0更新モデルの保存・再生成は追加学習に加算しない。

同じ拡張モデルで、開発13件の第一文合格は**初期{baseline['passed']}/13 → 選択後{candidate['passed']}/13**。従来9件だけでは**{baseline['corePassed']}/9 → {candidate['corePassed']}/9**。有効token出力は{baseline['validTokenOutputs']}/13 → {candidate['validTokenOutputs']}/13。全文非反復は初期1/13 → 選択後1/13、全文の意味の補助基準を満たす出力は初期0/13 → 選択後0/13で、今回の学習による安定した生成品質の改善は確認できない。凍結した開発言語基準の合格は**{c['languageGatePassed']}**。文章全体の意味の補助基準を含む目標達成判定は**{c['naturalLanguageEstablished']}**。生成を見る前にfull-meaning-policy.jsonを追加し、初期／選択重みの全文について、従来9件と拡張13件の物語／説明文の双方で80%以上の意味の一貫性を要求した。元の言語基準と重みの選択方法は変更していない。各行のfullOutputMeaningfulで点検し、詳細はcomparison.jsonに保存する。第一文の短い語尾が成立することや全文の非反復を、全文の意味・事実の正確性・会話能力の成立と同一視しない。全文の問題点は各validation-manual.jsonと編集していない生成文に残す。

## 原文と自作モデル

旧1,092文書の分割と原文単位を維持し、保存済みMDN日本語原文1,457文書を加えた。新規未露出グループだけを分割し、TRAIN1,967文書・8,721原文単位・4,861,881文字、VAL169文書、TEST209文書。TRAINで観測した4,315文字から独自に組み立て、既存IDと結合順位を保持して75規則を末尾へ追加した。語彙4,840、単語結合0、未知文字は元のbyte表現を使う。原文の利用条件・作者表示・HTML保存記録はround3／round7を参照する。

親は自作4層、今回8層dim192／4heads／context256／lookback32、4,537,728パラメータ。追加ブロックは初期状態で恒等変換、新規文字行は0、全パラメータを学習可能とした。親の既存logitと参照argmaxが保たれること、原文TRAINの勾配が新規層へ届くことを学習前に検証した。語彙増加により初期softmaxとNLLが親と同じとは限らない。主比較は同一の拡張モデルの初期0更新と学習後で、旧4層との比較では原文・語彙・層数も変わるため一因子の因果を主張しない。

CPU2threads、batch8、BF16 activation、FP32重み・optimizer・検証・推論。AdamWをリセット、seed1829、LR0.00015からcosine減衰。samplingは青空.35／MDN.25／気象庁.15／総務省.10／環境省.10／農水省.05。長さ64/128/256にまとめるが、全原文ラベルと境界を保持する。今回再抽出して学習に読ませた対象は{r['seenTargetTokens']:,}token／{r['seenTargetUtf8Bytes']:,}UTF-8bytes相当で、独立原文の新規量ではない。

## 誤差と生成の区別

canonical VAL NLL/UTF8 byteは開始{initial['nllPerUtf8Byte']:.6f}、選択{selected['nllPerUtf8Byte']:.6f}、終端{final['nllPerUtf8Byte']:.6f}。選択はこの誤差だけで固定し、その後に生成と採点を行った。終端optimizer重みとVAL選択重みは異なる場合がある。{warning}

| source | 初期0更新 | VAL選択 | 実10,000更新終端 |
| --- | ---: | ---: | ---: |
{genre_rows}

## 固定した言語基準

原文prefixから全語彙greedy、最大192新token、EOSまたはcontextで終了。文章補修・検索・固定回答・反復penalty・UTF-8文字フィルタなし。文法／意味／接続／反復／破綻を各0〜2点、一文9点以上・文法2・接続2・終止・有効tokenが必要。物語と現代説明文のそれぞれで第一文80%以上・全文非反復90%以上を、拡張13件と従来9件の双方で満たす必要がある。追加したMDNの成績で従来の失敗を隠さない。採点はアシスタントによる手動評価で、独立した人間の盲検評価ではない。

| run | scope | genre | 第一文合格 | 全文非反復 | 合格 |
| --- | --- | --- | ---: | ---: | --- |
{chr(10).join(groups)}

Pythonと独自JSの全文、全token、EOS、UTF-8有効性が一致し、参照logit誤差2e-4以下を確認した。途中の出力を補修せずに保存する。TEST30件は未生成、QA学習と公開モデル切替は未実施。外部重み・既成Tokenizer・生成API・Wikipedia・教師生成文を使用していない。以前の実験・共通実装・round7とround9-sourceの原文アーカイブもSHA一致を保持した。round9-sourceの統計・文化287ページは次回用の未分割・未学習データで、今回の重みに追加していない。

## 推論時間の記録

| run | 生成token合計 | Python秒 | 独自JS秒 |
| --- | ---: | ---: | ---: |
{speed}

モデル読み込みを除く13件の原文継続の記録。通信・UIを含むブラウザー速度の統制benchmarkではない。EOSと内容で仕事量が変わり、反復測定も行っていない。この表だけで応答速度の向上や実用的な会話能力を主張しない。
'''
 (ROOT/'RESULTS.md').write_text(text)
if __name__=='__main__':main()
