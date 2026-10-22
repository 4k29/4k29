# Mid-run observations — final assessment pending

Round37 is running; this note is posthoc analysis of already saved evidence, not a pretraining hypothesis, completed10000 result or change to the frozen plan. Only eligible original newline main CE is excluded; EOS0.3 and all other learning conditions remain fixed. Common/human DEV continue using original gold targets. Masked TRAIN CE must not be sold as directly comparable original NLL improvement.

## Same-actual1000 generation

Both raw FP32 models were evaluated on identical exposed daily12/native8 inputs, greedy192/context256, one Python thread. All40 full outputs were actually read and saved with SHA-bound per-row judgments. No interim JavaScript/export parity, independent blind human review or new TEST claim. This posthoc diagnostic does not influence checkpoint selection or learning conditions.

| Diagnostic | Retained newline R36 | Excluded newline R37 |
|---|---:|---:|
| Daily12 whole meaning | 0 | 0 |
| Daily12 primary long loops | 12 | 5 |
| Daily12 EOS | 0 | 8 |
| Native8 primary compatible speech acts | 0 | 3 |
| Native8 primary long loops | 8 | 1 |
| Native8 EOS | 0 | 8 |

Native3 includes2 short backchannels and1 agreement with an implicit actress referent. Requiring content beyond backchannels gives1; explicit referent/content gives0. Counting the finite42-token sour-drink repetition as nonlongloop gives0 loops rather than1 but does not fix its meaning. No original17/13/9 strict gate is evaluated or relaxed by these supplemental20 inputs. Whole daily0 prevents interpreting termination as broadly meaningful language.

Example unchanged full new output to `友人：明日の待ち合わせ、何時にする？\n私：` is `天気の毒が出来るのか？`: short EOS, inappropriate word combination, no meeting time. The complete40 outputs, including long failures, are in execution/paired-development-1000/FULL_GENERATIONS_AND_REASONS.md. Some finite repeated outputs remain intrusive even when primary nonlongloop.

## TRAIN-only mediated change

The100 scheduled negative rollouts through actual1000 use exactly the same source rows/prefix IDs; their evolving model weights differ. Human35 EOS rises16→33 and generated tokens1326→401; all-source100 totals4161→3263 tokens, repeated negative positions1746→1086. All35 human paired texts were actually read; many new completions are generic acknowledgements or unrelated questions. These are changing TRAIN-state max64 diagnostics, not frozen DEV192 evidence or100 independent samples. The objective change also changes subsequent negative text/length, so its direct effect cannot be separated from that mediated change with this comparison.

## Likelihood and remaining explanations

| Actual updates | R36 common DEV | R37 common DEV |
|---|---:|---:|
| 0 | 0.971898957127 | 0.971898957127 |
| 500 | 0.971475464075 | 0.971495448211 |
| 1000 | 0.971016699110 | 0.971076999219 |
| 1500 | 0.971564958420 | 0.971509395940 |
| 2000 | 0.971572300646 | 0.971517322309 |
| 2500 | 0.970893315781 | 0.970858746466 |

Small changes alternate sign; this is not a final NLL success or language finding. Original data exposure at2500 matches exactly3,892,923 targets /13,592,267 bytes /39,219 eligible excluded newline positions. The original-main-CE active positions are therefore3,853,704; exposure counts retain original stream positions.

Capacity remains unresolved: R27 FFN768→1536 did not establish daily meaning improvement, so this round does not enlarge the model. LR/Adam/RNG corruption is not observed in saved audits but optimality is unproven. Own BPE40/30/30 and eligible-end coverage stay fixed; mask correctness does not prove optimal tokenization. These short DEV inputs plus192 fit256, excluding inference history clipping as their observed trigger; learned memory may still be weak. The selected/terminal curves and humanTRAIN99/DEV99 comparisons are pending and cannot yet establish undertraining/overfitting. Final Python/JavaScript/raw-export measurements remain pending, with historical Round10 near-tie divergence retained.

A new human JMRD TRAIN candidate was acquired separately, SHA/license/attribution and protected64-character overlap checked, with no upstream valid/test acquisition or model evaluation. It remains unadmitted. Movie genre restriction, frequent literal acknowledgements and a shorter median utterance prevent assuming automatic benefit. Future use would require its own frozen one-factor round after current final results; no data change is made mid-run. See execution/next-source-not-admitted/README.md.

Continue the fixed10000 updates, preserve aligned selected and terminal states, complete all original42 fixed generation/numerical probes in each new state and actually read their complete outputs. Fixed practical floors remain humanDEV≤0.9107185711429243, daily whole≥0, nonloop≥4; they must not be lowered to R36's worse nonloop0. No adoption, deployment, merge or new TEST follows this interim note.
