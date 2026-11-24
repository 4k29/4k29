# 再現手順

既存PR111をbaseとする研究ブランチ上で実行する。公開モデル・旧報告を変更しない。

1. `response-ce-study/unpack_results.py`で旧固定パックの両SHAを検証し展開する。
2. `CE_V2_ROOT`をconversation-v2、`CE_PRIOR_ROOT`をresponse-ce-studyに設定し、`search.py`を実行する。固定seed・既存審査文書の除外・全履歴context上限を維持する。`PRIVATE_CARDS.json`はローカル限定で、Gitへ追加しない。
3. `annotate.py`は保存済みの主エージェント読解判定を再適用する。スクリプトによる意味品質の自動認定ではない。旧196件の判定を変更しない。
4. `audit_data.py --repo /path/to/repo --prior /path/to/response-ce-study`で集計する。SHA、source内話者・family・本文近重複・byte/BPE復元を確認する。
5. `test_study.py`は保存済みの実行証拠を読むだけの軽量テスト。optimizerを起動しない。

学習は専用Actionsの固定GOファイルで一度だけ実行した。完了済みGOを再発火しない。engineは既存UPDATESを検出した場合停止する。main学習は未承認である。pilot16返答は将来のmain候補から別記して除外する。

checkpointは`artifacts/{A,B}-PILOT{2,4}/checkpoint.json`に5分割のサイズ/SHAと全体SHAを保存する。`runtime.loader.load_checkpoint`で各部分→全体を検証し、RAMへ復元できる。COLDファイルは別bare GitでGitHubから取得した原本のみでの全model/Adam/RNG/sampler/trace一致証拠であり、通常の保存確認と区別する。

本文や履歴には元の人間A/B役割を保持する。人間の自己申告をAIの自己属性とみなさない。CC-BY-SA-4.0の帰属情報は元レコードから継承し、再配布条件・削除申立ては既存response-data/sns-dataの運用に従う。保留本文を新しい公開成果物へ転載しない。自動判定だけで個人情報や全世界での話者独立性が保証されるわけではない。

個別生成判定は`python response-learning-study/unpack_reading.py`で両SHAを検証してREADING.jsonを展開する。元生出力はevaluation/*.jsonとEXTRA_EVALUATION.jsonに圧縮せず保持している。
