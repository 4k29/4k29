# 次期11.23M比較：実データ量から決める学習準備

## 因果比較と実際の能力を分ける

PR92〜95を継承する。最初の1epochで本文NLLは改善したが、内容必須24件0成功・自己継続4件0成功。これは日本語基盤学習も応答能力も未達という証拠であり、容量不足だけの証拠ではない。64組暗記の成立は未知会話への一般化ではない。

第一候補は同じ中型11,225,280parameters、8層/d320/heads4/FFN1280/3997語彙/context256。初期checkpointはepoch1 terminal3470、完全state135,802,269bytes、SHA256 `5ad249d2c8d5910090c9baba94f94483e9c037139d15b9c4360fd3e975409544`。model全tensor、AdamW全moment/step/paramgroup、Torch RNG、private sampler RNG、order/cursor/historyを継承する。学習率は既存終端の3e-5を連続使用し、warmupやmomentをresetしない。

普通の全有効target CE、既存PAD=-100、FP32、globalclip1、既存FP64ノルム集約、固定4×256batch、全生成条件と旧厳格ゲートを維持。変更するのは原典データ条件だけ。4RP窓対2同一RP窓＋2新しい応答資料窓を比較し、各slotの有効target長を同じにする。body/EOS/roleの頻度差はデータ条件の一部で、全ての内訳が一致するとは主張しない。

## 実装した具体的な非反復schedule

`matched_schedule.py` はmodelもoptimizerも作らず、実際のRP token列と候補の原文token列から、最大2048更新/armの有限なscheduleを生成する。実際の更新数は `floor(長さを一致させられた新原文窓数/2)` 以下とし、足りない窓を再利用して予定2048へ水増ししない。

同じsource familyに複数の返答経路がある場合、事前固定SHA順で1本の完全経路だけを採る。短い経路を優先する等の品質に関係しない長さ選択は行わない。共有prefixの複製量を増やさず、完全な発話末尾EOSを残す。各経路を256target単位で一度だけ分割し、途中にBOS/EOSを追加しない。RP側も、共通窓と置換対照窓は全てdistinctにする。

OASSTの全361未採用候補からの**機構確認用**scheduleは69family/92新原文窓/46step/arm、29,989有効targets/armだった。新原文分は12,433targets（本文12,049/EOS192/role192）、真の経路末尾69。control本文26,139/EOS1957/role1893、treatment本文27,401/EOS1304/role1284。これらは品質採用前の量であり、正式な学習実行条件ではない。候補の全prefixを反復すると66,410tokensになることを新しい独立量と誤認しない。

品質選別後は `--decisions` を指定し、`decision=accept` かつ `full_history_safe_for_ce=true` のIDに限定して同じルールで再計算する。最後の返答だけ良くても、historyに架空自己属性・誤情報・権利例外が含まれれば、普通の全CEではその悪い本文も学習する。今回はresponse-only maskingを混ぜて問題を隠さず、祖先が安全な候補だけを採る。accepted候補が少なければ実際の小さい予算のまま報告し、その規模で十分な言語学習が可能とは判断しない。

JMultiWOZは公式TRAINだけを別候補として扱う。人間operatorによる内容応答でも、施設の事実が外部DBに依存する場合、発話本文だけから答えられるcontext-grounded応答とは別である。新しいDB serializationを今回のデータだけの比較へ混ぜない。候補全件と、原文根拠/履歴の安全性を確認した採用分を分けて計量する。

## 入力契約を一度に変えない

人間A/Bのrole3/4と、OASSTのprompter/assistant役割の意味は異なる。どちらも同じ既存IDで表現できるが、執筆者をroleと同一視しない。実際のsource-local執筆者IDは分割/監査に保持する。AIの能力・家族・職歴を人間原文から捏造する正解にしない。

MRMPCは3話者の原典として保持する。予約ID5を第三人間roleにする研究候補はparameter増加が不要でも、未学習embedding行の意味を変更する。独立した入力契約研究で、byte復元、話者帰属、真のEOS、全話者dose、勾配・完全再開、比較対照を先に固定する。2roleへ潰す、第三者だけ除く、mention_toを親投稿に置き換える処理はしない。

