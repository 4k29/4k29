# 保存範囲と再現手順

本研究は取得・審査の完了と学習No-Goの記録である。C学習、FAQ SFT、checkpoint復元、model forwardを実行したものとして再開しない。

読み取り検証:

```sh
python -m pip install -r training/language/conversation-v2/novel-continuous-study/requirements-data.txt
python -B training/language/conversation-v2/novel-continuous-study/verify_study.py
```

11検査は実在する原文候補のbyte/BPE復元、teacher shift/位置非重複、DEV不変、帰属、No-Go状態、PLAN SHAに加え、発見した数式/template除去断片のregressionと引用/画像/見出しでの境界を検証する。試験fixtureは自作の合成文字列であり、収集原文や学習教師に混入しない。Torchやmodelをimportしない。

原文候補は `REVIEWED_PROSE.jsonl.gz`、元の位置対応は `POSITION_MAP.json.gz`、窓は `SCHEDULE.json`。このscheduleは2767位置のコンパイル検証用で、学習許可ではない。`engine.py` はNo-Goを明示して停止するguardのみ。初期model/Adam/RNG、生成条件等は将来比較の予定としてPLANに残しているが、新モデルの作成や実行健全性を検証したことにはならない。

`acquisition/` に候補メタデータの抽出、公式API取得、段落抽出、重複照合、固定標本と個別判断の記録コードがある。取得原文全量は `/workspace/scratch/continuous/` の隔離cacheで処理した。公開すべきでない第三者引用や未審査原文を含むため、公開bundleには含めない。cacheは環境の永続性を保証できない。HTTP/版/本文SHAと原典URLはACQUISITION_RECEIPTSに残し、サイト更新・削除時に同一rawを再取得できない可能性を明記する。公開Gitだけから、引用を含む全取得原文の完全復旧はできない。

GV recordの `retrieved_UTC` は抽出時刻であり、厳密なHTTP取得時刻ではない。実取得日は2026-11-14。より近い時刻の手がかりはreceiptの元snapshotファイル書込み時刻proxyとし、元記事の公開/更新版日時とは区別する（METADATA_NOTE）。Wikiのretrieved_UTCはAPI取得後に記録した。

再取得・再処理を行う場合は、今回の固定原文・PLANや旧研究を上書きせず、新しい隔離研究領域で行う。`NOVEL_CACHE` で非公開の作業cacheを指定できる。本文SHA不一致を無視しない。個別の品質判定はスクリプトが意味や正確性を自動評価したものではなく、main agentが原文を読んで保存した判断である。

既存PR116 B-base/SFT-Bのmanifest・評価SHAはCHECKPOINT_INDEXの参照のみ。新しいcold復元や更新後再開一致を行ったというreceiptはない。新しいmodelが存在しないため、Python/JSモデル数値比較や勾配検証も未実施。旧成果を自分の新しい実測値として流用しない。
