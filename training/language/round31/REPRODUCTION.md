# Reproduction

Run prepare_suffix.py from a fresh directory copied from Round25 multiview data, freeze and preflight; then execution/persistent.sh. Existing partial checkpoints require --resume; completed10000 runs refuse restart. Full optimizer and RNG checkpoints are distinct from inference exports. Actual loss and update counts determine status.
