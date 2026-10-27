#!/usr/bin/env python3
"""Acquire pinned licensed dialogue corpus CANDIDATES; never auto-admit to TRAIN.

Network fetches go into an ignored local directory, never committed to public Git.
Requires Python 3.9+ stdlib only. Run by an operator in an environment with
public internet access. This script does not attempt to bypass any access controls.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.request import Request, urlopen
import zipfile

NEWS_REV = "fd09d8a7cad99449c5353447b785985fe8ac9a32"
JM_REV = "a78dd334b907e12318b76bb23d0a9ed1498b8d15"
SOURCES = {
    "news_v1": (
        f"https://raw.githubusercontent.com/fukanarita/newschat-with-impression/{NEWS_REV}/V1.jsonl",
        "V1.jsonl", "MIT; possible third-party news/tweet-derived language"),
    "news_v2": (
        f"https://raw.githubusercontent.com/fukanarita/newschat-with-impression/{NEWS_REV}/V2.jsonl",
        "V2.jsonl", "MIT; possible third-party news/tweet-derived language"),
    "news_v3": (
        f"https://raw.githubusercontent.com/fukanarita/newschat-with-impression/{NEWS_REV}/V3.jsonl",
        "V3.jsonl", "MIT; possible third-party news/tweet-derived language"),
    "jmultiwoz": (
        f"https://raw.githubusercontent.com/nu-dialogue/jmultiwoz/{JM_REV}/dataset/JMultiWOZ_1.0.zip",
        "JMultiWOZ_1.0.zip", "CC BY-SA 4.0; human Wizard-of-Oz task-oriented dialogue"),
}
RIGHTS = {
    "news": "https://github.com/fukanarita/newschat-with-impression/blob/main/LICENSE",
    "jmultiwoz": "https://github.com/nu-dialogue/jmultiwoz/blob/master/LICENSE",
}
MAX_BYTES = 40 * 1024 * 1024


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="download-", dir=destination.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        req = Request(url, headers={"User-Agent": "conversation-v2-research-acquisition/1.0"})
        size = 0
        with urlopen(req, timeout=90) as response, temp.open("wb") as output:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError(f"Download too large: {url}")
                output.write(chunk)
        if size < 20:
            raise ValueError(f"Unexpectedly small payload: {url}")
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)
    return {"bytes": size, "sha256": sha256_file(destination)}


def summarize_news(path):
    dialogs = []
    speakers = set()
    count_turns = 0
    used_tweet_count = 0
    no_tweet_count = 0
    malformed = 0
    for line in path.open("r", encoding="utf-8"):
        if not line.strip():
            continue
        obj = json.loads(line)
        turns = obj.get("dialog", [])
        if not isinstance(turns, list) or not turns:
            malformed += 1
            continue
        if not all(isinstance(t.get("utterance"), str) and t.get("speaker") in {"S", "U"} for t in turns):
            malformed += 1
            continue
        has_tweet = any(bool(t.get("used_tweet")) for t in turns)
        dialogs.append(str(obj.get("dialog_id", "")))
        count_turns += len(turns)
        speakers.update(t["speaker"] for t in turns)
        used_tweet_count += int(has_tweet)
        no_tweet_count += int(not has_tweet)
    return {
        "dialogues": len(dialogs), "turns": count_turns,
        "unique_ids": len(set(dialogs)), "speakers": sorted(speakers),
        "dialogues_with_used_tweet": used_tweet_count,
        "dialogues_without_used_tweet": no_tweet_count,
        "malformed": malformed,
        "warning": "No used_tweet field is NOT legal clearance. Do not use for TRAIN until reviewed."
    }


def summarize_jmultiwoz(path):
    with zipfile.ZipFile(path, "r") as archive:
        all_names = archive.namelist()
        for name in all_names:
            p = Path(name)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError(f"Unsafe ZIP entry: {name}")
        matches = [n for n in all_names if n.endswith("/dialogues.json") or n == "dialogues.json"]
        if len(matches) != 1:
            raise ValueError(f"Expected one dialogues.json, found {len(matches)}")
        with archive.open(matches[0]) as f:
            dialogs = json.load(f)
        splits = [n for n in all_names if n.endswith("/split_list.json") or n == "split_list.json"]
        split_sizes = None
        if len(splits) == 1:
            with archive.open(splits[0]) as f:
                split_obj = json.load(f)
                split_sizes = {k: len(v) for k, v in split_obj.items() if isinstance(v, list)}
        if not isinstance(dialogs, (dict, list)):
            raise ValueError("Unknown dialogue container")
        return {
            "dialogues": len(dialogs),
            "split_sizes": split_sizes,
            "dialogue_type": type(dialogs).__name__,
            "warning": "WoZ data are role-played human task dialogues, not live SNS chat."
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(Path(__file__).parent / ".local-dialogue-acquisition"), help="Private output directory; keep untracked.")
    parser.add_argument("--source", nargs="+", choices=[*SOURCES.keys(), "all"], default=["all"])
    args = parser.parse_args()
    root = Path(args.out).resolve()
    root.mkdir(parents=True, exist_ok=True)
    selected = list(SOURCES) if "all" in args.source else sorted(set(args.source))
    results = {}
    for key in selected:
        url, filename, rights_note = SOURCES[key]
        target = root / filename
        try:
            record = download(url, target)
            record["url"] = url
            record["rights_note"] = rights_note
            record["status"] = "candidate-only; no training authorization"
            record["audit"] = summarize_news(target) if key.startswith("news_") else summarize_jmultiwoz(target)
            results[key] = record
            print(f"FETCHED {key}: {record['bytes']} bytes, {record['audit'].get('dialogues')} dialogues", flush=True)
        except Exception as exc:
            results[key] = {"status": "failed", "error": str(exc), "url": url}
            print(f"FAILED {key}: {exc}", file=sys.stderr, flush=True)
    manifest = {
        "purpose": "acquisition / inspection only — NOT admitted to TRAIN or DEV",
        "rights": RIGHTS, "sources": results,
        "known_restrictions": [
            "Never ingest social posts solely because they are public.",
            "News dialogues may contain paraphrases or quotations derived from third-party posts/articles.",
            "Audit personally identifying and sensitive information before any redistribution/training.",
            "Preserve original author attribution and source-specific sharealike conditions.",
            "Do not pool source train/dev/test or overlap existing conversation-v2 evaluations."
        ]
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest: {path}")
    return int(any(x.get("status") == "failed" for x in results.values()))


if __name__ == "__main__":
    raise SystemExit(main())
