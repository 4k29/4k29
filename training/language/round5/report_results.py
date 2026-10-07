"""Report strict character-run development results without fluency claims."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text())
def main():
    c=read(ROOT/'comparison.json'); r=read(ROOT/'characters-10000/result.json'); m=read(ROOT/'characters-10000/metrics.json')
    b=c['runs']['baseline-1000']; f=c['runs']['characters-10000']
    text=f'''# 自作・文字単位Transformerの実更新と評価

外部の重み・既成Tokenizer・生成API・Wikipedia・QA・teacher文章を使わず、ランダム初期化から **10,000 optimizer更新**を完了した。実物のoptimizerカウンターを確認し、1,000更新の保存スナップショットは追加更新として数えない。以前のround3/4の重みを引き継がず、今回の選択重みの系譜は{r['bestStep']:,}更新。今回までのround3 pilot2,000 + main10,000 + round4追加2,000 + 今回10,000の実更新は24,000で、別初期化の合計と重みの系譜を区別する。

同じ文字モデル・同じ固定開発VAL9件・同じ生成条件で、一文合格は **1,000更新 {b['passed']}/9 → VAL選択 {f['passed']}/9**、有効token出力は{b['validTokenOutputs']}/9 → {f['validTokenOutputs']}/9。言語ゲート合格は **{c['languageGatePassed']}**。グループ別の結果と全文の反復はcomparison.json、各validation-review.jsonに残した。最初の一文だけの成功、短い語尾の補完、NLLの低下を会話全体の性能向上と取り違えない。

## 原文と符号化

round3で固定したTRAIN748文書・4,498原文連続単位・2,702,074文字をそのまま使う。新規文書は0件。TRAINに現れる4,259種のUnicode文字だけからUTF-8組み立て規則4,503個を作り、語彙4,765、単語結合0。TRAINの各文字は必ず1 tokenで、途中の単語結合がprefixを跨がない。VAL/TESTだけに現れる文字はbyte fallbackのまま。原文を正規化せず、実際のBOS/EOS・全対象ラベルを保つ。以前の原文出典・利用条件・分割の記録はround3/2/rootを参照する。

学習は4層・dim192・4heads・{r['parameters']:,}パラメーター、context256、lookback32、seed1629、CPU2threads／8GiB。activationはBF16、重み・optimizer・検証・推論はFP32。実際に再抽出して学んだ対象は{r['seenTargetTokens']:,} token、{r['seenTargetUtf8Bytes']:,} UTF-8 bytes相当で、独立原文の量ではない。

## 選択と評価の限界

canonical VAL NLL/byteは初期{m['history'][0]['validation']['nllPerUtf8Byte']:.6f}、最良{m['bestValidationNllPerByte']:.6f}。生成を見ずにこの基準だけで{r['bestStep']:,}更新の重みを選んだ。語彙全体でgreedy生成し、特殊tokenや不完全UTF-8片も出力から除かない。文法修復・検索・固定回答・反復penaltyは使わない。

文字tokenでは1 tokenが短いため、学習開始前に最大192新tokenと固定した。以前の単語tokenモデルの128新tokenとは、モデルの深さや実効文脈長も異なるため単一要因の因果比較はしない。主比較は同じ今回のモデルの保存1,000更新対VAL選択重み。

文法・意味・接続・反復・破綻を各0〜2点、一文9点以上・文法2・接続2・終止・有効tokenが条件。文学／現代説明文の各グループで一文成功80%以上、全文非ループ90%以上を必要とする。採点はアシスタントによる手動で独立したblind人間評価ではない。事実・数値の正確性や汎用会話能力を保証しない。Pythonと独自JSで全文・全token・EOS・UTF-8有効性の一致、全logit参照誤差2e-4以下を照合した。

新規TEST24件は未生成。QA学習や公開回答モデルの切替は実施していない。以前のround3の88ファイルとround4の55ファイルのSHAを維持し、今回のsource・data・checkpoint・採点・JS比較はreproducibility-manifest.jsonに固定する。
'''
    (ROOT/'RESULTS.md').write_text(text)
if __name__=='__main__': main()
