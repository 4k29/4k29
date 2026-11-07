# R47 reproduction — actual10,000 complete

完了済みなので同じ作業directoryで学習を再起動しない。source-manifest.jsonの433入力SHA、policyのコード/データSHA、execution/artifact-manifest.jsonの各成果を検証する。初期0/200/1000/5000/selected9500/latest10000はmodel/Adam/Torch RNG/private Python RNGの対応fullstateをlossless partsで保存。各checkpointの.chunks.jsonからcheckpoint_chunks.py restoreで元バイト列を復元できる。

別directoryでの再現のみ、固定入力/独自BPE/CPU FP32 deterministic2threads/seed2049を使い、execution/persistent.shを参照する。初期はR28latest/Adam20000/RNG、CP0は親LR2.25e-5を保持し実update時LR4.5e-5。同一条件partialの再開はtrain.pyの--resumeを用い、実step/optimizer/RNGの一致を先に確認する。予定stepを完了扱いしない。

学習済み検証: python training/language/round47/execution/verify_final_artifacts.py --require-tracked（repository root）。不在の必要rawだけ復元するため空き容量を先に確認する。追加optimizer更新なし。旧round全体の復元は不要。

全168出力の本文/tokenは未修正。DEVと新TESTを混同しない。result内の旧UL0.1説明文はexecution/objective-description-erratum.json参照。新データ条件ではimmutable hardlinkを直接上書きせず、独立copy/atomic replaceを用いる。
