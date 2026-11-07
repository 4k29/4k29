# Local storage layout

Only unused older prepared-data folders R29..R38/multiview are omitted from this compute working tree with Git sparse-checkout. The sparse layout omits no model exports or checkpoint parts; no Git history, data objects or current inputs were deleted. Earlier raw-copy cleanup is recorded separately and all raw states remain byte-exactly recoverable from Git parts. Current R43/R44 frozen input SHAs were verified before/after. Restore an old data folder when needed with `git sparse-checkout add --no-cone /training/language/round33/multiview/`. Full restore is `git sparse-checkout disable` when there is enough disk. GitHub/remote history retains all files.

R46も同じlocal sparse layoutを利用し、データ/履歴の一意な削除は行わない。

R47資料はR46とimmutable hardlinkで共有。旧モデルrawの回収はGit追跡済みlossless partsの全SHA/再構成SHA確認と新入力に含まれない確認後だけ行う。唯一の原本/履歴を削除しない。

R47のarchived-checkpoint-sparse-proof.jsonにあるR40/R41分割ファイルの作業ツリーコピーだけを省略した。全Git blob/履歴は保持し、各partとconcat SHAを事前確認。新入力は除外。復元時は対象の!/path行だけをsparse patternから除いてset --no-cone --stdinを適用し、十分な空き容量を確認する。
