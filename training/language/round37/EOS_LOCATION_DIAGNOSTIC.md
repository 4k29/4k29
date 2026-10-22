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