## 次の比較を開始する条件

今は本学習No-Go。必要な条件は、(1)全CEで使える原文と権利/個人情報例外の個別admission、(2)未知familyかつ既存話者と独立性を確認できる評価資料、(3)その資料を見た後の事後調整を禁止する固定ベンチマーク、(4)実量に基づくschedule SHAと固定terminal、(5)初期checkpoint全state復元と新条件の有限gradient/clip、(6)中断→再開と連続実行の完全一致、(7)atomic保存に十分な永続容量。

これらを満たした最初の試験で変える条件はデータ配分のみ。matched scheduleでの固定terminal3470+Nを両armで評価し、loss最小checkpointの事後選択は行わない。再開一致確認のreplay更新も実更新として別ledgerへ記録し、予定Nを完了数として扱わない。

## 成功・失敗の事前固定案

旧17/13/9、Pareto条件、日常会話反復上限と公開モデル採用基準は変更しない。次の内容応答比較の追加条件案は、内容必須DEV24件でcontrolより少なくとも4件多く全文適切、反復/逸脱/終了の退行なし、新規context-grounded DEVで80%以上の全文文法・意味・必要内容の同時成立、reason/compare/conditional/reference各型で最低1件成功、とする。これは今回の生成を見て決めた値ではなく、**将来の正式な評価資料の固定時に採否を決める提案**である。今回合格を宣言しない。

teacher-forcedの正しい/無関係/文脈なしで同じ返答を測る診断、自由生成の無修正全文/token列、自己生成履歴での複数ターンを併用する。表現だけ変わることや相槌で終了することを文脈理解としない。独立した日本語母語話者2名以上の盲検判定と不一致処理は正式評価前に必要。assistantの選別はその代用ではない。

NLLだけ良いなら採用せず、正しいhistory予測も弱い場合は基盤の分布/学習量/容量を独立比較する。正しいhistory予測が良く自由生成だけ崩れるなら自己履歴の誤差蓄積を診断する。少数のaccepted資料が暗記できても一般化の証拠にしない。小さな損失係数変更を機械的に繰り返さない。

## 正確な既知資源と未測定資源

モデルFP32重みは44,901,120bytes、重み+勾配+Adam2momentの16N静的下限は179,604,480bytes（activation、attention、Python、コピーを含まない）。実際のepoch1完全checkpointは135,802,269bytes。初期/一方のterminal/次のatomic saveの3完全コピーだけで407,406,807bytes必要で、両terminalと保存予備・ログ・履歴増加を安全に扱うには少なくとも512MiBの追加永続headroomを学習前に確保する。RAM-backed tmpfsを永続容量として数えない。

旧CPU実測1133有効targets/secでは、候補29,989targets/armは約26.5秒/armの単純計算になるが、小さいpartial窓では同じ4×256計算を行うため過小評価の可能性がある。実行時間保証ではなく、新条件の実測profileを別途行う。前回実モデル4batchのゼロ更新監査最大RSS約916MiBは同形の参考値で、新条件のgradient/再開は未検証。CPU2core/RAM8GiB/GPU0の現環境で今回のデータ処理は実行可能だが、本格学習の承認ではない。

100M targetsなら旧CPU値から約24.5時間/arm、1Bなら約245時間/arm。GPUは未取得でtokens/secも未測定。11M/context256を8–16GiB、より大きい独自モデル/512–1024contextを12–24GiB級等でprofileする案は保証ではない。CUDA/AMPの数値整合性、再開、Py/JS公開推論との既知分岐を保持して確認する。100M以上の原文、token cache、checkpoint世代には追加50–100GB程度を形式別に再見積りする。

広い現代日本語の基盤学習→具体的内容を返す2役割応答→自己履歴を含む複数ターン→知識/推論、の順序を基本方針とする。混合/段階的追加/保持CEの配分は独立比較で決め、単純なepoch追加や大規模化それ自体を成果にしない。
