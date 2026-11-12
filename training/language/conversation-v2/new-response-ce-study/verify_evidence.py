"""Zero-model integrity verification suitable for public CI."""
import pathlib,json,hashlib
P=pathlib.Path(__file__).resolve().parent;plan=json.loads((P/'PLAN.json').read_text());assert hashlib.sha256((P/'PLAN.json').read_bytes()).hexdigest()==(P/'PLAN.sha256').read_text().strip()
for f,h in plan['artifact_sha256'].items():assert hashlib.sha256((P/f).read_bytes()).hexdigest()==h,f
assert json.loads((P/'UPDATES.json').read_text())['actual_optimizer_calls']==0
assert not plan['learning_authorized']and not plan['user_confirmed_private_persistent_storage_available']
print('Public metadata/SHA verified; no model construction or raw source fetch')
