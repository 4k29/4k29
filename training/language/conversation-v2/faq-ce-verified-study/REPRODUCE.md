# 再現手順と保存の境界

このフォルダが最終の原典境界検査済み比較。`../faq-ce-study`（393件）と`../faq-ce-clean-study`（385件）は、後で見つかった抽出・文脈不備により主結論から外した旧系列であり、その入力・PLAN・checkpoint・ledgerは改変しない。結果の良し悪しによる選別ではない。最終DEV19・判定条件は旧系列から変更していない。

## 軽量な検証（モデルを構築しない）

```sh
V2_ROOT=training/language/conversation-v2 python training/language/conversation-v2/faq-ce-verified-study/verify_inputs.py
V2_ROOT=training/language/conversation-v2 python training/language/conversation-v2/faq-ce-verified-study/verify_evidence.py
python training/language/conversation-v2/faq-ce-verified-study/numerical_contract.py
```

`verify_inputs.py` は入力全件の独自BPE/byte、教師shift、全質問と返答のcontext適合、分割、事前PLAN SHA、原典の完結境界を確認する。`verify_evidence.py` は3系列の実optimizer/forward ledger、元のbatch順、4状態×3系列のmanifest/cold復元証拠、raw生成と採点元SHAを照合する。大きいcheckpointのchunkを再取得したり学習を再実行したりしない。`numerical_contract.py` は合成logitsのPython/JS masked CE計算だけの限定照合で、Transformer全体のJS数値一致ではない。

## 原文と出典

`rebuild_inputs.py --raw /path/to/pinned-data.jsonl` はJaGovFaqs固定revisionのSHA、全391採用Q/Aとcopyright/URL、token列を照合する。省略時は原配布ファイルを取得するが、全量は監査用隔離に置き、公開Gitには書かない。採用372TRAIN+19DEV以外を自動追加する機能はない。資料の公開・学習の可否はRIGHTS・原典規約snapshot・各行の出典記録に従う。

候補抽出・層別読解・原典取得は `../faq-ce-study/{profile_faqs,verify_sources,select_faqs,finalize,freeze}.py`、追加境界検査は同フォルダの `audit_{question_boundaries,adjacency,answer_strict}.py`、最終除外はFINAL_ADMISSIONを参照。開発時cacheパスは各script冒頭のP/V/QUARANTINEで明示されている。原典HTMLが更新されると過去SHAを再取得できないため、live取得の完全再現を保証しない。最終採用Q/Aと位置・snapshot SHAは固定保存する。raw文字列を修復・省略せず、NFKC/空白除去は照合だけに使う。

原配布ファイルの抽出誤りを実際に検出した。部分文字列一致だけでは完結性を保証しない。`ANSWER_BOUNDARY_STRICT_AUDIT.json` は原典DOM開始・終了と自然な文末の確認であり、全事実の正確性や原典著者個人を保証するものではない。DEVのうち2例はこの保守的な書式ゲートを満たさないが、全文を個別に読んで必要事実の完結を確認した評価参照で、TRAINにはしない。

## 入力・損失

`[BOS=1, slot3, question..., EOS=2, slot4, answer..., EOS=2]`。slot3/4は質問と原文返答の位置識別であり、執筆者やAIの個人的経験を意味しない。旧checkpointでは人間A/B会話も学んでいるので、旧roleの意味がassistantへ完全適合したとは主張しない。今回のA/Bではこの表現・全入力・右PAD・順序を同じにする。各資料は独立QAであり、無関係文書を連結しない。

Aは全非PADのshift後教師、Bは返答本文と真EOSだけ。両者は各batchの有効教師数でmean正規化するので、分母・勾配量・教師総数は異なる。質問はBでもAttentionと勾配経路に残る。正解EOSは完全なFAQ回答の終端であり、元ページ全体の文書末端や任意window切断ではない。全serialized長は最大255で切断なし。新しいtokenやTokenizer学習はない。

## 実行と完全復元

既存完了runを再実行しない。新しい再現をする場合は、独立branch/worktree・新run IDで、元PLANと同じデータ・初期MIX-579を明示する。無条件のworkflow rerunは禁止。元SOURCE full SHAは `fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7`。元Adam step6940、model/Adam/RNG/samplerを継承し、PR109/110/114または今回旧SFTの終端は初期にしない。

`CHECKPOINT_INDEX.json` のmanifestとcold.source_commitを使い、そのGit commitだけを新規bare repositoryへfetchし、各partを順に結合する。全part SHA・bytes・結合SHAを確認後、torch.loadの内部integrity、model/Adam/全RNG/sampler/cursor/traceを検証する。cold証拠は実際にremoteのみ・alternatesなしで照合したもの。chunkはGit上にあるのでローカルで欠けても正式checkpointを削除して容量を空ける必要はない。新規作業コピーの再構築には最低2GiB以上の安全余裕を持つ。

捨て検証4更新と別プロセス再開replay2更新を各系列の保持更新から分離する。`UPDATES.jsonl` と `FORWARDS.jsonl` はintent/returned両方の実呼出し。checkpointとledgerが一致しない場合に自動replayしない。モデル学習には無料の公開GitHub Actions CPUを使用し、ローカルの満杯32GiB領域や正式R25/R46は変更しない。

## 評価の再集計

`summarize.py`、`adjudicate.py` は保存済みrawを集計し、optimizer/forward0。個別意味判定はメインassistantによる非盲検読解で、自動proxyや独立母語話者評価ではない。参照文と違うだけでは失敗とせず、必要事実・条件・話題の維持で判断する。採点元ファイルSHAと入力別理由をREADINGへ残す。

原文DEV19は外部知識FAQ。grounded4はその人手原文を資料として付したプログラム構成評価で、独立した人手QA4件の新規取得ではない。旧129件・ASDC15・自己履歴4は露出済み診断。新DEVも本研究で3系列の比較を閲覧済みで、独立TESTや盲検評価とは呼ばない。初期旧評価はPR108/114を再利用し、最終系列の初期新DEVは同一入力・同一checkpointの保存済み23生成と391 TF記録を再利用する。全logits再利用とは異なる。

生成は全語彙greedy、token抑制・penalty・検索補填・文章修正なし。rawBytesHex、token、stopReasonを保持し、反復圧縮表示や文章抜粋は読解用だけとする。自由生成を行わない中間はNLLだけであり、中間checkpointを事後選択しない。
