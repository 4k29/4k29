# R44 — main daily-conversation sampling only

実学習継続中。初期0・実200・実1000更新のfull model/Adam/RNGを保存・監査済み。予定10000更新は未完了。

唯一の学習変更はRealPersona主sampling25%→40%。JMRD5%固定、非会話70%→55%を相対比保持で縮小。資料・独自BPE・1024pool・全loss・モデル・LR・seed・R28 fullstate・10000dose・selector・全gateはR43と同じ。主draws/target量/RNGの差はこの条件に含め、各run固有の再現を検証します。426入力は開始前commit3298933で凍結済み。

実1000更新の会話DEV NLLは旧0.9435959363020515→新0.9388160688890173。共通DEVは旧0.9698808789995499→新0.970905335028921と悪化。生成12件の全文意味成立は旧0/12→新0/12、長い反復は4→5、EOS到達は9→8でした。新12全文を実際に読み、旧読解は凍結manifestと生成内容一致で再利用しました。全文・項目別判断・境界例の感度はexecution/paired-daily-generation-1000/に保存しています。中間診断であり、新TESTでも採用判断でもありません。途中の学習条件変更はありません。

TRAIN文脈64件の7/57区分はいずれもTRAIN。両区分の正解NLLは改善しましたが、正しい文脈による利得は小幅に低下しており、文脈利用や未見一般化の改善は確認できません。execution/paired-human-dev-1000/context-membership-subsets.json参照。

実1000更新のAdam stepは21000、全重み・momentはfinite。主target数は旧1567814/新1592603、Python/Torch RNGは両方異なります。学習変更に伴う差として保存し、旧と同一とは主張しません。公開モデル・サイト・R25anchorは維持します。
