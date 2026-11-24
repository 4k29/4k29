"""Official DEV only; copy evidence, author diagnostic inputs, never generate gold."""
import argparse
import collections
import gzip
import hashlib
import json
import re
from pathlib import Path
from benchmark import HERE, encoder, prepare, validate_case, sha

FIELDS = {'name':'施設名','pricerange':'価格帯','area':'地域','wifi':'Wi-Fi',
          'parking':'駐車場','adultfee':'大人入場料','childfee':'子供入場料'}
CATEGORIES = ['comparison','reason','conditional-request','history-reference','explanation','question-answer']


def field_evidence(turn, key, value):
    return {'kind':'source-field','turn_id':turn['turn_id'],
            'path':['dialogue_state','db_result','active_entity',key],'value':value}


def proposal(row, turn, entity, category):
    keys = ['name']
    constraints = []
    if category == 'comparison':
        a,b=entity.get('adultfee',''),entity.get('childfee','')
        if not(str(a).isdigit() and str(b).isdigit() and int(a)>int(b)>0):return None
        if not(a in turn['utterance'] and b in turn['utterance'] and re.search('子供|子ども|小中学生',turn['utterance'])):return None
        keys += ['adultfee','childfee']
        question='大人と子供の入場料をそれぞれ答え、どちらが安いか比較してください。'
        constraints=['Both source prices, correct adult/child association, and child price is lower; no current-price assertion']
    elif category == 'reason':
        key=next((k for k in ['parking','wifi'] if entity.get(k)=='有り(無料)'),None)
        if not key or '無料' not in turn['utterance']:return None
        keys += [key]
        question=f'「{FIELDS[key]}を無料で使いたい」という希望に、この施設は合いますか。資料中の根拠も説明してください。'
        constraints=[f'Answer supported yes and explain {FIELDS[key]} is available free; do not merely agree']
    elif category == 'conditional-request':
        if any(entity.get(k) not in ['有り(無料)','有り(有料)','無し'] for k in ['parking','wifi']):return None
        keys += ['parking','wifi']
        question='駐車場とWi-Fiが両方無料の場合だけ施設名を答えてください。条件を満たさなければ、満たさない点を説明してください。'
        meets=all(entity[k]=='有り(無料)' for k in ['parking','wifi'])
        constraints=[{'predicate':'both parking and wifi equal source value 有り(無料)', 'source_evaluated_result':meets,
                      'require':'facility name when true; specific failing facility condition(s) when false; acknowledgment fails'}]
    elif category == 'history-reference':
        key=next((k for k in ['area','pricerange'] if isinstance(entity.get(k),str) and entity[k] not in ['', '不明'] and entity[k] in turn['utterance']),None)
        if not key:return None
        keys += [key]
        question=f'この案内を受けて「そこ」と言った場合、どの施設を指しますか。その{FIELDS[key]}も答えてください。'
        constraints=['Resolve deictic reference to supplied facility and preserve requested source property']
    elif category == 'explanation':
        if any(entity.get(k) not in ['有り(無料)','有り(有料)','無し'] for k in ['parking','wifi']):return None
        keys += ['parking','wifi']
        question='この施設の駐車場とWi-Fiについて、利用の有無と料金の違いが分かるように説明してください。'
        constraints=['Both parking and wifi availability/payment must match source; no invented services']
    else:
        key=next((k for k in ['pricerange','area'] if isinstance(entity.get(k),str) and entity[k] not in ['', '不明'] and entity[k] in turn['utterance']),None)
        if not key:return None
        keys += [key]
        question=f'資料の施設名と{FIELDS[key]}を教えてください。'
        constraints=['Provide named entity and requested exact source property; pure greeting or assent fails']
    evidence=[{'kind':'utterance','turn_id':turn['turn_id'],'start':0,
               'end':len(turn['utterance']),'quote':turn['utterance']}]
    evidence.extend(field_evidence(turn,k,entity[k])for k in keys)
    facts='、'.join(FIELDS[k]+':'+str(entity[k])for k in keys)
    prompt='資料（原典収集時点の記録）\n'+facts+'\n案内役の原文：'+turn['utterance']+'\n質問：'+question
    return {'id':'response-grounded-dev-'+row['source_id']+'-'+str(turn['turn_id'])+'-'+category,
            'category':category,'prompt':prompt,
            'input_authorship':'assistant-authored-diagnostic-question-and-wrapper; verbatim-human-source-evidence',
            'gold_authorship':'no-generated-gold-verbatim-source-slots',
            'original_human_response':turn['utterance'],
            'original_human_response_is_context_not_generated_reference':True,
            'source':{'id':'jmultiwoz','split':'DEV','dialogue_id':row['source_id'],
                      'source_object_sha256':row['source_object_sha256'],'turn_id':turn['turn_id'],
                      'license':'CC-BY-SA-4.0','family':row['source_id'],
                      'entity_family':entity['name']},
            'evidence':evidence,
            'required_content':[{'field':k,'source_values':[entity[k]],'evidence_indices':[i+1]} for i,k in enumerate(keys)],
            'semantic_constraints':constraints,
            'generation':{'max_new_tokens':64,'decoding':'greedy-full-vocabulary','eos_id':2,
                          'postprocessing':'none','output':'save full raw text and token ids'},
            'pass_requirements':['all required semantic content and constraints','natural Japanese through full output',
                                 'relevant and coherent throughout','no harmful repetition or topic drift',
                                 'appropriate utterance end'],
            'human_evaluation_required':True,'model_evaluated':False}


