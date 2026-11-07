# Matched5000 TRAIN-position EOS diagnostic

Round36 remains in training. This compares existing coefficient0/1 rounds and the current coefficient0.3 round at exactly5000 actual updates each. It adds no training condition, optimizer update, heldout access, generation or semantic grade. All use the same fixed12 TRAIN rows and boundary masks chosen for the prior Round35 posthoc analysis. The old coefficient0/1 numeric results were reproduced exactly, including checkpoint SHA and every group statistic. Raw results and reproduction hashes are in execution/.

| Positions / measure | R34 coefficient0 | R36 coefficient0.3 | R35 coefficient1 |
|---|---:|---:|---:|
| Eligible authentic utterance ends (67) / mean EOS probability | 0.032816995 | 0.174614877 | 0.369662851 |
| Eligible authentic utterance ends (67) / EOS argmax positions | 0 | 0 | 37 |
| Eligible authentic utterance ends (67) / original-gold NLL | 0.892809153 | 1.049059153 | 1.328342438 |
| Original content excluding every newline-containing token (1840) / mean EOS probability | 0.001823245 | 0.005638687 | 0.012166797 |
| Original content excluding every newline-containing token (1840) / EOS argmax positions | 3 | 19 | 45 |
| Original content excluding every newline-containing token (1840) / original-gold NLL | 3.280941963 | 3.285626411 | 3.294975042 |
| Original dialogue-final EOS (6) / mean EOS probability | 0.071075305 | 0.181753948 | 0.334974438 |
| Original dialogue-final EOS (6) / EOS argmax positions | 0 | 0 | 4 |
| Original dialogue-final EOS (6) / original-gold NLL | 2.906234741 | 1.929616332 | 1.285779476 |

At these measured positions, coefficient0.3 reduces the coefficient1 increase in EOS probability, content-position EOS argmax and original-gold NLL. Its EOS argmax count is0 at the67 eligible utterance ends, whereas coefficient1 gives37. At the1840 non-newline content positions it gives19, between coefficient0 (3) and coefficient1 (45). EOS on a content position is not by itself proof that an alternative continuation is wrong. The original dialogue-final EOS category contains only6 positions and is particularly small.

The authentic-end objective keeps original newline CE and adds EOS CE with the same denominator. Ignoring other losses, other examples and parameter sharing, the isolated-position optimum has p(EOS)/p(newline)=coefficient. A lower coefficient therefore cannot be assumed to yield correct greedy stopping, even when it improves original-gold likelihood. This observation is consistent with that competition; it does not isolate all mediated changes in self-generated unlikelihood targets.

Limits: selected TRAIN rows, correlated/possibly overlapping views, not a representative whole-TRAIN estimate, not independent replication, not an unseen test, and not free-generation evidence. The1867-position broader category includes27 newline-containing compound targets and must not all be called content interior. Do not infer improved meaning, fewer daily conversation loops or checkpoint adoption from these logits. No original gate, sampling, target, coefficient or selected-checkpoint rule changes in this round. Final selected/terminal full outputs and humanDEV99 still require evaluation.
