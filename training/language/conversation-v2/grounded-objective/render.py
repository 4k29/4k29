"""Render unabridged output and serialize previously read unblinded judgments.

The hardcoded success sets are the main assistant's saved reading decisions,
not an automated semantic evaluator. This script never repairs generation.
"""
import json, pathlib
H=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads((H/p).read_text())
def main():
    success={'full512':set(),'response512':{2,3,4,7,9,12,14,15,16,17,18,20,21,23,24,28},'full-extra':{24,28,29},'response-extra':{24,28,29,30,31,33,34}}
    legacy_success={'full512':{4,7,8},'response512':{4,7,17},'full-extra':{10},'response-extra':{7}}
    old23=json.loads((H.parent/'response-data/final/active-dev.json').read_text())['cases'];native=json.loads((H.parent/'epoch1/content-dev.json').read_text())['cases']
    old={c['id']:c for c in old23+native};lines=['# 無修正生成全文','', '原本JSONにtoken列/raw bytes/logit gapを保存。ここでは全文を省略しない。主評価36・TRAIN probe8・旧診断47件/endpoint。生成文は修正していない。', ''];reviews={};legacy_reviews={}
    def show(label,text):
        lines.extend([label,'','```text',text if text is not None else '[strict UTF8 invalid; see rawBytesHex in JSON]','```',''])
    for folder,names in [('evaluation',['initial3470','full32','response32','full512','response512']),('evaluation-extra',['full-extra','response-extra'])]:
        for name in names:
            d=read(folder+'/'+name+'.json');lines.extend(['## '+name,'', '原本: '+folder+'/'+name+'.json',''])
            for i,r in enumerate(d['cases']):
                lines.extend(['### '+r['partition']+' '+str(i)+' '+r['id'],'']);show('入力',r['prompt']);show('プログラム教師（人間原文ではない）',r['program_teacher']);show('モデル出力',r['text'])
                if name in success and r['partition']=='DEV':
                    ok=i in success[name]
                    reason=('入力に必要な '+r['program_teacher']+' の意味内容を短い自然な返答で満たす。独立人間評価ではない。')if ok else {
                      'fee':'入力の子供料金を正しい数値と単位で返していない。0円/利用可否への置換や文法崩壊。',
                      'compare':'同額か、どちらが安いかという入力の比較関係が成立しない。両方が安いという返答は不合格。',
                      'compare-swap':'交換後の仮定料金に対応した比較が成立しない。現実の料金を推測して補っていない。',
                      'condition':'両設備が無料という条件への判定又は理由が欠落/矛盾、又は全文が不自然。',
                      'parking':'駐車場の存在/料金に必要な情報を満たさないか、誤条件/不自然な文を出力。無料でないだけでは有料と不存在を区別できない。',
                      'wifi':'Wi-Fiの存在/料金が誤るか、別の対象への返答又はWi-Fi-Fi等で不自然。'}[r['task']]
                    reviews.setdefault(name,[]).append(dict(index=i,id=r['id'],task=r['task'],success=ok,reason=reason,expected_content=r['program_teacher'],output=r['text']))
            for r in d['legacy']:
                c=old[r['id']];lines.extend(['### '+r['panel']+' '+r['id'],''])
                show('入力',c.get('prompt',c.get('prefixText')));show('モデル出力',r['text'])
            for i,e in enumerate(d['self_history']):
                lines.extend(['### 自己履歴 episode '+str(i)+' 初期case '+e['id'],''])
                for k,t in enumerate(e['turns']):
                    show('turn '+str(k+1)+' 出力',t.get('text','[unsupported full history]'))
                lines.extend(['後続入力: この資料のWi-Fiについても教えてください。 / では駐車場について教えてください。',''])
            if name in legacy_success:
                rs={r['id']:r for r in d['legacy']if r['panel']=='provided23'}
                legacy_reviews[name]=[dict(index=i,id=c['id'],semantic_candidate=i in legacy_success[name],output=rs[c['id']]['text'],
                    reason=('短文でも、指定設備の利用条件又は不成立の理由を示す。'if i in legacy_success[name]else'必要な情報/理由/複数fieldを欠くか誤る。'),formal_human_pass=False)for i,c in enumerate(old23)]
    for name in ['full512','response512','full-extra','response-extra']:
        lines.extend(['## 補助context '+name,''])
        for i,r in enumerate(read('evaluation-extra/'+name+'-context.json')):
            lines.extend(['### case '+str(i),'']);show('入力',r['prompt']);show('モデル出力',r['text'])
    (H/'GENERATIONS.md').write_text('\n'.join(lines).rstrip()+'\n')
    (H/'evaluation/CASE_REVIEWS.json').write_text(json.dumps(dict(reviewer='main assistant, unblinded, no independent native-human evaluation',endpoints=reviews),ensure_ascii=False,indent=2)+'\n')
    (H/'evaluation/LEGACY_REVIEW.json').write_text(json.dumps(dict(scope='exposed supplementary provided23, semantic candidates only; old role-format comparability limitations retained',endpoints=legacy_reviews),ensure_ascii=False,indent=2)+'\n')
    (H/'evaluation-extra/CONTEXT_REVIEW.json').write_text(json.dumps(dict(all48_outputs_read=True,reviewer='main assistant only, not blind/native-human',pair_success={'full512':0,'response512':0,'full-extra':0,'response-extra':3},pairs_each=6,response_extra_success_pair_indices=[3,4,5],not_general_conversation_comprehension=True),indent=2)+'\n')
if __name__=='__main__':main()
