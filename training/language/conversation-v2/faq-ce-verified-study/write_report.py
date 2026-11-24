import pathlib,json
P=pathlib.Path(__file__).resolve().parent;rd=lambda n:json.loads((P/n).read_text());s=rd('SUMMARY.json');f=s['series'][-1];aud=rd('CORPUS_AUDIT.json');es=f['evaluation'];r={a:rd(f'evaluation/{a}-study93-READING.json')for a in'AB'}
lines=['# FAQ全CE／返答CE：比較表','', '最終の372件系列を主結果とする。旧393・385件系列は原典抽出検査の不備を含むため別記し、置換・消去しない。意味判定はメインassistantの非盲検読解。独立母語話者評価なし。','', '## 最終TRAINと教師位置','', '| source | 件数 | 返答本文tokens | A全教師 | B返答＋EOS |','|---|---:|---:|---:|---:|']
for k,x in aud['parts']['train']['source'].items():lines.append(f"| {k} | {x['cases']} | {x['body_tokens']:,} | {x['full_teachers']:,} | {x['reply_plus_EOS']:,} |")
lines+=['| 合計 | 372 | 34,766 | 49,856 | 35,138 |','', '両条件の非PAD入力は49,856。全serialized列は50,228tokensで、各列の最後のEOSは入力xではなくshift後の教師yになる。質問本文13,602・質問EOS372・返答EOS372・role744。BOS/PAD教師0。LF教師141・空白教師269（A対象内、返答だけとは異なる）。同一原文をA/Bで使うため独立量は合算しない。','', '## 最終系列の共通返答NLL','', '| 状態 | TRAIN本文 | DEV本文19 | DEV本文＋返答EOS | 書式厳格DEV17本文 |','|---|---:|---:|---:|---:|']
for name in ['initial','A-study47','B-study47','A-study93','B-study93']:
 x=es[name];lines.append(f"| {name} | {x['pilot_train']['body']:.6f} | {x['dev']['body']:.6f} | {x['dev']['with_response_EOS']:.6f} | {x['strict_format_dev17']['body']:.6f} |")
lines+=['','中間47はNLLのみ。終端93を結果にかかわらず使用。本文NLLは返答文字列内のLF/空白を含み、EOS/roleを含まない。全有効教師のDEV NLLは今回別測定していない。全CEと返答CEのTRAIN lossは分母が異なるので直接優劣を判定しない。','', '## source別DEV本文NLL','', '| source | DEV件数 | 初期 | A93 | B93 |','|---|---:|---:|---:|---:|']
for source,x in es['initial']['source_dev'].items():lines.append(f"| {source} | {x['cases']} | {x['body']:.6f} | {es['A-study93']['source_dev'][source]['body']:.6f} | {es['B-study93']['source_dev'][source]['body']:.6f} |")
lines+=['','## 終端greedyの内容判定','', '| 指標 | 初期（既存証拠含む） | A全CE | B返答CE |','|---|---:|---:|---:|','| FAQ具体回答 | 0/19 | 0/19 | 0/19 |','| 根拠入力のFAQ補助課題 | 0/4 | 0/4 | 0/4 |',f"| caption自然候補 | 21/32 | {r['A']['caption_natural']}/32 | {r['B']['caption_natural']}/32 |",'| 新たなcaption合格（初期不合格から） | — | 0 | 0 |','| 段落2〜3文 | 0/5 | 0/5 | 0/5 |','| 展開文章 | 0/45 | 0/45 | 0/45 |','| 内容必須 | 0/24 | 0/24（別に保留1） | 0/24 |','| 資料付き | 0/23 | 0/23 | 0/23 |','| ASDC条件確認 | 0/15 | 0/15 | 0/15 |','| 自己履歴エピソード | 0/4 | 0/4 | 0/4 |','', 'caption自然候補のうち6件は既入力の名詞や文の語尾の短い補完。画像への事実一致を確認した評価ではない。初期21件のうち468221は両条件で退行、822181はAだけ退行。Bの「小さなパソコンの横に白い犬がいる」は自然候補だが初期にも合格していた入力で、新しい能力獲得ではない。CAPTION_COMPARISON.jsonに32入力別の元出力・両出力と判定を保存。','', '## EOS／反復proxy（意味成立とは別）','', '| panel | A EOS | B EOS | A反復4gram | B反復4gram |','|---|---:|---:|---:|---:|']
for g in es['A-study93']['panels']:
 a=es['A-study93']['panels'][g];b=es['B-study93']['panels'][g];n=a['cases'];lines.append(f"| {g} | {a['EOS']}/{n} | {b['EOS']}/{n} | {a['repeat4gram_proxy']}/{n} | {b['repeat4gram_proxy']}/{n} |")
