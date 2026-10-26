"""Postprocess saved endpoints without inference, selection, or output repair."""
import hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    endpoints=['small','medium','r46']
    allrows={e:read(H/'evaluation'/e/'generations.json') for e in endpoints}
    paired={r['id'] for r in allrows['r46'] if r['generationSupported']}
    annotation={r['id']:r for r in read(H/'benchmark-preoutput-annotations.json')['rows']}
    summaries=[];blind=[];keys=[]
    for e,rows in allrows.items():
        for cohort,subset in [('overall-supported',[r for r in rows if r['generationSupported']]),('paired23',[r for r in rows if r['generationSupported'] and r['id'] in paired])]:
            summaries.append({'endpoint':e,'cohort':cohort,'n':len(subset),'eos':sum(r['eos'] for r in subset),
                'invalidUtf8':sum(not r['strictUtf8'] for r in subset),'nonEosSpecial':sum(r['nonEosContainsSpecialTokens'] for r in subset),
                'mechanicalRepeat4':sum(r['repeated4gram'] is not None for r in subset),
                'meanGeneratedTokens':sum(r['generatedNonEosTokens'] for r in subset)/len(subset),
                'scope':'Mechanical metrics are not whole-meaning or appropriate-response grades'})
        for r in rows:
            if not r['generationSupported']:continue
            ident=hashlib.sha256(('v2-blind-v1|'+e+'|'+r['id']).encode()).hexdigest()[:16]
            a=annotation[r['id']]
            blind.append({'blindId':ident,'prefixText':r['prefixText'],'text':r['text'],'rawBytesHex':r['rawBytesHex'],
                'strictUtf8':r['strictUtf8'],'nonEosContainsSpecialTokens':r['nonEosContainsSpecialTokens'],
                'eos':r['eos'],'stopReason':r['stopReason'],'contentRequired':a['contentRequired'],
                'contentOpportunity':a['contentOpportunity'],'acceptableContentConstraint':a['acceptableContentConstraint'],
                'mode':'human_dialogue_continuation; person A/B, not AI autobiographical facts'})
            keys.append({'blindId':ident,'endpoint':e,'id':r['id'],'paired23':r['id'] in paired})
    blind.sort(key=lambda r:r['blindId'])
    write(H/'evaluation/mechanical-summary.json',summaries)
    write(H/'evaluation/blind-input.json',blind);write(H/'evaluation/blind-key.json',keys)
    write(H/'evaluation/summary.json',{'endpoints':{e:read(H/'evaluation'/e/'summary.json') for e in endpoints},
        'pairedGenerationIds':sorted(paired),'blindOutputs':len(blind),
        'scope':'New-new width comparison only; old reference differs exposure/format/tokenizer. Not an unseen common TEST.'})
    print(json.dumps(summaries,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
