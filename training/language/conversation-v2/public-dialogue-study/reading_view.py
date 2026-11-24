import pathlib,json,re,sys,os
P=pathlib.Path(__file__).parent;V=pathlib.Path(os.environ.get('V2_ROOT',str(P.parent)));pieces=[bytes.fromhex(x)for x in json.loads((V/'data/tokenizer.json').read_text())['bytes']];reference=P/'evaluation/A-pilot17.json'if '--against-A'in sys.argv else (P/'BASELINE-terminal-MIX.json'if (P/'BASELINE-terminal-MIX.json').exists()else V/'mixed-retention-study/evaluation/terminal-MIX.json');base={(r['panel'],r['id']):r for r in json.loads(reference.read_text())['cases']}
def compact(s):
 if s is None:return '[invalid UTF8]'
 # Exact repeated byte-equivalent Unicode spans, display only; raw output unchanged.
 return re.sub(r'(.{1,40}?)\1{2,}',lambda m:'⟪'+m.group(1)+'⟫×'+str(len(m.group(0))//len(m.group(1))),s,flags=re.S)
name=sys.argv[1];group=sys.argv[2];a=json.loads((P/'evaluation'/f'{name}.json').read_text())
for i,r in enumerate(a['cases']):
 if group=='prose'and r['panel']not in ['old24','oldNew9','new-MAFF12','new_source_heldout_paragraph5']:continue
 if group=='dialogue'and r['panel']not in ['native24','provided23']:continue
 b=base.get((r['panel'],r['id']));eq=b is not None and r['tokensIncludingEos']==b['tokensIncludingEos']
 if eq:continue
 print(i,r['panel'],r['id'],'P:',b''.join(pieces[x]for x in r['prefix']).decode('utf8','replace'),'G:',compact(r['text']))
