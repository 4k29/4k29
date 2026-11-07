"""Durable ungraded full-text assembly after actual completion; no model/Git/grades."""
import pathlib,json,subprocess,sys,time,hashlib,datetime
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
flag=E/'mechanical-full-assembly-complete.json'
if flag.exists():raise SystemExit('Already assembled; do not duplicate')
while True:
 try:
  if all(p.exists()for p in [E/'automatic-publish-complete.json',E/'fixed-source-mrmp-dev/mechanical-complete.json',D/'mechanical-complete.json',E/'human-train-gap/complete.json']):
   r=read(R/'continue-10000/result.json');assert r['completedRun']and r['completedSteps']==10000;break
 except (json.JSONDecodeError,FileNotFoundError):pass
 time.sleep(45)
for script in ['assemble_full_outputs.py','assemble_three_states.py','assemble_matched_terminal.py']:subprocess.run([sys.executable,str(E/script)],check=True)
pin=read(E/'terminal-control-reference.json');same=read(D/'mechanical-complete.json')['terminalAndSelectedWeightsExactlyEqual'];old=read(R.parent/'round40/continue-10000/result.json');lines=['# All four states — mechanical assembly; semantic reading pending','','Both rounds actually completed10000 updates. These are168 state outputs for42 fixed exposed DEV inputs, not168 independent examples. All texts are unedited. This assembly assigns no language scores and does not certify actual semantic reading. Old outputs retain historical provenance; current manual judgments must be checked separately. Source5 are one cast family.','']
paths={'original17':('old-validation.json','new-validation.json'),'daily12':('daily-old-python.json','daily-new-python.json'),'native8':('content-native-dev/old-python.json','content-native-dev/new-python.json'),'mrmp5':('fixed-source-mrmp-dev/old-python.json','fixed-source-mrmp-dev/new-python.json')};count=0
for item in pin['groups']:
 group=item['group'];op,np=paths[group];oldend=R/item['terminalPath'];assert sha(oldend)==item['terminalSha256'];states=[read(E/op)['rows'],read(E/np)['rows'],read(oldend)['rows'],read(E/np if same else D/f'{group}-python.json')['rows']]
 assert all(len(x)==item['inputs']for x in states);lines += [f'## {group}','']
 for rows in zip(*states,strict=True):
  assert len({x['id']for x in rows})==len({x['prefix']for x in rows})==1;lines += [f"### {rows[0]['id']}",'','Prefix:','```text',rows[0]['prefix'],'```','']
  for label,row in zip([f"R40 selected{old['bestStep']}",f"R41 selected{r['bestStep']}",'R40 terminal10000','R41 terminal10000'],rows,strict=True):lines += [label+':','```text',row['text'],'```',''];count+=1
assert count==168;out=E/'MECHANICAL_ALL_FOUR_STATE_GENERATIONS.md';out.write_text('\n'.join(lines)+'\n');record=dict(actualCompletedUpdates=10000,savedFourStateOutputs=count,uniqueFixedInputs=42,semanticReadingPending=True,noSemanticScoresAssigned=True,noModelOrOptimizerOrGitUsed=True,fullTextSha256=sha(out),codeSha256=sha(pathlib.Path(__file__)),utc=datetime.datetime.now(datetime.timezone.utc).isoformat());flag.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
