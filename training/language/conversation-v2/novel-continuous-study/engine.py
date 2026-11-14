"""Explicit guard. No C training runner is approved by this audit."""
import json,pathlib
if __name__=='__main__':
 plan=json.loads((pathlib.Path(__file__).parent/'PLAN.json').read_text())
 assert plan['training_GO']is False
 raise SystemExit('No-Go: insufficient quality-confirmed prose. No model import, forward or optimizer call. Use a new study and pre-fixed plan when adequate data is available.')
