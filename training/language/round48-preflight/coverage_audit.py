"""Stage1 TRAIN-only scalar coverage and exact private-RNG schedule audit.

No model/optimizer instance, forward/backward pass, or parameter update.
Checkpoint deserialization is only for copying/checking private sampling RNG.
"""
import argparse
import bisect
import collections
import hashlib
import json
import pathlib
import random
import sys
import time
import numpy as np
import torch


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(path.read_text())


def quantiles(values):
    return dict(zip(['min','p25','median','p75','p95','p99','max'],map(float,np.quantile(values,[0,.25,.5,.75,.95,.99,1])))) if values else None


def main(args):
    begun=time.monotonic();root=args.root;out=args.out;prereg_path=out/'PREREGISTRATION.json';prereg=read(prereg_path)
    original_torch_rng=torch.get_rng_state().clone();original_python_rng=random.getstate()
    feature_path=out/'response-turns.json';feature=read(feature_path)
    assert sha(feature_path)=='e73c13d7adeb06253feb5dfa1df74ff9041b8f345b10a9912019a5b050020791'
    for name,key in [('train.index.json','trainIndexSha256'),('train.tokens.bin','trainTokensSha256'),('tokenizer.json','tokenizerSha256')]:assert sha(root/'multiview'/name)==feature[key]
    assert sha(root/'sources/documents.jsonl')==feature['sourceDocumentsSha256']
    index=read(root/'multiview/train.index.json');rows=index['rows'];units={d['id']:d for d in index['documents']};turns=feature['turnsByUnit']
    ends=read(root/'human-turn-token-boundaries.json')['boundariesByUnit'];pieces=[bytes.fromhex(s) for s in read(root/'multiview/tokenizer.json')['bytes']];byte_lengths=np.array([len(b) for b in pieces],dtype=np.int64);tokens=np.memmap(root/'multiview/train.tokens.bin',dtype='<u4',mode='r')
    policy=read(root/'policy.json');views={0:.4,1:.3,2:.3};genres=policy['genreSampling']
    source=lambda r:('jmrd' if r['document'].startswith('jmrd:') else 'realpersona') if r['site']=='human-chat' else r['site']
    source_mass=dict(genres);source_mass.pop('human-chat');source_mass.update(realpersona=.4,jmrd=.05)
    counts=collections.Counter((source(r),r['variant']) for r in rows)
    # TRAIN-only surface expressions, not semantic/generic-response labels.
    documents=[json.loads(s) for s in (root/'sources/documents.jsonl').open()]
    jmrd_sha=sha(args.jmrd_train);assert jmrd_sha==feature['rawJmrdTrainSha256']
    jmrd={d['dialog_id']:d for d in read(args.jmrd_train)};texts={};frequencies=collections.Counter()
    for d in documents:
        assert d['partition']=='train'
        if d['id'].startswith('jmrd:'):
            assert d['sourceSha256']==jmrd_sha and d['upstreamPartition']=='train';ts=[u['text'] for u in jmrd[d['dialogueIdMetadata']]['dialog']]
        else:
            p=args.realpersona_train/pathlib.PurePosixPath(d['sourcePath']).name;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==d['sourceSha256'];ts=[u['text'] for u in json.loads(raw)['utterances']]
        assert '\n'.join(ts)==d['text'] and len(ts)==d['utteranceCount'];texts[d['originalDocument']]=ts;frequencies.update(' '.join(t.split()) for t in ts)
    top20={t for t,n in frequencies.most_common(20)}
    allstats=collections.Counter();groupstats=collections.defaultdict(collections.Counter);sourceview=collections.defaultdict(collections.Counter);expected=collections.Counter();cache=[];weightgroups=collections.defaultdict(list);reply_lengths=[];representatives=collections.defaultdict(list);max_rows={}
    for row_index,r in enumerate(rows):
        s=source(r);group=groupstats[s];sv=sourceview[(s,r['variant'])];group['rows']+=1;sv['rows']+=1
        probability=source_mass[s]*views[r['variant']]/counts[(s,r['variant'])];expected['allSamplerMass']+=probability
        seq=tokens[r['offset']:r['offset']+r['length']];valid=r['length']-r['prefixLength'];protected=sum(int(t) in (1,2) for t in seq[r['prefixLength']:]);active=valid;excluded=set();candidate=None;category='nonhuman';start=r['start'];low=start+r['prefixLength'];high=start+r['length'];first=int(seq[0]);clean=first==1 or first>=6 and bool(pieces[first]) and not 0x80<=pieces[first][0]<0xc0
        if r['site']=='human-chat':
            unit=units[r['unit']];unitseq=tokens[unit['offset']:unit['offset']+unit['length']];bs=ends[r['unit']];excluded={e-1 for e in bs[bisect.bisect_left(bs,low+1):bisect.bisect_right(bs,high)] if int(unitseq[e-1])==16};active-=len(excluded);category='no-eligible';candidates=[]
            if clean:
                ts=turns[r['unit']]
                for j in range(1,len(ts)):
                    _,a,b=ts[j-1];_,c,e=ts[j]
                    if None in (a,b,c,e):continue
                    assert a<b==c<e
                    if start<=a and low<=c and e<=high:
                        n=e-c-sum(c<=x<e for x in excluded)-sum(int(t) in (1,2) for t in unitseq[c:e])
                        if n:candidates.append((j,c,e,n))
            else:category='unclean-character-start'
            if candidates:
                key=f"r48-response-ce-v1|{r['unit']}|{start}|{r['length']}|{r['prefixLength']}".encode();value=int.from_bytes(hashlib.sha256(key).digest(),'big');bound=2**256-(2**256%len(candidates));counter=0
                while value>=bound:counter+=1;value=int.from_bytes(hashlib.sha256(key+f'|{counter}'.encode()).digest(),'big')
                candidate=candidates[value%len(candidates)];category='eligible-with-EOS' if protected else 'eligible'
        content=active-protected
        record=dict(valid=valid,active=active,content=content,protected=protected,excluded=excluded,candidate=candidate,clean=bool(clean),category=category,utf8Bytes=int(byte_lengths[seq[r['prefixLength']:]].sum()))
        for key in ['valid','active','content','protected']:group[key]+=record[key];allstats[key]+=record[key]
        if candidate:
            j,c,e,n=candidate;assert n<=content;changed=content>n;weight=content/n;record.update(changed=changed,weight=weight)
            original_text=texts[units[r['unit']]['sourceDocument']][j];normalized=' '.join(original_text.split());short=len(normalized)<=8;is_top=normalized in top20;record.update(short=short,isTop20=is_top)
            group['eligibleRows']+=1;sv['eligibleRows']+=1;expected['eligibleSamplerMass']+=probability;expected[s+':eligibleSamplerMass']+=probability
            group['eligibleContentMass']+=content;group['eligibleSelectedNonzeroContent']+=n
            if changed:
                group['trulyChangedRows']+=1;sv['trulyChangedRows']+=1;group['changedPositionsAndOldNewMass']+=content;group['changedPositivePositions']+=n;group['zeroedPositions']+=content-n;expected['trulyChangedSamplerMass']+=probability;expected[s+':trulyChangedSamplerMass']+=probability
            else:group['eligibleUnchangedRows']+=1;group['eligibleUnchangedContentMass']+=content
            for name in ['all','shortAtMost8Chars' if short else 'longer']:weightgroups[name].append(weight)
            reply_lengths.append(n)
            width=next(w for w in (64,128,256) if r['length']-1<=w);k=(s,r['variant'])
            if k not in max_rows or weight>max_rows[k]['positionWeight']:max_rows[k]=dict(source=s,view=r['variant'],width=width,anchorRowIndex=row_index,positionWeight=weight)
            expected['eligibleContentMassPerDraw']+=probability*content;expected['eligibleSelectedNonzeroContentPerDraw']+=probability*n;expected['shortSamplerMass']+=probability*short;expected['shortContentMassPerDraw']+=probability*content*short;expected['top20SamplerMass']+=probability*is_top;expected['top20ContentMassPerDraw']+=probability*content*is_top
        elif r['site']=='human-chat':group['fallback:'+category]+=1;sv['fallback:'+category]+=1
        if len(representatives[category])<20:representatives[category].append(row_index)
        cache.append(record)
    # Verify scalar counts and selected position weights against actual prototype
    # on100 real windows, with no logits, model, gradients, or updates.
    sys.path.insert(0,str(out));from response_position_ce import Turn,build_weights
    matched=collections.Counter()
    for category,indices in representatives.items():
        for k in indices:
            r=rows[k];record=cache[k];seq=np.array(tokens[r['offset']:r['offset']+r['length']],dtype=np.int64);y=torch.tensor(seq[1:]).unsqueeze(0);y[:,:r['prefixLength']-1]=-100;endmask=torch.zeros_like(y,dtype=torch.bool)
            for x in record['excluded']:endmask[0,x-r['start']-1]=True
            mapping={r['unit']:[Turn(*t) for t in turns[r['unit']]]} if r['site']=='human-chat' else {}
            w,audit=build_weights([dict(r,cleanCharacterStart=record['clean'])],y,endmask,mapping);expected_weights=(y.ne(-100)&~endmask).double()
            if record['candidate']:
                j,c,e,n=record['candidate'];contentmask=y.ne(-100)&~endmask&~(y.eq(1)|y.eq(2));expected_weights[contentmask]=0
                for x in range(c,e):
                    t=x-r['start']-1
                    if bool(contentmask[0,t]):expected_weights[0,t]=record['content']/n
                assert audit[0]['selectedTurn']==j
            else:assert audit[0]['selectedTurn'] is None
            assert torch.equal(w,expected_weights) and abs(float(w.sum())-record['active'])<1e-8
            matched[category]+=1
    # Same exact original draw implementation, using a private RNG clone only.
    sys.path.insert(0,str(root));from batching import sampler,draw
    saved=torch.load(args.initial_checkpoint,map_location='cpu',weights_only=False);assert saved['step']==0;rng=random.Random();rng.setstate(saved['pythonRng']);del saved
    strata,weights,masses=sampler(rows,genres);by_key={(r['unit'],r['start']):k for k,r in enumerate(rows)};sample=collections.defaultdict(collections.Counter);sample_weights=collections.defaultdict(list);sample_lengths=[]
    for step in range(10000):
        _,batch=draw(rng,8,strata,weights,masses)
        for r in batch:
            s=source(r);g=sample[s];g['draws']+=1;x=cache[by_key[(r['unit'],r['start'])]]
            for name in ['valid','active','content','protected','utf8Bytes']:g[name]+=x[name]
            if x['candidate']:
                j,c,e,n=x['candidate'];m=x['content'];g['eligibleDraws']+=1;g['eligibleOldActive']+=x['active'];g['eligibleContentMass']+=m;g['selectedNonzeroContent']+=n;g['selectedNonzeroIncludingProtected']+=n+x['protected'];g['shortSelectedDraws']+=x['short'];g['shortContentMass']+=m*x['short'];g['top20SelectedDraws']+=x['isTop20'];g['top20ContentMass']+=m*x['isTop20']
                if x['changed']:g['trulyChangedDraws']+=1;g['changedPositionsAndOldNewMass']+=m;g['changedPositivePositions']+=n;g['zeroedPositions']+=m-n
                else:g['eligibleUnchangedDraws']+=1;g['eligibleUnchangedContentMass']+=m
                for name in ['all','shortAtMost8Chars' if x['short'] else 'longer']:sample_weights[name].append(x['weight'])
                sample_lengths.append(n)
            elif r['site']=='human-chat':g['fallback:'+x['category']]+=1
    control=torch.load(args.control_terminal,map_location='cpu',weights_only=False);assert rng.getstate()==control['pythonRng'];del control
    assert torch.equal(original_torch_rng,torch.get_rng_state()) and original_python_rng==random.getstate()
    sample_total=collections.Counter()
    for g in sample.values():sample_total.update(g)
    stress=[]
    for k,entry in sorted(max_rows.items()):
        anchor=entry['anchorRowIndex'];width=entry['width'];selected=[anchor];identities={(rows[anchor]['unit'],rows[anchor]['start'],rows[anchor]['length'],rows[anchor]['prefixLength'])}
        for row_index,r in enumerate(rows):
            identity=(r['unit'],r['start'],r['length'],r['prefixLength'])
            if identity in identities or next(w for w in (64,128,256) if r['length']-1<=w)!=width:continue
            selected.append(row_index);identities.add(identity)
            if len(selected)==8:break
        assert len(selected)==8;stress.append(dict(entry,rowIndices=selected))
    result=dict(schemaVersion=1,scope='All immutable original TRAIN index rows; exact10000 nominal draw schedule only, no training',codeSha256=sha(pathlib.Path(__file__)),prototypeSha256=sha(out/'response_position_ce.py'),preregistrationSha256=sha(prereg_path),responseTurnsSha256=sha(feature_path),dataInputs={name:sha(root/name) for name in ['sources/documents.jsonl','added-human-source/documents.jsonl','multiview/train.index.json','multiview/train.tokens.bin','multiview/tokenizer.json','human-turn-token-boundaries.json','batching.py']},sourceTextChanged=False,featuresByteidenticalToPrevious=True,samplingProbabilitiesChanged=False,semanticFiltering=False,relation='Authentic adjacent other-speaker next utterance; no all-pair semantic reply certification',fullIndex=dict(allRows=len(rows),allTargetTotals=dict(allstats),perSource=dict(groupstats),perSourceView={f'{s}:view{v}':dict(c) for (s,v),c in sorted(sourceview.items())},expectedSampler=dict(expected),positionWeightQuantiles={k:quantiles(v) for k,v in weightgroups.items()},selectedContentLengthQuantiles=quantiles(reply_lengths)),prototypeExactMatchWindows=dict(matched),exactDrawReplay=dict(nominalUpdates=10000,optimizerUpdatesPerformed=0,perSource=dict(sample),totals=dict(sample_total),positionWeightQuantiles={k:quantiles(v) for k,v in sample_weights.items()},selectedContentLengthQuantiles=quantiles(sample_lengths),initialCheckpointSha256=sha(args.initial_checkpoint),initialCheckpointDescription='Own R47 step0 aligned R28 state',controlTerminalSha256=sha(args.control_terminal),controlTerminalDescription='Own R46 terminal step10000',privateRngExactlyMatchesControlTerminal=True,globalTorchAndPythonRngUnchanged=True),surfaceFrequencyBaseline=dict(originalUtterances=sum(frequencies.values()),shortAtMost8Chars=sum(n for t,n in frequencies.items() if len(t)<=8),top20ExactCount=sum(frequencies[t] for t in top20),semanticGenericClassifier=False),stressBatches=stress,stressSelection='Maximum eligible position-weight row per source/view; earliest index breaks ties; first seven distinct same-width other rows in original index order; no model outputs',additionalOptimizerUpdates=0,modelInstantiated=False,optimizerInstantiated=False,gradientComputed=False,heldoutRead=False,elapsedSeconds=time.monotonic()-begun,cautions=['Equal row mass does not imply equal gradient norm or variance','Short selected next turns have high per-position amplification; no new cap/filter introduced','Eligible C=S rows retain exact original weights and are not actual treatment','Full-index quantiles are uniform eligible rows; replay quantiles use fixed original draws'])
    (out/'coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(coverageSha256=sha(out/'coverage.json'),codeSha256=sha(pathlib.Path(__file__)),allRows=len(rows),exactReplayTotals=dict(sample_total),stressBatches=stress,additionalOptimizerUpdates=0,elapsedSeconds=time.monotonic()-begun)))


if __name__=='__main__':
    p=argparse.ArgumentParser();here=pathlib.Path(__file__).resolve().parent
    p.add_argument('--root',type=pathlib.Path,default=here.parent/'round47');p.add_argument('--out',type=pathlib.Path,default=here)
    p.add_argument('--initial-checkpoint',type=pathlib.Path,default=here.parent/'round47/continue-10000/checkpoint-0.pt');p.add_argument('--control-terminal',type=pathlib.Path,default=here.parent/'round46/continue-10000/checkpoint.pt')
    p.add_argument('--realpersona-train',type=pathlib.Path,default=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train'));p.add_argument('--jmrd-train',type=pathlib.Path,default=pathlib.Path('/workspace/next-source-candidate-jmrd/upstream-train.json'))
    main(p.parse_args())
