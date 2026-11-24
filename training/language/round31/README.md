# Round31 — TRAIN duplicate suffix line cleanup

Actual training completed10,000/10,000 updates; selected step10,000. Common DEV NLL/byte0.9708387240808534, but first-sentence5/17, nonloop2/17, full meaning0/17; daily0/12 and native-dialogue0/8 meaning. Rejected under unchanged adoption rules; Round25 remains adopted research baseline. Public/site unchanged.

One-factor sibling of adopted Round25: only TRAIN suffix dedup-policy.json; same own8layers192dim, own BPE40/30/30, LR, seed,64-token self-negative rollout, genre masses, aligned Round11 parent model/optimizer/RNG. No generated positive targets or output repair. See RESULTS.md for complete measurements/limitations, execution/FINAL_FULL_GENERATIONS.md for all74 old/new unedited continuations, and REPRODUCTION.md for concrete reproduction/restoration commands. Midpoint actual/selected steps remain separate in INTERIM_RESULTS.md. Fixed199 learning inputs were not changed during training.
