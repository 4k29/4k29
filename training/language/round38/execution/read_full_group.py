"""Display actual saved full generated prefixes/text; no truncation, scores or model calls."""
import pathlib,json,sys,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';state,group=sys.argv[1:3];paths={'original17':'new-validation.json','daily12':'daily-new-python.json','native8':'content-native-dev/new-python.json','mrmp5':'fixed-source-mrmp-dev/new-python.json'};assert state in ['selected','terminal']and group in paths
r=json.loads((R/'continue-10000/result.json').read_text());assert r['completedRun']and r['completedSteps']==10000
p=E/paths[group]if state=='selected'else E/'terminal-state-diagnostic'/f'{group}-python.json'
if state=='terminal':
 flag=E/'terminal-state-diagnostic/mechanical-complete.json'
 if flag.exists()and json.loads(flag.read_text()).get('terminalAndSelectedWeightsExactlyEqual'):p=E/paths[group]
d=json.loads(p.read_text());expected={'original17':17,'daily12':12,'native8':8,'mrmp5':5}[group];assert len(d['rows'])==expected
print('STATE',state,'GROUP',group,'GENERATION SHA',hashlib.sha256(p.read_bytes()).hexdigest(),'ACTUAL TRAIN UPDATES',r['completedSteps'],'SELECTED STEP',r['bestStep'])
start=int(sys.argv[3])if len(sys.argv)>3 else 0;stop=int(sys.argv[4])if len(sys.argv)>4 else len(d['rows']);assert 0<=start<stop<=expected
for i in range(start,stop):
 row=d['rows'][i]
 print('\nINDEX',i,'ID',row['id'],'EOS',row['eos'],'NEW TOKENS',len(row['tokens']),'VALID',row['validTokens'],row['validUtf8'])
 print('FULL PREFIX:\n'+row['prefix']);print('FULL GENERATED TEXT:\n'+row['text']);print('\nEND GENERATED TEXT')