lines+=['','段落5件はA3件・B4件が空白のみ。残りも空白や疑似英字などで本文は成立しない。旧展開45件のうちEOSはA7件・B5件だが、語尾や単語だけで段落成功0。EOSが出ても回答内容が正しくなったとは扱わない。','', '## 最終93更新の数値健全性','', '| 指標 | A | B |','|---|---:|---:|']
for label,key in [('保持更新','updates'),('有効教師','active_teachers'),('全更新clip','clipped')]:lines.append(f"| {label} | {f['arms']['A'][key]} | {f['arms']['B'][key]} |")
for label,key in [('勾配norm平均','mean'),('勾配norm最大','max')]:lines.append(f"| {label} | {f['arms']['A']['gradient_norm'][key]:.6f} | {f['arms']['B']['gradient_norm'][key]:.6f} |")
lines.append(f"| 更新weight L2平均（層別ではない） | {f['arms']['A']['per_update_weight_L2']['mean']:.8f} | {f['arms']['B']['per_update_weight_L2']['mean']:.8f} |")
lines+=['','## 全実行を含むledger','', '| 系列 | TRAIN/本文tokens | 保持/arm | 実optimizer | 捨て原更新 | 再開replay | forward | 秒 |','|---|---:|---:|---:|---:|---:|---:|---:|']
for x in s['series']:
 e=x['execution'];lines.append(f"| {x['folder']} | {x['train_cases']}/{x['reply_body']:,} | {x['arms']['A']['updates']} | {e['actual_optimizer_returns']} | {e['discarded_original']} | {e['resume_replay']} | {e['model_forward_returns']:,} | {e['seconds']:.3f} |")
