# Fixed-checkpoint context use and autoregressive diagnosis

Inference only, using our existing R46 selected raw FP32 weights (step9500). No optimizer is constructed, no parameters are updated, no checkpoint/selector/adoption criterion is changed, and no public model/site is replaced. The R48 full-mass CE concentration proposal remains No-Go. All work is on a separate diagnostic branch.

Before any own-model inference, freeze `PLAN.json`, the exact panel, manual lexical annotations, data receipts and code. Primary25 cases comprise12 previously fixed TRAIN originals (first6 per source) and13 exposed DEV originals. Every complete authentic next utterance is fixed across correct/mismatched/BOS-only contexts. Correct and mismatched contexts have exactly equal own-BPE lengths. No context or target is cropped. All75 primary free generations use full-vocabulary greedy192, genuine EOS and no penalties or repair.

Different-document, same-length donor selection is SHA-fixed. Before model outputs, four same-topic donor candidates were manually rejected with exact source/ordinal/reason receipts to obtain unrelated topics. Generic gold responses may remain appropriate under a different context; mismatched is not an invalid-answer training label. No training data is changed.

All1024 existing correct-context auxiliary TRAIN pairs are a separate teacher-forced-only supplement. They were used for auxiliary supervision, are anchor-selected, and contain403 target documents. They cannot establish unseen generalization. Their original mismatched donors are preserved; no semantic-negative claim is made. TRAIN, exposed DEV, sources and cohorts are never silently pooled.

BOS-only context removal also changes absolute positions. The controlled primary comparison is correct versus equal-length mismatched context. No fake BOS padding is introduced. Manual lexical phrases/inflected words are frozen before model scores; own-BPE word-boundary coverage is reported instead of treating BPE IDs as linguistic words.

Teacher-forced next-token scores use the entire original gold utterance, excluding EOS from its NLL; EOS at the gold end is separate. Same-gold scores after substituting generated history are counterfactual sensitivity probes: after the first departure they are not aligned language accuracy. First token departure and mechanical repeated ngrams are not automatically semantic failure. Whole unmodified outputs must be read for grammar, relevance, topic drift and meaningful repetition onset.

Original source licenses/URLs/hashes and split are retained. No sealed TEST is opened. Python raw FP32 diagnostic results are not a new JavaScript/full-hardware equivalence claim; known historical numerical branches remain disclosed. A same-history teacher-forced/incremental comparison records numerical discrepancies without hiding ties.

## Reproduction

`build_panel.py` reconstructs the data-only panel, including rejected donor receipts. `finalize_panel.py` applies the pre-output manual annotations to that exact unannotated panel. `run_diagnostic.py` requires explicit panel and plan SHA arguments and a NEW output directory. Do not silently overwrite a frozen panel/results or treat this as training. Synthetic tests load no own checkpoints. Exact commands and immutable receipts accompany the results.
