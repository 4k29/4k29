"""Report verified own additional updates, strict language results and limits."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
    c=read(ROOT/'comparison.json');r=read(ROOT/'character-continue-10000/result.json');m=read(ROOT/'character-continue-10000/metrics.json')
    a=read(ROOT/'optimizer-audit.json');b=c['runs']['parent-10000'];f=c['runs']['character-continue-10000'];timing=read(ROOT/'performance.json')['runs']
    speed='\n'.join(f"| {name} | {t['generatedTokenIds']:,} | {t['pythonGenerationSeconds']:.2f} | {t['javascriptGenerationMs']/1000:.2f} |" for name,t in timing.items())
    text=f'''# 同じ自作文字モデルの原文追加学習

保存した自作round5のcanonical VAL最良重みだけから **追加10,000 optimizer更新**を完了した。実物のoptimizerカウンターは10000。親の選択は10,000更新、子の選択は{r['bestStep']:,}更新、選択重みの系譜は{a['selectedWeightLineageUpdates']:,}更新。子0を選んだ場合は親のままであり、実行した10,000回を改善した系譜に自動加算しない。別初期化のpilotを含むround3/4/5合計24,000実更新と今回を合わせて34,000であり、単一の重みの更新数とは区別する。親の再生成は追加学習として数えない。

同じ固定開発9件の一文合格は **親{b['passed']}/9 → 子{f['passed']}/9**、有効token出力は{b['validTokenOutputs']}/9 → {f['validTokenOutputs']}/9。言語ゲート合格は **{c['languageGatePassed']}**。全文の反復・意味の破綻・数値の根拠は各validation-manual.jsonの理由に残す。一文の語尾だけが成立することや非ループを、全文の意味や会話能力の成立と同一視しない。

## 学習と選択

原文TRAIN748文書・4,498連続単位・2,702,074文字、独自文字語彙4,765、単語結合0、4層dim192／4heads／context256／lookback32、2,743,872パラメーターを維持。原文・Tokenizer・splitを再適合せず、新規文書0件。原文byteと全対象・真のBOS/EOSは親と同じ。出典・利用条件はround3/2/root、文字組み立てと被覆の検証はround5に保存している。

CPU2threads、batch8、BF16 activation、FP32重み・optimizer・検証・推論。optimizerとseedをリセットしseed1729、LR0.00015からcosine減衰を使う。追加露出に加えoptimizer・seed・LRが変わるため、一変数の因果比較ではない。今回実際に再抽出した対象は{r['seenTargetTokens']:,} token、{r['seenTargetUtf8Bytes']:,} UTF-8 bytes相当で、新しい独立原文の量ではない。

開始canonical VAL NLL/byte {m['history'][0]['validation']['nllPerUtf8Byte']:.6f}、最良 {m['bestValidationNllPerByte']:.6f}。親の重み・TRAIN／held／Tokenizer・source SHA・構造・実optimizer更新数を開始前に確認。選択はcanonical VAL byte NLLのみで、生成・採点を見る前に重みを固定する。選択モデルとoptimizer終端モデルは選択stepによって異なり得る。

全体の誤差は下がったが、一文合格は3/9のまま、全文非ループも1/9のままで、生成品質の改善は確認できない。JMAのcanonical VAL NLL/byteは開始{m['history'][0]['validation']['sites']['jma']['nllPerUtf8Byte']:.6f}から終端{m['history'][-1]['validation']['sites']['jma']['nllPerUtf8Byte']:.6f}へ悪化した。全体平均だけで各分野の改善や自然な会話の成立を主張しない。選択8,000更新以降の全体誤差も僅かに上がったため、終端10,000更新の重みを採用していない。

## 評価と監査

原文prefixから語彙全体greedy最大192新token、EOSまたはcontextで終了。文法補修・固定回答・検索・反復penalty・UTF-8 tokenフィルターは使わない。文法／意味／接続／反復／破綻を各0〜2点、一文9点以上・文法2・接続2・終止・有効token、文学／現代説明文それぞれ一文80%以上と全文非ループ90%以上が基準。アシスタントの手動採点で独立blind人間評価ではなく、事実の正確性を保証しない。Pythonと独自JSの全文・全token・EOS・UTF-8有効性が一致し、参照logit誤差2e-4以下を検証する。

新規TEST24件は未生成。QA学習と公開モデルへの切替は実施していない。外部重み・既成Tokenizer・生成API・Wikipedia・teacher文章・QAを使わない。以前のround3 88ファイル、round4 55ファイル、round5 61ファイルをSHA一致で保持し、今回の学習code・policy・重み・採点・照合・監査をmanifestに固定する。

親／子それぞれの実更新10000・同じ規模からversion文字列が重複し得るため、成果物の識別にはモデル全文のSHA256とtrainer／policy SHAを使う。学習中のexporterは変更していない。

## 記録した推論時間

| run | 生成token IDs合計 | Python生成秒 | 独自JS生成秒 |
| --- | ---: | ---: | ---: |
{speed}

モデル読み込みを除く9件の原文続き生成の記録で、ブラウザー応答速度の統制benchmarkではない。EOS／出力内容により仕事量が変わり、反復時間測定もしていない。速度の向上や実用的な回答品質は、この表だけで主張しない。
'''
    (ROOT/'RESULTS.md').write_text(text)
if __name__=='__main__':main()
