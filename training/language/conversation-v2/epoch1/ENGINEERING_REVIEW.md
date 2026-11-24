# Independent engineering review

The pre-training implementation supports an exact continuation of the first shuffled epoch, with two counted replay updates per arm. No issue was found in the retained/actual update accounting, final batch of two windows, inherited Adam/RNG/order, or constant terminal learning rate. This is a conditional Go pending final source/input freeze and the runtime receipts; it is not a claim that training or language capability has succeeded.

Checkpoint chunks are verified before loading and before manifest replacement. A graceful signal stops at a complete update and saves the full trajectory. An arbitrary process failure between durable saves leaves a ledger gap and deliberately cannot auto-resume. tmpfs protects against process loss only; host memory loss before Git archival remains an explicit risk. Final Git archive verification and finite/nonnegative Adam moments remain required.

The canonical human-A/B mapping preserves every body and EOS token. The original TRAIN documents already begin with role3, so training data remains unchanged. New24 DEV cases are genuine human-human continuations, not an AI instruction benchmark; personal facts and missing advice/conditional-instruction categories must not be overinterpreted.

## Resume receipt defect found after launch

The frozen original resume path collided with the initial audit receipt. This was discovered during independent review after training had already launched. Training was gracefully stopped at retained580, with70actual continuation updates including2replays. The original --resume was shown to fail before any further optimizer update, and both its failure and stopped state were preserved.

A separately frozen wrapper changes only the receipt filename for resumed runs. An inverse text transform is byte-identical to the original source, and the AST is identical except for that pathname assignment. The wrapper revalidates the immutable source/plan and exact stopped checkpoint/ledger/deadline. This repair changes no model, data, optimizer, RNG, update, loss, LR, or evaluation condition. Process resume is approved after amendment commit; successful actual resumption still needs runtime evidence.
