# Round40 結果 — 文脈gapの改善は自然な生成へ移らなかった

**実10,000回のoptimizer更新を一度完了、不採用。** 共通DEV・会話DEVの選択状態NLLは僅かに悪化し、日常全文の意味成立は0/12のまま。native8の選択状態はloop2→1、source5は最小相槌0→1だが、内容のある対象参照・新情報の改善は実証できなかった。最終状態では日常loop6→7、native loop2→3。全従来言語ゲート、固定会話NLL条件、R39/研究anchor R25へのPareto条件が不合格で、公開モデル・サイトは変更していない。

## 実行と単一条件

R39と同じR28 latestのmodel、Adam counter20000、Torch/privatePython RNGから開始した兄弟比較。R39terminalの単純延長ではない。8層192/heads4/FFN768/context256/dropout0.1/4,655,808 parameters/独自5455語彙、CPU2/FP32/seed系譜2049/LR2.2499999999999998e-5/wd0.05/clip1/batch8、同じ10000dose、共通DEVを0/every500で測るselectorを維持した。

唯一の学習変更は、人間TRAIN原文の正しい2発話文脈と同token長・別文書の文脈で、同じ次発話の平均token NLLを比較する補助目的 `0.1 * mean softplus(correctNll - mismatchedNll)` をevery10/batch2で追加したこと。eval-modeでも勾配を計算し、fork_rngと元のmodel modeを戻す。生成した正解、他モデルの回答、外部の学習済みweights/tokenizer/APIは使わない。

main data全35ファイル、source RealPersona25%/JMRD5%（人間計30%）、main BPE40/30/30、教師4gram UL1、自己生成negative UL0.1/every10/greedy64、真の発話末尾EOS補助0.3、対象改行のmain CE除外と元のvalid-target分母はR39と同じ。**追加補助目的はcanonicalのみで、全目的を合算した露出が40/30/30になるとは主張しない。**

2026-10-23T10:30Zに起動、約13:18Zまでに学習完了。checkpoint計測10074.549516799001秒（学習・DEVを含む）。実counterは全パラメータ30000、選択状態9000のfull aligned counter29000。中断・重複訓練・途中の条件変更はない。100 trainingログ・21 DEVイベントを保存。training曲線は100更新ごとの**一つのミニバッチ**で、全TRAIN平均ではない。

main実露出は15,578,400 targets /54,368,222 bytes、80,000行。view抽出32003/23922/24075、人間source RP20124/JMRD4055で、全体の抽出列・最終Torch/Python RNG・真のEOS補助対象156558か所/9191batchがR39と一致した。補助は実1000呼出/2000組、元のgold47833tokens、両文脈でscore95666tokens/input276126tokens。全256組をcyclicに参照し、実stepと履歴、exposure、有限値を独立検証した。追加optimizer.stepはない。

41 unit contracts、全189166 TRAIN行のprefix/mask、全data SHA、実モデル勾配、初期model/moments/RNGと全DEVの完全一致、400凍結入力を学習前に確認。補助256組すべてで元の発話オブジェクト・source SHA・TRAIN分割・連結のtokenization・同長/別文書を確認。語彙や原文は書き換えていない。最初の64組は学習前に全文を読み、残り192組は開始後に追加読解した。全件を事前に意味監査したという主張はしない。

## 同じ入力・生成条件での結果

42露出DEV入力（従来17/日常12/native8/別出典5）を、greedy192・全語彙・Python1thread・無修正で比較した。新しい選択/最終の84状態出力は全prefix/全文を読み、79種類のprefix/全文組に整理。5重複は同判定、同じ初文の33照合も同成分点を維持した。旧選択42は再生成raw coreの完全一致後にR39読解を再結合、旧最終42はR39凍結成果のSHA/bytes照合を伴う履歴再利用。独立・盲検の人間評価ではない。4状態168全文を[無加工で保存](execution/ALL_FOUR_STATE_GENERATIONS.md)し、全token列をJSONに残した。

