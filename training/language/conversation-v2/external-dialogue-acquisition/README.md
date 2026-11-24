# Additional Japanese dialogue sources — acquisition only

These are **new** source candidates for conversation-v2, in addition to already-audited
RealPersonaChat, JMRD, MRMPC, OASST2 and the foundation-data collection.

## New candidate sources

1. **News chat with impressions** by Fuka Narita et al., [source repo](https://github.com/fukanarita/newschat-with-impression), MIT (original repository LICENSE); [research article](https://doi.org/10.5715/jnlp.31.1015). Human participants produced two-role Wizard-of-Oz news discussions. Repo total: 1,047 dialogues, 11,713 turns. Independently fetched and parsed V1 and V2 via the GitHub connector on 2026-10-27: **425 dialogues / 4,789 turns**, comprising V1 202 / 2,293 and V2 223 / 2,496; 346 of those 425 dialogues have at least one `used_tweet` reference. V3 was not fully inspected in this session. **News articles and third-party tweets are separately owned; repo MIT license does not necessarily license their original text.** No dialogue is formally admitted to training.
2. **JMultiWOZ** by Nagoya University, [source repo](https://github.com/nu-dialogue/jmultiwoz), **CC BY-SA 4.0**. Approx. **4,246 human Wizard-of-Oz dialogues**, in travel, hotel, restaurant, shopping, taxi and weather scenarios. Real human input, but scripted task-oriented roles rather than open-ended SNS conversation. Preserve upstream dataset split, attributions and ShareAlike obligations. Separate from evaluation benchmarks.
   
Both links are to the original publishers. Never combine raw text into the public repository
without an independent review of privacy, attribution, third-party quoted content and licensing.

## Retrieve and inspect in Codex / local environment

Python 3.9+ standard library; **requires ordinary public-network access**:

```sh
python3 training/language/conversation-v2/external-dialogue-acquisition/acquire.py \
    --source all
```

The script pulls **fixed upstream commit SHAs**, performs bounded downloads, checks
checksums, parses and counts dialogues, guards against ZIP path traversal, and
saves a detailed local `manifest.json`. It does not construct training pairs,
perform model updates, inspect sealed TEST, alter the public site, or commit raw
corpus text. Keep `.local-dialogue-acquisition/` out of Git.

**Next gate before any learning:** complete rights and privacy review; inspect
sampled conversations (especially those with `used_tweet`), verify speaker and
reply relations, compare with existing source/author/family splits, and build
content-demanding DEV independent of all training material. Only then assess
how many conversations and tokens are admissible.

**Current execution boundary:** This ChatGPT runtime cannot perform direct
large binary downloads from external hosts. The code and fixed source references
are available here, but full raw acquisitions have not been executed in Codex
or this runtime. Partial V1/V2 source records were fetched and audited using
the GitHub connector. Do **not** claim the entire datasets were downloaded.