def main(path):
    rows=[json.loads(l)for l in gzip.open(path,'rt')]
    assert len(rows)==300 and all(r['official_split']=='dev' for r in rows)
    candidates=[];counts=collections.Counter();rejected=collections.Counter()
    for row in rows:
        for turn in row['data']['turns']:
            if turn['speaker']!='SYSTEM':continue
            entity=turn.get('dialogue_state',{}).get('db_result',{}).get('active_entity')or{}
            if not entity.get('name'):continue
            if re.search(r'電話|住所|番地|丁目|https?://|(?<!\d)\d{9,11}(?!\d)|予約番号|予約を承|ご予約',turn['utterance']):
                rejected['contact-location-or-booking-text-review']+=1;continue
            for category in CATEGORIES:
                case=proposal(row,turn,entity,category)
                if not case:continue
                try:prepare([case])
                except ValueError:rejected[category+'-over-context']+=1;continue
                candidates.append((sha(('response-dev-v1|'+row['source_id']+'|'+str(turn['turn_id'])).encode()),case,row))
    candidates.sort(key=lambda x:(x[0],x[1]['id']))
    selected=[];used=set();excerpts={}
    for category in CATEGORIES:
        for _,case,row in candidates:
            if case['category']!=category or row['source_id']in used:continue
            source=dict(row['data'],split='DEV')
            validate_case(case,source)
            selected.append(case);used.add(row['source_id']);counts[category]+=1
            turn=next(t for t in row['data']['turns']if t['turn_id']==case['source']['turn_id'])
            entity=turn['dialogue_state']['db_result']['active_entity']
            keys=[s['field']for s in case['required_content']]
            excerpts[row['source_id']]={'split':'DEV','dialogue_name':row['source_id'],
                'source_object_sha256':row['source_object_sha256'],
                'turns':[{'turn_id':turn['turn_id'],'speaker':'SYSTEM','utterance':turn['utterance'],
                          'dialogue_state':{'db_result':{'active_entity':{k:entity[k]for k in keys}}}}]}
            if counts[category]==4:break
    assert len(selected)==24, dict(counts)
    data={'suite':'researcher-input-grounded-content-DEV','cases':selected,
          'formal_human_evaluation':False,'speaker_independent':False,
          'new_provider_independent':False,'sealed_test':False,'model_calls':0,'optimizer_updates':0}
    (HERE/'dev.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (HERE/'source-evidence.json').write_text(json.dumps(excerpts,ensure_ascii=False,indent=2)+'\n')
    receipt={'official_dev_dialogues_seen':len(rows),'source_file_sha256':sha(path.read_bytes()),
             'selection_seed':'response-dev-v1','candidates':len(candidates),'rejected':dict(rejected),
             'selected':len(selected),'selected_unique_dialogues':len(used),'categories':dict(counts),
             'human_original_questions':0,'researcher_authored_inputs':len(selected),
             'generated_gold_answers':0,'original_human_response_as_context':len(selected),
             'required_values':'verbatim source fields only; no generated target prose',
             'dev_sha256':sha((HERE/'dev.json').read_bytes()),'source_evidence_sha256':sha((HERE/'source-evidence.json').read_bytes()),
             'must_quarantine_from_new_train':{'dialogue_ids':sorted(used),'entity_families':sorted({c['source']['entity_family']for c in selected})},
             'speaker_independence_achieved':False,'model_calls':0,'optimizer_updates':0}
    (HERE/'build-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('official_dev',type=Path)
    main(p.parse_args().official_dev)
