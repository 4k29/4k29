# Matched original-TRAIN continuation diagnosis — observational only

This uses recorded self-negative histories during learning, not a final checkpoint's independent generation. Each trace was generated from that update's pre-update model, then used by its own regularizer. R28 first10000 and R33 next2000 aggregate different contexts and model states; their rates are not a paired causal model comparison. No alternative learning condition, new model forward, optimizer, heldout text or generated positive target was used.

For each actual recorded TRAIN prefix, retrieve the next at most64 original source tokens from the same admitted unit (including true EOS if reached). The real source prefix must match every recorded token. Count repeated fourgram-completion positions using the unchanged own objective code. Report full horizons and a common horizon equal to the shorter observed continuation, so source length/early EOS do not silently change the denominator.

| Recorded human TRAIN contexts | Calls | Common compared positions | Own repeated positions | Original-source repeated positions | Own fraction | Source fraction |
|---|---:|---:|---:|---:|---:|---:|
| R28 first10000 updates | 306 | 17255 | 10525 | 402 | 60.9968% | 2.3298% |
| R33 first2000 additional updates | 65 | 3480 | 2085 | 75 | 59.9138% | 2.1552% |

R33 own full horizons totaled3571 generated positions/EOS12, source4065 positions/EOS5; neither length nor EOS is silently equated. Raw all-site and per-site/per-view records remain in execution/matched-train-repetition-2000.json, with auditor/checkpoint/index SHA. Source continuations are measured original TRAIN, not added labels or manufactured answers. Different tokenization views remain matched within each source/model comparison. Fourgram repetition is not the full semantic rubric.

The model overproduces local repeated fourgrams compared with actual original continuations on these same training contexts. This does not support explaining the observed loops solely as literal equally repetitive raw source. It does not rule out genre/topic bias, insufficient coverage, weak conditioning, objective strength or capacity. It does not establish how the latest or selected final model behaves, or that R33's59.91% is an improvement over R28's60.99%: those aggregates are not matched contexts/states. Fixed-DEV unedited full generation and final assessment remain necessary.

Separate true-offset audit: during R28, only14/306 human negative prefixes ended after a true interior turn separator. During R33's first1300 updates,0/46 did. Most already contained earlier real turn separators, so context was present; the ending position was usually inside an utterance. Counts use original human utterance arrays and source SHA, not a newline heuristic (original raw utterances can themselves contain newlines). That distribution is a future hypothesis about negative-prefix selection, not a condition changed in R33 or proof that boundary-aligned negatives will improve meaning.
