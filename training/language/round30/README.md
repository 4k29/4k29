# Round30 — longer own-negative rollout, frozen one-factor experiment

Status: actual10,000 updates completed; selected9,500. Full final17+daily12+additional native8 outputs read and graded. Whole meaning remains0 in every set, common NLL is slightly worse than R25. Not adopted; public model unchanged. See RESULTS.md and execution/artifact-manifest.json.

Scientific control and last adopted settings: Round25. Only max generated negative rollout tokens64→128. Original positive corpus, 40/30/30 own-tokenizer views,8layers/192dim, LR, seed, parent aligned model/AdamW/RNG, teacherUL1.0 and sequenceUL0.1every10 unchanged. No human-corpus mixture or EOS-framing change. Daily conversation is the practical target; existing17 and12 daily DEV are exposed diagnostics, not TEST.

No public model/site changes. Original strict gates and conservative Pareto adoption remain. Full raw Python/JavaScript comparisons and matched optimizer/RNG archives are required. R29 improved NLL but was not adopted. Earlier R29 old-TEST-reference visibility incident remains disclosed in that round; those excerpts are not human-blind. No new TEST model use.