lines+= [f"| 合計（独立データ量ではない） | 合算禁止 | — | {s['actual_optimizer_calls']} | {s['discarded_original']} | {s['replay']} | {s['model_forwards']:,} | {s['model_seconds']:.3f} |",'', '保持は全系列578、うち旧2系列392・主系列186。失敗したimport runはoptimizer0/forward0。最終系列の初期23生成＋391 TF記録は保存済み同一入力から再利用（forward相当1,668回を回避）、全logitsの再利用ではない。分析・専用CIはoptimizer0/forward0。','', '各runは無料公開GitHub Actions CPU4logical cores/Torch2threads、GPUなし、RAM約16GiB・開始空き約84.6GiB。元のローカルCPU2/RAM8GiB環境と同一ハードウェアの主張はしない。最終主プロセスpeak RSSは1,373,824KiB。主系列のmodel処理958.558秒、3系列合計2,520.630秒はsetup/取得・読解・Git upload等を含む全タスク時間ではない。','', '## 完全checkpoint','', '| 系列 | 保存点 | 個数 | 完全cold復元 |','|---|---|---:|---|','| 旧393 | A/B ×50,99 | 4 | 成功 |','| 旧385 | A/B ×49,97 | 4 | 成功 |','| 主372 | A/B ×47,93 | 4 | 成功 |','', '全SHA・bytes・Adam step・Git commitはCHECKPOINT_INDEX.jsonと元manifest/COLDに保存。全12状態のchunk/結合SHAとmodel/Adam/RNG/sampler/trace一致をremote-onlyで検証。各seriesで実更新後の別プロセス再開も一致。正式checkpointではなく隔離研究用。']
(P/'TABLES.md').write_text('\n'.join(lines)+'\n')
report='''# 日本語FAQによる全CE／返答CE比較

2026-11-13 JST。**原典境界を検査した372件・返答本文34,766独立BPE tokensを用い、両CEを各93更新・一巡学習した。FAQ具体回答は両方0/19で、正式採用・公開モデル置換はNo-Go。** 返答NLLは下がったが、必要情報を返す能力は確認できず、caption自然候補も初期21/32からA19/32・B20/32へ退行した。公開研究checkpointとの両立を確認して実学習・全文保存・完全復元まで進めた成果と、対話能力の未達を区別する。

## 取得・権利・出典

JaGovFaqs-22kをrevision `a9fd35ae0f7d984cef7c054cfa6ae68bc7b5d354` に固定し、22,794件・20,855,829bytesを監査用RAM領域に取得した。原配布READMEだけで全原文の権利が確定したとはせず、気象庁・文科省・環境省・デジタル庁の公式利用規約を一次確認した。原典規約snapshot・取得日時・SHA・URLはRIGHTSとACQUISITIONに保存。現行PDL1.0のCC BY4互換利用、帰属、改変表示、第三者権利の除外、政府の推奨を誤認させない条件を継承する。これらの採用原文にはichikaraのモデル公開禁止条件はなく、公開研究state保存と両立する範囲で使用した。

全文の他機関原文や未確認本文は公開Gitに保存せず、採用Q/Aと規約・公開可能なメタデータを分離した。原典の画像・ロゴ・第三者転載まで包括許諾とは扱わない。農水省は許諾確認しても既存source-held-outを守ってTRAIN0。ASDCも補助評価15件だけでTRAIN0、旧66件を再周回しない。外部モデル作成回答・既成Tokenizer・生成APIは使っていない。

22,794件が人間による独立新規回答の検証済み全量という意味ではない。配布者は人手抽出と記し、個別著作権を自称せず抽出誤りの可能性を説明している。公式機関の原文執筆者個人やAI混在の有無を全件独立確認できたわけではない。配布revision日は2024-02-29で、回答の更新日ではない。2014/2015等の原文日付は残し、2026年の制度・安全助言として現在も正しいと保証しない。

## 品質と分割

機械的候補は5機関1,496件。原典181 URLを少数並列・cache付きで確認し161ページを取得、元質問と回答の全文字列が一致する候補992件・94,393返答tokensを確認した。原典取得不能102候補、Q/A対応不一致402候補は保留。これらは段階ごとの候補数であり、全件合格や最終採用量ではない。PDF、context超過、医療等の高リスク、電話等の連絡先、参照不足、第三者権利不明、過去評価familyを除外した。リスク規則の「がん」が「愛がん」に誤反応した点は学習前に修正し回帰テストを追加した。

学習前にsource×質問proxy×長さの層別標本を固定して原文を読解した。事前抽出・再選別過程で76候補を読解し、最終TRAINにはそのうち44件が残る。重要なDEV19と高リスク候補も個別に読んだ。全TRAINを個別の人間審査済みとは扱わず、決定的検査と層別読解による限定採用である。原典の事実を別の独立資料で全件再検証したとも主張しない。

最終TRAINは372件、返答本文34,766tokens、原典ページ78・連結近重複family75。DEV19件・2,092tokens・8familyを保持。QA canonical重複は分離、近い質問(.85)/回答(.90)の5linkは同じfamilyへまとめ、過去原文/評価の既知URLと本文重複も除外した。機関・制度topicはTRAIN/DEVで共有し、個別著者は不明なので、話者独立・未知topic TESTではない。新DEVも本研究中に3系列の出力を参照済みで、開発評価である。

本文5万tokens目標には届かなかった。TRAINの質問proxyは定義199・条件100・手順49・理由11・比較13だが、分類器の自動ラベルで意味的認定ではない。比較proxy13件は全文を読み、実際に選択肢・基準を対比する確認済み例は5件。その他は所在地への質問、手順、理由、単一条件等だった。237件の複数句点も複数文の内容品質を自動保証しない。対応DEVには理由・定義・条件はあるが、真正な比較・助言・複数ターンの分離DEVは不足する。今回はFAQ能力の限定的探索比較で、全対話カテゴリが揃った本格汎用比較とは呼ばない。

## 検査の不備と再計算

最初のworkflowは新規select.pyがPython標準selectを隠してimport前段で失敗した。model forward/optimizerとも0。select_faqs.py/profile_faqs.pyへ改名してimport回帰検査後に独立runを開始した。

当初の原典検査が「部分文字列一致」で完結性まで保証すると扱った点は不十分だった。393件系列の開始後、質問index12461の先頭「資」が欠けた原文、制度・公園名の不足計8件を追加検査で検出し、別の385件系列へ分離した。さらに385件の比較カテゴリを全文読解し、index12541の回答「…雇用関係を結んでいる」が原典では「A研究機関となります。なお…」へ続く切断であると確認した。これは誤った終了教師になり得る。旧結果・原文・checkpointを後から補修しなかった。

原典DOMの開始・終了と自然な文末の照合を追加して、保守的なゲートを満たす372件を最終PLANに固定し直した。385件からの13件除外すべてを抽出誤りとは断定せず、書式やリスト終端を確認しきれない資料も保留した。質問の前後対応・既知の別質問が途中にないことも照合した。この構造検査は意味品質を完全保証しない。

DEV19は判定条件とともに変更せず、うち2参照はDOM/句点ゲートが保守的に不合格となるが、全文に必要事実があることを個別確認して評価専用として維持。17件の書式厳格部分集合でもNLL傾向を別報告する。どちらもTRAINへ戻さない。除外はモデル出力に有利な例の選別ではなく、原典比較で確認した検査不足に基づく。旧393/385の結果は数値証拠として残すが、主結論のコーパスではない。

## 入力・損失・実学習

共通初期はPR108 MIX-579 full SHA `fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7`。model/Adam moment・step6940/全RNG/samplerを復元し、元stateを変えず隔離した。PR109/110/114や今回旧SFTの終端を使わない。独自11.23M/BPE3997/context256、AdamW β(.9,.999)/eps1e-8/decay.05、LR1e-5、clip1を固定。質問と返答の原文字列・順序・真の終了を保ち、切断や編集で収めず最大serialized長255の完全QAだけを使用した。

BOS/slot3/質問/EOS/slot4/返答/EOSは両条件で同じ。slotは質問・返答の位置であり、元執筆者やAI経験ではない。旧人間A/B token履歴に完全なassistant意味が備わったと主張しない。Aは全49,856教師、Bは返答本文34,766＋真EOS372の35,138教師。質問はBでもAttentionに残り、loss外logit gradient0・質問activation gradient非0を実測した。両条件は有効教師数によるbatch meanなので分母と勾配スケールが異なる。同じ入力・更新予算でloss範囲を変えた比較であり、教師数一致の比較ではない。

原文を原則一巡、同一位置の重複学習なし、各93保持更新。中間47・終端93を事前固定し、途中生成を見て選び直さない。全更新でclipが発生し、平均勾配normはA3.5360/B3.9549。常時clipと低いLRは制約候補だが、今回変更しなかった。非有限・状態不整合・保存失敗なし。別プロセスで実更新後に完全再開し次更新の全状態一致、Adam非共有・初期A/B同一logitsを確認した。

主系列の実optimizerは192（保持186、捨て4、再開replay2）、forward26,939。旧2系列も含めると実optimizer596（保持578、捨て12、replay6）、forward96,426、主モデル処理2,520.630秒。独立原文量や主系列更新をこの合計で水増ししない。初期の保存済み同一23生成と391 TF記録を再利用してforward相当1,668を回避した。これは保存済み全logits再利用ではない。

無料の公開GitHub Actions CPU4logical/Torch2threads・RAM約16GiB・GPUなし、開始空き約84.6GiBを実測した。ローカル満杯ディスクには大きいstateを書かず、正式checkpoint・Git履歴を保持。中間と終端、A/B計4状態×3系列の12完全checkpointを32MiB chunkでGit保存し、新規bare Gitのremote-only cold復元でSHAとmodel/Adam/RNG/sampler/cursor/trace一致を確認した。主系列peak RSSは約1.31GiB（子プロセス合計peakではない）。同一run内の再開一致と、異なるhost間のFP32 bit一致は区別する。初期生成23件のtokenは旧2runで一致したが、NLLには約2e-8の差があり、異機種の数値完全一致は保証しない。

## NLLと無修正生成

共通参照DEV19の本文NLLは初期4.603824→A4.298014/B4.302010。TRAIN本文は4.639671→A4.240766/B4.233872。BのTRAIN値がわずかに良くてもDEVでAを上回ったとは言えず、自然な内容応答は両方0/19。資料を添えた別形式4課題も0/4で、知識の記憶不足だけでなく入力情報利用も未達。ただし読解形式自体をTRAINしていないという課題差は残る。

例えば住民票を問う入力でも、Aは日付の反復、Bは「大学校の発生活用…国際…」へ逸脱する。資料に住民票と書いても両方とも必要情報を返せない。全語彙greedyの無修正raw bytes・tokens・prefix・停止理由を保存し、改行抑制・反復penalty・本文強制・検索や生成APIによる補填は行わない。

caption自然候補はA19/B20、初期21のうちA2件/B1件が退行し、新しい成功入力は0。6件は語尾・既提示名詞の補完であり、自力で新しい文章を展開した証拠ではない。画像自体は評価していないので画像と真に一致する事実回答の成功率ではない。

段落0/5・旧展開0/45・内容必須0/24・資料付き0/23・ASDC0/15・自己履歴0/4は両条件で継続。Aの既存内容DEV1件「最近のゲームを見ます」は文として成立する可能性を認めつつ、作品を尋ねる文脈への具体回答と確認できず保留し、成功に加算しない。自己履歴は初回EOSが出ず後続を実施できない例と、3ターン出ても内容が成立しない例を別記した。EOS増加や単なる自然な相槌を合格にしていない。

## 判断と限界

公開可能な原典照合済みFAQを確保し、実モデルの2損失方式を比較する学習経路は成立した。しかし、3.5万本文tokensの一巡で自然な具体回答は獲得できなかった。NLL改善が自由生成の成功に結び付かなかった結果であり、返答CEの一般的な優劣や無効性は証明しない。短文保持はBがAより1件多いが、非盲検の小さい開発標本で一般的優越とは呼ばない。

政府FAQには外部知識と制度topicの偏りがあり、日常会話・比較・助言・複数ターン教師は十分でない。原典の現在性、個人著者独立性、語義レベルの近重複、全件の人間執筆確認・独立事実検証にも限界が残る。特に、元モデル自身の自由段落生成が未達な状態で応答学習を吸収できるかを次の主要仮説とする。容量不足やAttention欠陥とは断定しない。

正式採用・公開置換はNo-Go。GOAL.md・旧ゲート・正式R25/R46・旧研究を変更せず、封印TESTは未使用、サブエージェント0、有料資源0、公開サイト変更0、PRマージ0。同じ少量FAQの追加epochやLR微調整を自動で開始しない。次の研究1件はNEXT_STRATEGY.md。再現コマンドはREPRODUCE.md、数値・個別判定はTABLES/SUMMARY/evaluation、専用CI結果はCI_RECEIPTを参照する。
'''
(P/'REPORT.md').write_text(report)