| 指標 | R39選択9000 | R40選択9000 | R39最終10000 | R40最終10000 |
|---|---:|---:|---:|---:|
| 共通DEV NLL/byte | 0.965276906820 | 0.965337249841 | 0.965644446420 | 0.965669155745 |
| 会話DEV99 NLL/byte | 0.934594382344 | 0.934598192708 | 0.934098717368 | 0.934037243105 |
| 固定RP TRAIN99 NLL/byte | 0.907145654377 | 0.907099825491 | 0.905600342570 | 0.905534951749 |
| 従来17 初文 | 6 | 6 | 7 | 7 |
| 従来17 非loop | 2 | 2 | 5 | 4 |
| 従来17 全文意味 | 0 | 0 | 0 | 0 |
| 日常12 全文意味 | 0 | 0 | 0 | 0 |
| 日常12 長いloop | 4 | 4 | 6 | 7 |
| 日常12 EOS | 8 | 8 | 7 | 6 |
| native8 全文意味 | 3 | 3 | 2 | 2 |
| native8 長いloop | 2 | 1 | 2 | 3 |
| native8 EOS | 8 | 8 | 7 | 7 |
| source5 全文意味 | 0 | 1 | 0 | 0 |
| source5 長いloop | 1 | 1 | 2 | 2 |
| source5 EOS | 4 | 4 | 3 | 3 |

全17/13/9 scopeとnarrative/expository群が初文80%・非loop90%・全文意味80%を満たさない。文法2・接続2・合計9以上・閉文・valid tokenという既存初文条件も変更しない。固定会話DEV bound0.9107185711429243を新旧の悪い値へ緩めず、daily whole0/nonloop4のfloorとR39比の非悪化条件も保持した。選択状態human NLLが上がるためpaired practical条件も失敗した。

nativeのwhole3/2は最小相槌や共有の好みで、content beyond backchannelは両状態2、明示的対象参照0、新情報0。source選択のwhole1は、土産店とロープウェイの話への「そうですね。」という自然な受け止めのみ。source5はONE cast family/3公開仮名話者であり、5人の独立TESTではない。新TEST一般化は評価していない。

## 成功と混同しない失敗例

待ち合わせ時刻への選択状態の**生成全文**:

```text
天気の毒が出るのか？
```

挨拶の切替時刻を話したnative文脈では、旧115tokensloopが新17tokensEOSへ短くなったが、**新生成全文**は:

```text
そうなんですね。それはどうしてもおいしいですか？
```

意味が通る会話になったわけではない。source5の改善1件も「そうですね。」という最小相槌で、対象や新情報が増えた証拠ではない。最終状態の日常では「そうか」の連打、公園の長い所有句loop、nativeでは米・お前はおいしいへの逸脱が残る。創作の存在や外部API/統計/法令の真偽だけで失格にせず、主述・係り・内部意味・接続を評価した。

曖昧さも保存: 夕食の質問を未提示他者への自然な問いと補うならdaily whole1、解析雨量を道具として読むならoriginal whole1、source最終の「あとは？」や「何かあったんですか？」を場所追加/動機確認と補う代替などがある。有限法律/会合列挙や短い家族所有句はprimaryでは非長期loop、長い相槌・同文連打はEOSでもloop。広い/狭い反復解釈は各読解JSONに記録し、primaryやgateを結果に合わせて変更しない。

## 文脈診断と指標の限界

補助集合256は163正例文書・45donor文書/49 donor prefix。3文字以上の漢字spanを共有する条件は長い漢字語に偏り、北海道13組などのliteral偏りがある。これはtopic classifierではない。原文の本/国の取り違え、内蔵脂肪、多角面等も無修正で含まれる。corpusのSHA一致は全人間文が自然という証明ではない。不一致文脈からでも可能な返答があり、binaryの「間違った回答」という正解ラベルは付けていない。

| TRAIN診断 | R39選択 | R40選択 | R39最終 | R40最終 |
|---|---:|---:|---:|---:|
| 補助256 正しい文脈NLL/token | 3.631771 | 3.568419 | 3.617299 | 3.550039 |
| 補助256 gap（wrong-correct） | 0.202642 | 0.365598 | 0.198644 | 0.373911 |
| 別の64 正しい文脈NLL/token | 3.483394 | 3.488198 | 3.477242 | 3.482519 |
| 別の64 wrong文脈NLL/token | 3.581521 | 3.600924 | 3.576188 | 3.598347 |
| 別の64 gap | 0.098127 | 0.112725 | 0.098946 | 0.115829 |
| 別の64 正gap件数 | 48 | 49 | 45 | 46 |

64組は補助と同一の(document,turn)を含まないが、同じTRAINから選び文書の重なりもあるためholdout TESTではない。gapは、正しい文脈を改善せず不一致側の尤度を壊しても上がる。今回は256への適応は進んだが、64のcorrect NLLは両状態で悪化した。局所的な補助集合適応・topic shortcut・代理指標への最適化と整合し、一般的な文脈理解の実証にはならない。

