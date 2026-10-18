# Reproduction

Restore own parent Round11 aligned checkpoint and baseline Round25 checkpoint from their lossless chunks if absent. Restore this round training-token parts if needed; all data files match Round25 exactly. Run execution/verify_single_factor.py, verify_runtime.py, preflight_initial_validation.py and tests before bash execution/persistent.sh. Requested10000 is never a completed count. Existing incomplete runs require --resume and exact identities; completed runs are refused.
