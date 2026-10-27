"""Fixed-checkpoint, zero-update diagnostic generation. No public-code changes."""
import argparse,json,pathlib,sys,time
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parents[1];REPO=HERE.parents[4]
sys.path.insert(0,str(BASE));sys.path.insert(0,str(BASE/'epoch1'))
from benchmark_core import read,sha,prepare_cases,mechanical_summary,check_final_split

def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main(a):
    if sha(a.plan)!=a.plan_sha:raise ValueError('Frozen benchmark plan SHA mismatch')
    plan=read(a.plan)
    for relative,expected in plan['codeAndDataReceipts'].items():
        if sha(REPO/relative)!=expected:raise ValueError('Frozen benchmark dependency differs: '+relative)
    human=read(HERE/'human-dev.json');synthetic=read(HERE/'researcher-input-dev.json');tok=read(BASE/'data/tokenizer.json')
    rows=prepare_cases(human,synthetic,tok)
    if len(rows)!=plan['cases']or [r['id']for r in rows]!=plan['caseIds']:raise ValueError('Fixed case inventory differs')
    if a.prepare_only:
        report=dict(cases=len(rows),supported=sum(r['generationSupported']for r in rows),
            unsupported=[r['id']for r in rows if not r['generationSupported']],
            optimizerUpdates=0,modelCalls=0,sealedTestUsed=False,checkpointLoaded=False,
            planSha256=a.plan_sha,preparedOnly=True)
        print(json.dumps(report));return
    if plan.get('inferenceAuthorized')is not True:raise ValueError('No root-authorized preregistered inference; preparation only')
    # Imports alone do not instantiate any optimizer or outside model.
    import torch
    from core import decoder,digest
    from eval_core import greedy,response_scores,fence
    from eval_chunk_loader import load_chunks
    if a.output is None or a.manifest is None:raise ValueError('New output path and exact checkpoint manifest required')
    out=a.output.resolve()
    if not out.is_relative_to(HERE)or out.exists():raise ValueError('Refuse output overwrite or outside benchmark directory')
    archive=read(a.manifest)
    if archive['sha256']!=plan['checkpointSha256']:raise ValueError('Wrong checkpoint SHA')
    saved=load_chunks(a.manifest);state=saved['trajectory']
    if saved['modelName']!='medium'or state['uniqueUpdates']!=3470:raise ValueError('Fixed medium first-epoch terminal only')
    if state['config']!=plan['modelConfig']:raise ValueError('Wrong own model configuration')
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True);rng=torch.get_rng_state().clone()
    model=decoder(state['config']);model.load_state_dict(state['model'],strict=True);model.eval();torch.set_rng_state(rng)
    initial=digest(model.state_dict());del state,saved
    pieces=[bytes.fromhex(x)for x in tok['bytes']];outputs=[];tf=[];started=time.monotonic();out.mkdir()
    for row in rows:
        if not row['generationSupported']:
            outputs.append(dict(**row,generation=None,unsupportedReason='Full frozen input + generation budget exceeds256; no crop/repair'));continue
        gold=row.get('goldTokens');logits=None
        if gold:
            logits,scores=response_scores(model,row['prefixTokens'],gold,pieces)
            tf.append(dict(id=row['id'],kind=row['kind'],scores=scores,
                extractiveSpanEndEosIsNotSemanticRequirement=row['kind']=='human-grounded-qa',
                referenceNotUnique=True))
        g=greedy(model,row['prefixTokens'],pieces,gold,logits,max_new=row['maxNewTokens'])
        outputs.append(dict(**row,generation=g))
    if initial!=digest(model.state_dict())or not torch.equal(rng,torch.get_rng_state()):raise AssertionError('Read-only inference changed model/RNG')
    summaries={}
    for kind in sorted({r['kind']for r in outputs}):summaries[kind]=mechanical_summary([r for r in outputs if r['kind']==kind])
    write(out/'generations.json',outputs);write(out/'teacher-forced.json',tf);write(out/'mechanical-summary.json',summaries)
    md=['# Full unmodified diagnostic outputs','New QA/researcher prompt serialization is not a validated learned AI-role contract.']
    for row in outputs:
        text=row.get('inputText')or'\n'.join(row['history']);md+=['','## '+row['id'],fence(text)]
        if row['generationSupported']:
            g=row['generation'];md+=[fence(g['text']if g['strictUtf8']else g['rawBytesHex']),fence(json.dumps(g['tokensIncludingEos']))]
        else:md.append('UNSUPPORTED: full input + fixed generation budget exceeds context; no crop.')
    (out/'ALL_GENERATIONS.md').write_text('\n'.join(md)+'\n')
    receipt=dict(status='complete-unscored-diagnostic',cases=len(rows),generated=sum(r['generationSupported']for r in rows),
        humanQaCases=len(human['cases']),humanProseCases=len(human['proseCases']),researcherInputOnlyCases=len(synthetic['cases']),
        elapsedSeconds=time.monotonic()-started,checkpointSha256=archive['sha256'],planSha256=a.plan_sha,
        modelAndRngUnchanged=True,optimizerUpdates=0,sealedTestUsed=False,formalAdoption=False,
        semanticSuccess=None,fullIndependentSemanticReadingRequired=True)
    write(out/'receipt.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha',required=True)
    p.add_argument('--prepare-only',action='store_true');p.add_argument('--manifest',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path);main(p.parse_args())
