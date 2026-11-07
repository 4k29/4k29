# Local storage layout

Only unused older prepared-data folders R29..R38/multiview are omitted from this compute working tree with Git sparse-checkout. The sparse layout omits no model exports or checkpoint parts; no Git history, data objects or current inputs were deleted. Earlier raw-copy cleanup is recorded separately and all raw states remain byte-exactly recoverable from Git parts. Current R43/R44 frozen input SHAs were verified before/after. Restore an old data folder when needed with `git sparse-checkout add --no-cone /training/language/round33/multiview/`. Full restore is `git sparse-checkout disable` when there is enough disk. GitHub/remote history retains all files.

R46も同じlocal sparse layoutを利用し、データ/履歴の一意な削除は行わない。
