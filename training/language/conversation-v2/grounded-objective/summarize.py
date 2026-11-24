"""Aggregate stored evidence without treating automatic matches as language success."""
import collections, hashlib, importlib.util, json, math, pathlib, platform
H = pathlib.Path(__file__).resolve().parent
def read(p): return json.loads((H / p).read_text())
def stats(xs):
    ys = sorted(xs)
    return dict(count=len(ys), min=min(ys), mean=sum(ys)/len(ys), p50=ys[len(ys)//2], p95=ys[int(.95*(len(ys)-1))], max=max(ys))
def main():
    d=read('data.json'); extra=read('contrast-data.json'); primary=d['train'][:2048]
    assert len({r['id'] for r in primary+extra})==2432
    assert not {r['entity'] for r in primary}&{r['entity'] for r in extra}
    assert not {r['entity'] for r in primary+extra}&{r['entity'] for r in d['dev']}
    spec=importlib.util.spec_from_file_location('own_encoder',H.parent/'new_tokenizer.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    enc=module.Encoder(json.loads((H.parent/'data/tokenizer.json').read_text()))
    facts={r['entity']:r['provenance']['facts'] for r in primary}
    summary={'new_human_authored_prose_tokens':0,'program_case_counts':{'initial':2048,'contrast':384},
      'independent_source_entities_initial':len(facts),'new_entities_contrast':len({r['entity']for r in extra}),
      'facts_only_BPE_tokens_once_per_initial_entity':sum(len(enc(json.dumps(f,ensure_ascii=False,sort_keys=True)))for f in facts.values()),
      'facts_token_count_is_not_independent_natural_prose':True,'train_case_repetition_excluding_discarded_replay':0,
      'arms':{},'generation_files':{}}
    total_completed=total_replay=0
    for name in ['updates.jsonl','contrast-updates.jsonl']:
        events=[json.loads(l) for l in (H/'run'/name).read_text().splitlines()]
        intents=[(r['arm'],r['step'],bool(r.get('replay')))for r in events if r['event']=='intent']
        completed=[(r['arm'],r['step'],bool(r.get('replay')))for r in events if r['event']=='completed']
        assert collections.Counter(intents)==collections.Counter(completed)
        total_completed+=len(completed);total_replay+=sum(r[2]for r in completed)
    summary['optimizer_calls']=dict(actual=total_completed,retained=total_completed-total_replay,replay=total_replay,invalid_updates=0,setup_failures_before_any_update=1)
    assert summary['optimizer_calls']['actual']==1248 and total_replay==32
    for arm in ['full','response']:
        rows=read('run/'+arm+'-512-trace.json'); later=read('run/'+arm+'-extra-trace.json')
        assert len(rows)==512 and len(later)==96
        summary['arms'][arm]={}
        for stage,trace in [('primary512',rows),('contrast96',later)]:
            assert all(math.isfinite(r['loss'])and math.isfinite(r['gradient_norm'])for r in trace)
            summary['arms'][arm][stage]=dict(updates=len(trace),loss=stats([r['loss']for r in trace]),
                gradient_norm_before_clip=stats([r['gradient_norm']for r in trace]),
                clipping_count=sum(r['gradient_norm']>1 for r in trace),
                presented_targets=sum(r['presented_targets']for r in trace),
                supervised_targets=sum(r['supervised_targets']for r in trace),
                supervised_response_targets=sum(r['response_targets_including_EOS']for r in trace),
                padded_forward_token_slots=len(trace)*4*256)
    a,b=summary['arms'].values()
    assert all(a[k]['presented_targets']==b[k]['presented_targets']for k in a)
    for folder,names in [('evaluation',['initial3470','full32','response32','full512','response512']),('evaluation-extra',['full-extra','response-extra'])]:
        for name in names:
            output=read(folder+'/'+name+'.json'); rows=output['cases']+output['legacy']
            summary['generation_files'][name]=dict(single_prompts=len(rows),self_history_episodes=len(output['self_history']),
                self_history_generated_turns=sum('tokensIncludingEos'in t for e in output['self_history']for t in e['turns']),
                single_greedy_tokens=sum(len(r['tokensIncludingEos'])for r in rows))
    import torch, numpy
    summary['runtime']=dict(python=platform.python_version(),torch=torch.__version__,numpy=numpy.__version__,device='CPU FP32',gpu_used=False,threads=2,host_platform=platform.platform())
    (H/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items()if k not in ['generation_files','arms']},ensure_ascii=False))
if __name__=='__main__':main()
