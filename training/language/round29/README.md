# Round29 — human everyday-conversation sampling mass10%

Single factor: same8975 human TRAIN dialogues and all three token views asRound28, sampling mass30%→10%. Against the last adopted scientific controlRound25 this is0→10%, old genre masses×90%. Same alignedRound11 parent, optimizer/RNG, own8-layer192dim model, vocabulary, objectives, LR, seed, context256 and10000 actual updates. Round28 is not adopted or made the baseline. No turnEOS/role labels or inference changes.

Round28 humanDEV NLL improved27.94% but common NLL and daily loops regressed. Test whether a lower dose retains domain learning without those regressions. Original strict gates/Pareto and additional humanDEV/daily nonloop guards remain unchanged againstRound25. NLL improvement alone never means semantic success. Fixed17 and daily12 are exposedDEV, not freshTEST. No public/site promotion.

The identical copiedsource-policy.json describes historical admission/filtering atRound28 (including its30% mixture), not this run sampling; policy.json is the authoritative frozen10% configuration. Source manifest binds both. SameCC-BY-SA4.0 provenance, train/dev/test hygiene and raw-only reserved hashes are reused; no newly acquired/test-encoded source.

Training and automatic mechanical evaluation run under execution/persistent.sh; actual retained steps only are reported. Full human-readable judgments require actually reading every raw output, never guessed by automation.
