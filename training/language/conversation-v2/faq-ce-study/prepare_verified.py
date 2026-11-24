import pathlib,json,hashlib
P=pathlib.Path(__file__).parent;C=P.parent/'faq-ce-clean-study';F=P.parent/'faq-ce-verified-study';F.mkdir(exist_ok=True);d=json.loads((C/'DATA.json').read_text());a=json.loads((P/'ANSWER_BOUNDARY_STRICT_AUDIT.json').read_text());ok=set(a['pass_ids']);old=d['parts']['train'];d['parts']['train']=[r for r in old if r['id']in ok];n=len(d['parts']['train']);d['batch_order']=[list(range(i,min(i+4,n)))for i in range(0,n,4)];d['updates_per_arm']=len(d['batch_order']);d['midpoint']=(d['updates_per_arm']+1)//2;d['stage']='final source-answer-block verified one-pass CE A/B; earlier393 and385 candidates remain archived';(F/'DATA.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
for name in ['DEV_PROTOCOL.json','GROUNDED_DEV.json','RIGHTS.json','ACQUISITION.json','SOURCE_FETCH.json','ASDC-DATA.json','ASDC-DEV_PROTOCOL.json','CLEANING_PROTOCOL.json','QUESTION_BOUNDARY_AUDIT.json','PAIR_ADJACENCY_AUDIT.json']+[x.name for x in C.glob('rights-*')]: (F/name).write_bytes((C/name).read_bytes())
(F/'ANSWER_BOUNDARY_STRICT_AUDIT.json').write_bytes((P/'ANSWER_BOUNDARY_STRICT_AUDIT.json').read_bytes())
plan=dict(reason='Repair source-completeness validator: substring match alone allowed incomplete original question/answer',previous_run_actual_calls=404,previous_retained=392,previous_results_immutable=True,previous_sft_not_used_as_initial=True,rule='TRAIN normalized full Answer must begin at original block boundary (ordinary A/answer markers allowed), end at original block boundary, and have a complete natural ending; conservative holds for lists/links are not all called errors',removed_from385=[dict(id=r['id'],reason='unconfirmed start/end or nonterminal field')for r in old if r['id']not in ok],no_human_text_repair=True,DEV19_unchanged=True,DEV_reference_note='Two references fail conservative formatting gate but were individually read and contain complete required facts; retained as original fixed DEV, not training.17 strict-end DEV subset additionally reported without changing rubric.',grounded4_unchanged=True,performance_not_used_to_select_training=True,no_further_training_beyond_fixed_onepass=True)
(F/'FINAL_ADMISSION.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
s=(C/'engine.py').read_text().replace('scratch-faq-ce-clean','scratch-faq-ce-verified').replace('"""Frozen corrected one-pass government FAQ A/B; N from DATA and PLAN."""','"""Final source-block-verified FAQ A/B; immutable N and masks from PLAN/DATA."""')
s=s.replace(" evaluate(src,'initial',False)"," reuse_initial()")
s=s.replace("for row in data['dev']:\n   prefix", "for row in (data['dev'] if legacy else []):\n   prefix")
s=s.replace("for row in read(P/'GROUNDED_DEV.json')['cases']:","for row in (read(P/'GROUNDED_DEV.json')['cases'] if legacy else []):")
insert='''def reuse_initial():
 old=V/'faq-ce-clean-study';original=read(old/'evaluation/initial.json');assert read(old/'SOURCE_STATE.json')['checkpoint_sha256']==SOURCE
 want={r['id']for part in ['pilot_train','dev']for r in data[part]};refs={r['id']:r for r in original['cases']}
 for row in data['dev']:assert refs[row['id']]['prefix']==row['tokens'][:row['response_body_start']]
 for row in read(P/'GROUNDED_DEV.json')['cases']:assert refs[row['id']]['prefix']==row['prefix']
 obj=copy.deepcopy(original);obj['NLL']=[r for r in original['NLL']if r['id']in want];assert len(obj['NLL'])==len(want)
 obj['reused_initial']=dict(source='PR this study385-run common MIX579 initial',sha256=sha(old/'evaluation/initial.json'),same_initial_model=SOURCE,generated_cases=23,NLL_cases=len(want),avoided_forward_equivalent=sum(len(r['steps'])for r in obj['cases'])+len(want),optimizer_calls=0,model_forwards=0)
 write(P/'evaluation/initial.json',obj)

'''
s=s.replace('def main():',insert+'def main():');(F/'engine.py').write_text(s);compile(s,str(F/'engine.py'),'exec')
s=(C/'verify_inputs.py').read_text().replace('/faq-ce-clean-study/','/faq-ce-verified-study/').replace('range(385)','range('+str(n)+')').replace('),385)', '),'+str(n)+')').replace("self.d['updates_per_arm'],97","self.d['updates_per_arm'],"+str(len(d['batch_order'])))
b=sum(r['body_tokens']for r in d['parts']['train']);total=sum(len(r['tokens'])-1 for r in d['parts']['train']);s=s.replace('for x in r),35948','for x in r),'+str(b)).replace('for x in r),51520','for x in r),'+str(total));(F/'verify_inputs.py').write_text(s)
oldplan=json.loads((C/'PLAN.json').read_text());paths={}
for path,h in oldplan['sha256'].items():
 name=pathlib.Path(path).name
 if '/faq-ce-clean-study/'in path:paths[path.replace('/faq-ce-clean-study/','/faq-ce-verified-study/')]=hashlib.sha256((F/name).read_bytes()).hexdigest()
 else:paths[path]=h
paths['training/language/conversation-v2/faq-ce-verified-study/FINAL_ADMISSION.json']=hashlib.sha256((F/'FINAL_ADMISSION.json').read_bytes()).hexdigest();paths['training/language/conversation-v2/faq-ce-clean-study/evaluation/initial.json']=hashlib.sha256((C/'evaluation/initial.json').read_bytes()).hexdigest()
oldplan.update(stage='final source-block-verified A/B',N=d['updates_per_arm'],midpoint=d['midpoint'],retained_optimizer_calls=2*d['updates_per_arm'],anticipated_total_actual_calls=2*d['updates_per_arm']+6,checkpoint=[d['midpoint'],d['updates_per_arm']],evaluate='initial reused, midpoint NLL only, terminal all fixed greedy and NLL',prior_experiment_actual_calls=404,prior_retained_superseded=392,scope=f'{n} original officialFAQ; {b}reply body tokens; onepass research, not50k achievement',arms={'A':str(total)+' full active teachers','B':str(b+n)+' reply body+EOS teachers'},sha256=paths)
(F/'PLAN.json').write_text(json.dumps(oldplan,ensure_ascii=False,indent=2)+'\n');(F/'PLAN.sha256').write_text(hashlib.sha256((F/'PLAN.json').read_bytes()).hexdigest()+'\n')
print('FINAL',n,'body',b,'A',total,'B',b+n,'N',d['updates_per_arm'],'mid',d['midpoint'],'calls',2*d['updates_per_arm']+6,'plan',hashlib.sha256((F/'PLAN.json').read_bytes()).hexdigest())
