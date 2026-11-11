# 専用CI完了

[run42956370978](https://github.com/4k29/4k29/actions/runs/42956370978) は completed / success。入力commit c966137aff5eb0b086ab246aa69d7c7ce07487c3。

36個の固定成果物のbyte数/SHA256、4個のlossless圧縮JSONの復元SHAを検証し、12テストが合格した。保留本文・可逆tokenを公開するprivate中間物が追跡されていないことも確認した。結果はCI_RESULT.json、manifestはMANIFEST.json。ローカルの再照合でも36ファイル不一致0。

実optimizer0、保持/捨て/replay0、モデルforward0、新checkpoint0。合成logitsのautogradを用いたmask試験であり、自作Transformerの実モデル勾配/Attention/Adam/再開や言語能力の検証ではない。A/B実学習、NLL、greedy生成、Python/JS推論照合は未実施。独立人間評価もなし。

学習No-Goは維持し、処理中の学習・評価jobを残していない。旧研究、正式checkpoint、公開モデル/サイト、封印TESTを変更せず、PR111はDraftでマージなし。
