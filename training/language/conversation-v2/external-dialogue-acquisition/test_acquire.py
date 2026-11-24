#!/usr/bin/env python3
"""Offline contract tests for pinned candidate acquisition; no network use."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest
import zipfile

MODULE = runpy.run_path(str(Path(__file__).parent / "acquire.py"))
summarize_news = MODULE["summarize_news"]
summarize_jmultiwoz = MODULE["summarize_jmultiwoz"]
sha256_file = MODULE["sha256_file"]


class AcquisitionTests(unittest.TestCase):
    def test_news_turns_and_tweet_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.jsonl"
            cases = [
                {"dialog_id": "1", "dialog": [
                    {"speaker": "S", "utterance": "最近どう？", "used_tweet": []},
                    {"speaker": "U", "utterance": "元気だよ"}]},
                {"dialog_id": "2", "dialog": [
                    {"speaker": "S", "utterance": "ニュース見た？", "used_tweet": ["tweetid"]},
                    {"speaker": "U", "utterance": "見たよ"}]},
            ]
            source.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in cases), encoding="utf-8")
            stats = summarize_news(source)
            self.assertEqual(stats["dialogues"], 2)
            self.assertEqual(stats["turns"], 4)
            self.assertEqual(stats["dialogues_with_used_tweet"], 1)
            self.assertEqual(stats["dialogues_without_used_tweet"], 1)
            self.assertEqual(stats["malformed"], 0)
            self.assertEqual(len(sha256_file(source)), 64)

    def test_jmultiwoz_split_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "safe.zip"
            with zipfile.ZipFile(p, "w") as archive:
                archive.writestr("JMultiWOZ_1.0/dialogues.json", json.dumps({"d1": {}, "d2": {}}))
                archive.writestr("JMultiWOZ_1.0/split_list.json", json.dumps({"train": ["d1"], "dev": ["d2"]}))
            stats = summarize_jmultiwoz(p)
            self.assertEqual(stats["dialogues"], 2)
            self.assertEqual(stats["split_sizes"], {"train": 1, "dev": 1})

    def test_jmultiwoz_rejects_zip_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "unsafe.zip"
            with zipfile.ZipFile(p, "w") as archive:
                archive.writestr("../attack", "no")
                archive.writestr("JMultiWOZ_1.0/dialogues.json", "{}")
            with self.assertRaises(ValueError):
                summarize_jmultiwoz(p)


if __name__ == "__main__":
    unittest.main()
