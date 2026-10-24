# R46 再現手順 — 開始前、実更新0

科学対照はR44、Git上の前ラウンドはR45。R45係数0.2は採用しない。R44の係数0.1・主RealPersona40%/JMRD5%・同じ全資料/1024pool/own BPE/モデル/全目的関数を固定し、実updateの学習率だけ2.2499999999999998e-5から4.4999999999999996e-5へ変更する。core10ファイルは対照と同一。

開始前にsource-manifest.jsonの各入力SHA、データ同一性・全行マスク・sampling・初期全DEV・勾配・43 Python契約試験・962 Node試験・公開43問2580応答・JS構文を確認する。初期model/Adam moments・counter20000/PythonとTorch RNGは同じR28最新fullstateを使う。親のbeststateと最新optimizerを混ぜない。

初期checkpoint-0.ptではoptimizer LRも親と完全一致する。実updateの直前に既存train.pyがCLI LRを全param-groupへ設定し、全updateは新しい固定LRで進む。initialization-description-erratum.jsonに継承された文字列「hold terminal learning rate」と実動作の差を記録する。

開始コマンドはリポジトリ直下で `bash training/language/round46/execution/persistent.sh`。既存checkpointやlockがある場合は新規実行しない。部分実行を正確に継続するときだけ、保存状態と実counter・ログ・traceを確認して `bash training/language/round46/execution/persistent.sh --resume`。completed10000の再実行は禁止。

checkpointのlossless partsは `python training/language/round46/checkpoint_chunks.py restore <manifest.pt.chunks.json>` で全SHA検証後に復元する。必要な空き容量を先に確認する。R45のraw重複のみ約448MBを回収し、全Git追跡part・manifest・履歴を保持した。詳細はexecution/reversible-disk-cleanup.json。科学対照R44と初期親R28のraw状態は保持。

checkpoint0/200/1000/5000/selected/terminalは同一軌跡の保存点。実1000/5000診断と固定10000の評価を混同せず、更新数・損失・生成全文をそのまま記録する。旧新selected/terminalの168全文、新84全文の実読解、PyJS/raw-export一致、元17件と日常12/native8/source5の厳格ゲートを確認する。全て既存DEVであり新TESTではない。NLLやEOSの改善だけで意味能力を判定しない。公開サイトとR25anchorは維持。

データには過去ラウンドと共有するhardlinkがある。既存データを直接上書きしない。新データ条件を扱う別roundでは独立したコピーかatomic replaceを使う。
