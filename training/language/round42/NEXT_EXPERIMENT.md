# 次の単一条件候補 — R42では未実装・実更新0

同じ1616候補のSHA順先頭を保持し、補助poolサイズだけ256→1024へ変更する。R42の局所pool改善が大きい一方、非poolTRAIN57への移行と日常全文改善が乏しいため、総2000auxpair露出を固定したまま反復頻度を下げ被覆を広げる効果を分離する。

R42を科学対照に同じR28 model/Adam20000/RNGから兄弟比較。候補2漢字条件/donor/canonical/CE.1/every10/batch2/cyclic、全main source25/5・40/30/30、モデル/LR/seed/10000dose/selector/生成/全gateを保持。document balancing・新資料・意味filter・dose/係数探索を混ぜない。pool構成・長さの変化はsize条件に含む。

全新poolを原典/token/境界/勾配で検証し、追加正例の全文を読んだ範囲を明記する。固定64診断は再選択せず新poolとのoverlap別集計を開始前固定、両方TRAINで未見ではない。旧新selected/terminal全168全文とhumanDEV99・数値を比較し、NLLだけで採用しない。実験前にこの案を設定として凍結する。
