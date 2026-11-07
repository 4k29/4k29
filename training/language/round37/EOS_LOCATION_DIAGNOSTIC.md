# Actual5000 matched TRAIN-position diagnostic

Only original eligible newline main CE differs. Both models have actual5000 updates /Adam25000 from the same aligned Round28 full state; EOS coefficient0.3 fixed. The same12 TRAIN rows, salt and all old Round36 category values were reproduced exactly. No heldout, generated positives, optimizer update, semantic grade or selection change. Small correlated TRAIN subset, not a whole-corpus estimate or generalization test.

| Category | Count | R36 mean EOS | R37 mean EOS | R36 EOS argmax | R37 EOS argmax | R36 original-gold NLL | R37 original-gold NLL |
|---|---:|---:|---:|---:|---:|---:|---:|
| Eligible true end | 67 | 0.174615 | 0.452223 | 0 | 49 | 1.049059 | 5.029821 |
| All newline-free content | 1840 | 0.005639 | 0.007627 | 19 | 45 | 3.285626 | 3.267379 |
| Original dialogue EOS | 6 | 0.181754 | 0.402998 | 0 | 5 | 1.929616 | 1.398122 |

The treatment raises greedy termination pressure at eligible human ends while reducing likelihood of the excluded original newline. Original labels and the full denominator remain unchanged in evaluation. Do not replace DEV newline gold with EOS to hide this tradeoff. Common weighted DEV at5000 improves0.970094710562→0.969979167754, but excludes expanded human DEV; final humanDEV99 remains pending. These aggregate diagnostics cannot determine final content quality.

At content positions EOS pressure also rises; its becoming argmax is not automatically an ungrammatical alternative continuation. Original content NLL improves in this selected subset. Direct end-target effects and changed later self-negative text/length are mediated together and not separated. At1000, paired fixed DEV output reading found shorter loops but daily12 whole meaning0; final selected/terminal raw192 generation and all numerical checks remain pending.

Full counts, uncensored group probabilities and checkpoint/code/data SHA: execution/eos-location-effect-5000.json; exact old-control reproduction: execution/eos-location-control-reproduction.json. Scope/cautions predeclared in the diagnostic plan. No adoption, new TEST or public model change.

## Subsequent same-actual5000 human DEV check

The exploratory follow-up measured both raw FP32 checkpoints on the unchanged99 human DEV files,390 canonical windows,66,402 original targets,247,408 serialized bytes. Every document/token identity and window setting matches; the original evaluator is recovered byte-for-byte by undoing only the saved raw-loader/report-metadata patches. No optimizer, TEST, model selection or mid-run condition change; raw Python only, no interim JS/export claim.

Human original-gold DEV NLL worsens **0.914884896722→0.939224732172**, delta+0.024339835451, while common weighted DEV improves. This is direct evidence that the common selector does not summarize human conversation and that the target tradeoff reaches original human-DEV likelihood. It does not attribute all aggregate loss change to the67 selected TRAIN end positions, identify final-state performance or grade meaning. The final selected/terminal humanDEV measurements remain required. See execution/paired-human-dev-5000/{plan,control,new,comparison}.json.

## Original human-DEV token-category decomposition

A further read-only pass added category sums to the same evaluator. Undoing its recorded patches recovers the raw evaluator exactly, and both models reproduce their original per-document/full NLL **exactly**. All original contexts/targets remain in the aggregate. Categories are tokens, not character likelihood; compound-newline tokens can also contain content.

| Original target category | Targets | R36 mean CE | R37 mean CE | Change in contribution / serialized byte |
|---|---:|---:|---:|---:|
| Standalone newline16 | 1637 | 1.087372 | 5.328797 | +0.028063817 |
| Compound newline token | 1253 | 2.387134 | 2.389238 | +0.000010656 |
| Dialogue EOS | 99 | 2.189696 | 1.893981 | -0.000118330 |
| Other original content | 63413 | 3.490798 | 3.476689 | -0.003616295 |

The aggregate human-DEV regression is predominantly an original newline-serialization cost; it is inaccurate to describe all of it as worsened content prediction. Content-token teacher-forced CE improves slightly in this fixed sample. Neither that nor EOS gains proves grammatical/contextual free generation. The unchanged original aggregate and fixed practical guard remain binding; do not drop newline categories, substitute EOS labels, select weights by the decomposed loss or call this a new gate. Final generation remains decisive for Japanese meaning. Repeated passes were needed to resolve the aggregate tradeoff, not repeated optimizer conditions. Receipts: execution/paired-human-dev-5000/*decomposition*.json.
