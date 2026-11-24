"""Lightweight result-integrity checks; cannot certify linguistic judgments."""
import unittest,json,pathlib
from summarize_results import aggregate,read
P=pathlib.Path(__file__).resolve().parent
class Results(unittest.TestCase):
 def test_completed_learning(self):
  r=read("RUN_STATUS.json");self.assertEqual((r["retained_updates"],r["completed_optimizer_calls"],r["additional_targets"]),(401,405,409856));self.assertEqual(r["automatic_replay"],0)
 def test_full_reading_coverage(self):
  panels={"native24","provided23","new-caption32","old24","oldNew9","new-MAFF12","new_source_heldout_paragraph5"}
  for stage,label in [("lr3-mid205","mid205"),("lr3-terminal401","terminal401")]:
   raw=read("evaluation/"+stage+".json");a=read("ADJUDICATION-"+label+".json");keys=[(r["panel"],r["id"]) for r in a["decisions"]]
   self.assertEqual(len(keys),129);self.assertEqual(len(set(keys)),129);self.assertEqual(set(keys),{(r["panel"],r["id"]) for r in raw["cases"] if r["panel"] in panels});self.assertFalse(a["independent_human_evaluation"])
 def test_caption_counts_and_membership(self):
  s=aggregate()["stages"]
  for name,count in [("lr3-mid205",21),("lr3-terminal401",23)]:
   a=s[name];self.assertEqual(a["semantic_counts"]["new-caption32"],count);self.assertEqual(len(a["caption_change"]["retained"]),20);self.assertEqual(len(a["caption_change"]["gained"])+20,count);self.assertEqual(len(a["caption_change"]["lost"]),1)
 def test_greedy_bytes_and_EOS(self):
  for stage in ["lr3-mid205","lr3-terminal401"]:
   e=read("evaluation/"+stage+".json")
   self.assertEqual(len(e["cases"]),149);self.assertEqual(e["optimizer_calls"],0)
   self.assertTrue(all(r["eos"] for r in e["cases"] if r["panel"]=="new-caption32"))
 def test_boundary_and_NLL_scope(self):
  for name in ["lr3-mid205","lr3-terminal401"]:
   s=aggregate()["stages"][name];self.assertEqual(s["boundary"]["n"],40);self.assertEqual(s["boundary"]["paired_n"],32);self.assertEqual(s["boundary"]["other16_gold_top1"],0);self.assertEqual(sum(x["targets"] for x in s["body_NLL"].values()),53847)
 def test_restores_and_frozen_inputs(self):
  v=read("FINAL_VERIFICATION.json");self.assertTrue(v["passed"]);self.assertEqual(v["frozen_SHA_checks"],93);self.assertEqual(v["cold_Git_restores"],[4,205,401])
  for x in read("CHECKPOINT_INDEX.json")["saved"]:self.assertTrue(x["cold_Git_restore"]["full_model_Adam_RNG_sampler_cursor_trace_integrity"])
 def test_parity_and_forward_ledger(self):
  p=read("parity-terminal-summary.json")["LR3-401"];self.assertEqual(p["comparison_positions"],12);self.assertEqual(p["same_history_argmax_disagreements"],0);self.assertFalse(p["complete_reply_parity_established"])
  f=read("FORWARD_COUNTS.json");self.assertEqual(f["Python_total"],19041)
  js=read("parity-terminal/LR3-401/javascript.json");n=sum(len(r["referencePythonHistoryScores"])+len(r["independentAutoregression"]["steps"]) for r in js["rows"]);self.assertEqual(n,f["JS_score_queries"])
if __name__=="__main__":unittest.main()
