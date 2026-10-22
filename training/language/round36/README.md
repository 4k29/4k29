# Round36 — completed training; semantic review pending

Actual additional optimizer updates: **10000/10000**. The run has finished, with Adam counter30000. The predeclared common-DEV selector chose actual8000 with aligned Adam28000; selected and terminal model/optimizer/RNG states are saved separately. Only EOS auxiliary coefficient1.0→0.3 changed against Round35; both trials used the same aligned Round28 parent and fixed remaining settings.

Selected common DEV NLL/byte:0.9677411390068936 (Round35:0.9678213304515457). Human DEV99 NLL/serialized byte:0.9073871096397005 (Round35:0.9107185711429243). These are exposed DEV diagnostics, not a new TEST or proof of improved Japanese meaning.

All168 old/new selected/terminal full state outputs are saved in [execution/MECHANICAL_ALL_FOUR_STATE_GENERATIONS.md](execution/MECHANICAL_ALL_FOUR_STATE_GENERATIONS.md). New selected42 and terminal42 full sequences each match Python/JavaScript and raw/rounded inference in the measured scope. The known historical Round10 numerical divergence remains recorded; this does not establish universal parity.

**Full semantic reading and strict language-gate judgment are pending.** No semantic score has been invented, no model has been newly adopted, and the public model/site is unchanged. At the user's request this is a stopping boundary: no Round37 has started.

[execution/boundary-status.json](execution/boundary-status.json) records verified states and numerical scope. [execution/boundary-artifact-manifest.json](execution/boundary-artifact-manifest.json) hashes saved artifacts; it is a handoff manifest, not a completed language assessment. [REPRODUCTION.md](REPRODUCTION.md), [HYPOTHESES.md](HYPOTHESES.md) and [EOS_LOCATION_DIAGNOSTIC.md](EOS_LOCATION_DIAGNOSTIC.md) preserve reproduction and bounded analysis. Do not retrain the completed10000 updates.

Next work: read all42 new selected and42 new terminal full prefixes/continuations, bind actual judgments to generation hashes, compare the unchanged strict gates and daily guardrails, then finish the assessment and final artifact manifest. Do not run the pending-reading finalizer before that work.
