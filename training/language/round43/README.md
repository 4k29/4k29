# R43 — auxiliary pool size only

実学習を継続中。初期0と実200・1000更新のfull model/Adam/RNGを保存・監査済み。200/1000更新はR42とmodel/moments/RNGが完全一致。1000の旧新24生成も全文core一致、日常意味0/12・反復4・EOS9、人間DEV NLL0.9435959363で一致。最終10000更新と意味改善の判定は未完了。元1616候補の同じSHA順先頭256→1024のみ変更。旧256は新poolの完全prefix。CE係数.1/every10/batch2、総10000更新/2000auxpairs、全main/モデル/LR/seed/R28fullstate/selector/gateを保持。固定TRAIN64の現pool重複は7組で別集計し未見評価とはしない。意味改善は未測定、公開/R25anchor維持。

新poolの先頭256は旧と同じため、最初1280更新はモデル/Adam/RNGがR42と一致する予測を開始前固定。初めて異なる正例を読むのは1290更新。200/1000のtensor一致を実測し、早期差や改善を捏造しない。
