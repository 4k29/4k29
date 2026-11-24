import pathlib,json,hashlib
P=pathlib.Path(__file__).parent
# A DEV question names no checklist; retain in audit but do not replace with easier samples.
d=json.loads((P/'DATA.json').read_text());d['parts']['dev']=[r for r in d['parts']['dev']if r['index']!=11758];(P/'DATA.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
s=(P/'prior-engine.py').read_text().replace('scratch-public-dialogue','scratch-faq-ce').replace('research/public-dialogue-ce-study','research/faq-response-ce-study')
s=s.replace('pilot-retained','study-retained').replace('PILOT','FAQ').replace('pilot only, not main A/B or generalization proof','one-pass FAQ A/B; no formal deployment or general dialogue claim').replace("main_learning_updates=0","main_learning_updates=2*data['updates_per_arm']")
s=s.replace('if i+1 in [9,17]:',"if i+1 in [data['midpoint'],data['updates_per_arm']]:").replace("i+1==17","i+1==data['updates_per_arm']").replace('if i==8:',"if i+1==data['midpoint']:")
s=s.replace("arm+'-pilot'","arm+'-study'").replace('seventeen-update pilot raw evaluation','one-pass FAQ study raw evaluation')
s=s.replace("actual_optimizer_returns=40,intents=40,retained=34", "actual_optimizer_returns=2*data['updates_per_arm']+6,intents=2*data['updates_per_arm']+6,retained=2*data['updates_per_arm']")
s=s.replace('Complete40 actual optimizer calls and fixed pilot evaluation','Complete fixed one-pass FAQ optimizer ledger and generation evaluation')
s=s.replace("prefix=row['tokens'][:row['response_body_start']];assert len(prefix)+64<=256;result.append(dict(id=row['id'],panel='ASDC-condition-dev15',prefix=prefix,**greedy(m,prefix,pieces,max_new=64)))", "prefix=row['tokens'][:row['response_body_start']];budget=256-len(prefix);result.append(dict(id=row['id'],panel='FAQ-dev',prefix=prefix,**greedy(m,prefix,pieces,max_new=budget)))")
# ASDC remains held-out retention only. Source initial raw is reused from PR114, no initial ASDC forward.
s=s.replace("   old=V/'paragraph-foundation';", "   for row in read(P/'ASDC-DATA.json')['parts']['dev']:\n    prefix=row['tokens'][:row['response_body_start']];result.append(dict(id=row['id'],panel='ASDC-condition-dev15',prefix=prefix,**greedy(m,prefix,pieces,max_new=64)))\n   old=V/'paragraph-foundation';")
# Optional grounded diagnostic, program-constructed prompts using unchanged held-out human facts; not training data.
s=s.replace("  episodes=[]", "  for row in read(P/'GROUNDED_DEV.json')['cases']:\n   prefix=row['prefix'];result.append(dict(id=row['id'],panel='FAQ-grounded-diagnostic',prefix=prefix,**greedy(m,prefix,pieces,max_new=256-len(prefix))))\n  episodes=[]")
(P/'engine.py').write_text(s);compile(s,str(P/'engine.py'),'exec')
print('engine compiled',d['updates_per_arm'],len(d['parts']['dev']))
