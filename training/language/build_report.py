"""Build a factual Japanese result report from finalized, explicitly reviewed runs."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads((ROOT/p).read_text())
def main():
    source=read('sources.json');policy=read('generation-policy.json');choice=read('vocabulary-choice.json');paragraph=read('paragraph-bpe-4096/data.json')
    results={n:read(n+'/result.json') for n in ['raw-million','paragraph-million']}
    for r in results.values():assert r['completedRun'] and r['completedSteps']==10000
    reviews={n:read(n+'/test-review.json') for n in results};tests={n:read(n+'/test.json') for n in results};exposure=read('baseline-exposure.json')
    benchmark=read('tokenizer-benchmark.json')
    text=['# 独自Transformerの原文日本語学習：実測結果','']
    passed=reviews['paragraph-million']['gatePassed']
    text+=['**言語段階の合格基準は'+('成立した。' if passed else '未達。')+'** 原文のみの2つの実験で、実際に10,000更新ずつ、計20,000 optimizer更新を完了した。損失低下と更新数を、自然な日本語生成の実現とは扱わない。公開済みの本人回答モデルは比較用に維持し、この原文モデルへ置き換えていない。','']
    text+=['## 原文と独自語彙','',f"出典・利用条件付き原文は{source['documents']:,}文書、{source['characters']:,}文字、{source['utf8Bytes']:,} UTF-8 bytes。青空文庫の著作権が消滅した日本語原著、MDN、気象庁、農林水産省を使う。Wikipedia・外部の生成AI・既存学習済み重み・既成トークナイザーは使っていない。PyTorch2.6.0は計算ライブラリとして利用する。",'', '文書・作品・強い長段落重複を先にグループ化してTRAIN354／VAL45／TEST44へ固定。独自byte-BPEの語彙学習はTRAINの原文だけ。出典・利用条件は [DATA-LICENSE.md](DATA-LICENSE.md)、全件の表示は `source-credits.json`。短い共通段落の残存は `data-audit.json`、欄外・公式連絡先の残存は `residual-layout-audit.json` に開示している。','', '| BPE語彙数 | パラメーター | 実際の更新 | VAL NLL／UTF-8 byte |','| --- | ---: | ---: | ---: |']
    for r in choice['rows']:text.append(f"| {r['vocabulary']:,} | {r['parameters']:,} | {r['completedUpdates']:,} | {r['validation']['nllPerUtf8Byte']:.6f} |")
    text+=['', 'VALのbyte正規化損失で語彙4,358を選択。語彙間でtoken PPLを直接比較しない。語彙以外に埋め込みパラメーター数、文字で見たcontext幅、バイト曝露も異なり、語彙サイズ単独の因果効果とはしない。','', '## 実際の原文学習','', '自作decoderはdim192・4層・4heads・MLP768・context256、2,665,728パラメーター。乱数から原文のcausal next-token predictionのみで開始した。追加実験は自分で学習した最良の原文重みから始め、AdamWを新しく初期化した。QA、instruction、teacher文は両方に含めていない。','', '| 実験 | 完了更新 | 選択更新 | 初期VAL byte NLL | 最良VAL byte NLL | TEST byte NLL | TEST token PPL |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name,r in results.items():
        h=r['history'];best=min(h,key=lambda x:x['validation']['nllPerUtf8Byte']);t=tests[name]['likelihood']
        text.append(f"| {name} | {r['completedSteps']:,} | {r['bestStep']:,} | {h[0]['validation']['nllPerUtf8Byte']:.6f} | {best['validation']['nllPerUtf8Byte']:.6f} | {t['nllPerUtf8Byte']:.6f} | {t['tokenPerplexity']:.3f} |")
    parent=results['paragraph-million']['ownInitialModel'];p=paragraph['stats']['train']
    text+=['',f"追加実験の親は最初の実験の{parent['selectedParentStep']:,}更新時点。TRAINの{p['uniqueParagraphs']:,}原文段落、{p['uniqueSourceCharacters']:,}文字を使う。canonicalと独自BPE merge省略15%／30%の3表現は同じバイトへ復元でき、新しい原文文字数へ足さない。VAL／TESTはcanonicalのみ。長さ64／96／128／192／256のbucketを使い、余分なPADの計算を減らす。",'', '**全文書EOSと完結段落EOSでは評価単位が違う。** 上の両行のtoken PPLを同じ条件の性能比較として扱わない。各実験の初期と最良のVAL損失、同じ22の書き出しからの実際の生成を確認する。各データのtoken/byte分母は `test.json` にある。','',f"最良の追加モデルへつながる選択重みの更新数は{parent['selectedParentStep']+results['paragraph-million']['bestStep']:,}であり、完了した20,000更新とは区別する。語彙pilot2,000更新、放棄した抽出実験1,238更新、破棄した速度測定用の更新も別に記録する。本人QA追加実験は7,500更新で中断し、今回再開していない。",'', '実測曲線： [全文書](raw-million/learning-curves.svg)／[完結段落](paragraph-million/learning-curves.svg)。損失を自然さの点数へ読み替えず、曲線を平滑化していない。','', '## 未見の自己回帰生成','', '選択完了後に、学習前に固定したTEST22件（物語8、説明文14）を初めて生成した。入力はBOS＋書き出し、全語彙greedy、最大128 new tokens。検索、固定回答、テンプレート、外部API、語尾修正、反復penalty、生成後の修正は使わない。元の続きを全文一致で再現する要求も置いていない。','', '文法・意味・接続・反復・破綻を各0〜2で全件点検。最初の生成文が閉じ、文法2・接続2・合計9以上で一文合格。物語／説明文の各群で一文80%以上、全文の非ループ90%以上を要求する。点検は実装者アシスタントによる明示的な採点であり、独立した人による盲検評価ではない。','', '| モデル | 群 | 第一文合格 | 全文非ループ | 群の合格 |','| --- | --- | ---: | ---: | --- |']
    for name,r in reviews.items():
        for group,g in r['groups'].items():text.append(f"| {name} | {group} | {g['firstSentencePassed']}/{g['total']} | {g['fullOutputNonLoop']}/{g['total']} | {'合格' if g['gatePassed'] else '未達'} |")
    text+=['', '失敗例（書き出し＋出力を変えずに表示）：','']
    for name,r in reviews.items():
        failed=[x for x in r['rows'] if not x['firstSentencePass']]
        if failed:
            row=failed[0];text += [f"- `{name}`／`{row['id']}`：{row['manual']['reason']}",'', '> '+row['joined'].replace('\n','\n> '),'']
    text+=['失敗だけを省いた成功率にはしていない。生成全文・token列・EOS・不正UTF-8／制御token・手動点検・集計は各モデルの `test.json`、`test-manual-review.json`、`test-review.json` に保存。途中のVAL9件の診断と重みも保存しており、最終TESTと混同しない。','', f"従来の自作ownerモデルも同じ書き出しでraw生成を比較用に保存した。ただし以前の分割では{exposure['oldTrainSourceMatches']}ページ／{exposure['oldTrainOpeningMatches']}書き出しがTRAINにあるので、22件すべて未見の同条件比較とはしない。`baseline-exposure.json` と `baseline-switch/` に明記する。",'', '## 推論の一致・速度・再現','', 'PyTorchと独自JavaScript実装で、全22件の生成全文、全token、EOS、有効性が一致した。独立のlogit照合も保存。速度最適化は出力を変えない独自隣接heap BPEで比較し、モデルの自然さの改善とは混同しない。','',f"BPEの{benchmark['reference']['samples']}測定で、reference p50/p95は{benchmark['reference']['p50Ms']:.4f}/{benchmark['reference']['p95Ms']:.4f} ms、heapは{benchmark['heap']['p50Ms']:.4f}/{benchmark['heap']['p95Ms']:.4f} ms。完全なtoken列一致を確認した。CPUでのtoken化だけの値であり、通信・画面表示込みの速度保証ではない。",'', '2CPU quota、8GiB、GPUなしでFP32学習。BF16は実際のcompile後の比較で速くならず採用していない。optimizer・RNG・設定・原文・語彙・重み・評価のSHAは `reproducibility-manifest.json` に記録し、同じ設定／資料だけのresumeを許可する。再生成手順は [README.md](README.md)。','', '## 公開版と残る課題','', '公開版では「Nothing Headphone (1)について詳しく教えて」をスマホ幅／PC幅で確認し、デザインと複数仕様をまとめて返す。所有の一言で終わらない。「nothing headphone1」の表記揺れでも同じ詳細を返し、横はみ出しもない。Appleの日本語回答、興味と好きなものの区別、MER／VIVANTの説明範囲など、先に公開した本人回答修正を維持した。','']
    if not passed:text+=['**安定した自然な日本語生成が現在の阻害点。** 規模拡大・原文拡充・10,000更新＋追加10,000更新・段落境界とsubword継続の学習を行っても、活用・意味の接続・反復が厳格基準を満たさない。原文は古い文学に偏り、現代説明文や話し言葉の広い分布を十分に覆っていない。この2CPU／8GiBの小規模実験だけでChatGPT相当や社会で通用する広い会話能力を達成したとは言えない。言語段階が未達のため、本人QAの追加学習や原文候補の公開モデル置換へ進めていない。','']
    (ROOT/'RESULTS.md').write_text('\n'.join(text).rstrip()+'\n')
    print(json.dumps(dict(report='RESULTS.md',bothRunsCompleted=True,languageGatePassed=passed)))
if __name__=='__main__':main()