1000時点の旧新24全文も読解済みでwhole0→0/loop3→4/EOS10→10。common/human NLLの僅かな改善を意味向上にはしなかった。5000ではhuman NLL0.94184901→0.94185127、64組のgapは増えたがcorrect NLLも悪化。5000で日常自由生成は実行していない。これらはfinal84や新TESTと混同しない。

## 原因の切り分け

| 仮説 | 観測と限界 / 次への意味 |
|---|---|
| 容量不足 | 4.66Mの共有表現で目的間tradeoffはあり得る。R27の限定的FFN768→1536試験でも日常意味は実証されなかったが、全ての拡大を否定はしない。今回のproxy改善/生成停滞だけから即拡大しない。 |
| データ不足・偏り | main source/bytesは完全同一。小さな漢字span補助集合・donor再利用・元の誤字には偏りがある。単なるsource比率変更ではない今回も内容の参照が増えず、会話の幅・質は未解決。 |
| 分割・文字境界 | 語彙、全main BPE、真の発話境界/maskを保持し、auxの元文字列と連結tokenを全検証。新84と自己negative1000はUTF8 validで、明確なbyte破損では説明されない。語や形態の混成は残り、形態境界の影響までは否定しない。 |
| LR・optimizer・目的 | counters/moments/RNG/勾配・合成係数は正常で対照と抽出も一致。最適LRを証明はしない。softplusの相対目的はwrong NLLを上げるだけでも改善し、correct NLL悪化と整合。係数を盲目的に上げない。 |
| context256 | 固定42prefixは192生成を含め256内に収まり、現評価は推論contextの切落としが先に起きない。短い時刻・好みへの逸脱もあり、延長だけの根拠ではない。長い訓練会話の制約は未否定。 |
| 学習不足・過学習 | 実10000完了。補助集合と64組との差は局所適応と整合するが、全TRAINの過学習とは断定しない。TRAIN99は旧RP subsetでJMRD込み全TRAIN平均ではなく、DEVと話題/長さも未対応。R33の追加doseでも日常意味0だったので回数追加を自動選択しない。 |
| 推論数値誤差 | 新84/84 Py/JS、84/84 raw FP32/7桁export全文一致。今回の失敗はこの差では説明されない。既知R10 near-tie16/17は保持し、他hardware/全時刻一致の保証にはしない。 |
| 評価方法 | mixed DEV・人間NLL・contrast gapを言語ゲートの代わりにしない。roleなしnative/sourceでも内容不足が残り、role形式だけのせいとは言えない。DEV露出、human99の完全重複1組、source1 cast、非盲検・解釈感度を明示する。 |

選択TRAIN99 NLL0.90714565→0.90709983、DEV0.93459438→0.93459819、gap0.02744873→0.02749837。最終はTRAIN0.90560034→0.90553495、DEV0.93409872→0.93403724と僅かに改善するが、daily/native loopは悪化。これを理由にselectorを最終へ差し替えない。

## 数値・再現性・保存

新84/84でPython/JavaScriptのtoken・全文・EOS・UTF8 flagが一致、raw FP32と7桁exportも84/84一致。測定reference最大差はJS1.33514404296875e-5、raw/export1.9788742065429688e-5、従来tol2e-4のまま。referenceは一部logitsで全時刻/全hardware保証ではない。旧選択JS42件を現runtimeで確認、旧rawは追加25件のみで元17を再実行しておらず、旧terminalは凍結履歴。既知R10 near-tie16/17（参照SHA117e5f69…）を隠していない。

962 repository testsは0 failure、既存公開モデルの43質問/2580応答回帰も成功。これらは公開挙動の保護であり、R40言語能力の証明ではない。公開コード・モデルは変更しない。全6保存役割(initial0/200/1000/5000/selected9000/latest10000)のfull model/Adam/RNG、lossless parts、selected FP32 weights、コード/data SHA、実counter、loss曲線、全168全文、読解・失敗/感度・次候補を保存する。

訓練用凍結入力400のSHAを後から変更していない。中間読解のtext digest表現だけを従来canonical JSON方式へ修正し、raw全文・採点・学習には変更がないことを24件で再検証した。上流R39のoperator policy出力の広範囲表示事故はR39記録を参照し、本実験を未露出TESTとは扱わない。R40のモデルにTEST文を入力・tokenize・損失評価・生成した結果はない。

次は[補助損失の形式だけを正しい文脈CEへ変える対照](NEXT_EXPERIMENT.md)を提案。まだ実装/訓練は0更新。R40は採用せず、研究anchor R25と公開挙動を維持する。
