"""Prepare a real length-matched data-only schedule; no model construction.

True prose document endings and RP partial windows are retained. No new role,
EOS, objective mask, optimizer update or model generation is introduced.
"""
import argparse,array,collections,gzip,hashlib,json,pathlib,sys,time
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parents[1];REPO=HERE.parents[4]
sys.path.insert(0,str(BASE))
from core import open_tokens
from new_tokenizer import Encoder
def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def rank(scope,ident):return hashlib.sha256(('foundation-matched-length-v1|'+scope+'|'+ident).encode()).hexdigest()
def dose(sequence):
    targets=sequence[1:]
    return dict(targets=len(targets),body=sum(t>=6 for t in targets),eos=targets.count(2),role=sum(t in(3,4)for t in targets),other=targets.count(1))
def add(a,b):
    for k,v in b.items():a[k]+=v
def main(a):
    if a.output.exists():raise ValueError('Refuse schedule overwrite')
    a.output.mkdir(parents=True)
    start=time.monotonic();data_path=BASE/'data/data.json';data=read(data_path)
    values,rp_windows=open_tokens(data,'train');tok_path=BASE/'data/tokenizer.json';tok=read(tok_path);encoder=Encoder(tok)
    if sha(tok_path)!=data['tokenizerSha256']:raise ValueError('Wrong frozen own tokenizer')
    if any(b'\n'in bytes.fromhex(tok['bytes'][r[2]])for r in tok['merges'][tok['glyphRules']:]):
        raise ValueError('Unexpected newline-containing learned word piece: native paragraph join needs re-audit')
    pieces=[bytes.fromhex(x)for x in tok['bytes']];docs={};pool=[];source_pool=collections.Counter();source_ends=collections.Counter();empty_train_docs=0
    with gzip.open(a.documents,'rt',encoding='utf8')as f:
        for line in f:
            d=json.loads(line)
            if d['split']!='train':continue
            paragraphs=[p['normalizedText']for p in d['paragraphs']if p['keepForCandidateTraining']]
            if not paragraphs:empty_train_docs+=1;continue
            text='\n\n'.join(paragraphs);ids=encoder(text)
            if b''.join(pieces[t]for t in ids)!=text.encode():raise ValueError('Native source byte roundtrip failed')
            if any(t<6 for t in ids):raise ValueError('Tokenizer manufactured a special ID')
            seq=array.array('I',[1]+ids+[2])
            if seq.itemsize!=4:raise ValueError('Expected4byte token storage')
            if d['id']in docs:raise ValueError('Duplicate native document ID')
            docs[d['id']]=dict(id=d['id'],source=d['source'],family=d['family'],component=d['component'],
                url=d['url'],revision=d['revision'],license=d['license'],humanStatus=d['humanStatus'],admission=d['admission'],
                normalizedArticleBodySha256=hashlib.sha256(text.encode()).hexdigest(),tokens=seq)
            for offset in range(0,len(seq)-1,256):
                length=min(257,len(seq)-offset);n=length-1;ident=d['id']+'@'+str(offset)
                end=offset+length==len(seq);source_pool[d['source']]+=1;source_ends[d['source']]+=end
                pool.append(dict(id=ident,documentId=d['id'],source=d['source'],offset=offset,length=length,targetLength=n,trueDocumentEnd=end,rank=rank('native',ident)))
    buckets=collections.defaultdict(list)
    for i,w in enumerate(rp_windows):buckets[w['length']-1].append(i)
    for n in buckets:buckets[n].sort(key=lambda i:rank('rp-match',str(i)),reverse=True)
    selected=[];matched=[];skipped=collections.Counter();used_rp=set()
    for window in sorted(pool,key=lambda w:w['rank']):
        n=window['targetLength']
        if not buckets[n]:skipped[n]+=1;continue
        rp_index=buckets[n].pop();selected.append(window);matched.append(rp_index);used_rp.add(rp_index)
        if len(selected)==4096:break
    if len(selected)!=4096:raise ValueError('No feasible4096distinct native/RP length pairs; do not fill with repetitions')
    if len({w['id']for w in selected})!=4096:raise AssertionError('Duplicate native selected window')
    common=sorted([i for i in range(len(rp_windows))if i not in used_rp],key=lambda i:rank('rp-common',str(i)))[:4096]
    if len(common)!=4096:raise ValueError('Insufficient nonoverlapping shared RP windows')
    rp_intervals=sorted((rp_windows[i]['offset']+1,rp_windows[i]['offset']+rp_windows[i]['length'])for i in common+matched)
    if any(b[0]<a[1]for a,b in zip(rp_intervals,rp_intervals[1:])):raise AssertionError('Control RP target positions overlap')
    native_intervals=collections.defaultdict(list)
    for w in selected:native_intervals[w['documentId']].append((w['offset']+1,w['offset']+w['length']))
    for intervals in native_intervals.values():
        intervals.sort()
        if any(b[0]<a[1]for a,b in zip(intervals,intervals[1:])):raise AssertionError('Native target positions overlap')
    chosen_ends=collections.Counter(w['source']for w in selected if w['trueDocumentEnd'])
    if sum(chosen_ends.values())<32 or any(chosen_ends[s]<1 for s in source_pool):raise ValueError('Predeclared native ending coverage guard failed; no source may lose all endings')
    control=collections.Counter();treatment=collections.Counter();source_dose=collections.defaultdict(collections.Counter)
    native_index=[];binary=a.output/'native-selected-windows.u32';total_ints=0
    with binary.open('wb')as f:
        for w in selected:
            d=docs[w['documentId']];seq=d['tokens'][w['offset']:w['offset']+w['length']]
            if w['trueDocumentEnd']!=(seq[-1]==2):raise AssertionError('True source ending changed')
            if 2 in seq and not w['trueDocumentEnd']:raise AssertionError('Fake native EOS')
            stored=array.array('I',seq)
            if sys.byteorder!='little':stored.byteswap()
            f.write(stored.tobytes());row={k:v for k,v in w.items()if k!='rank'}
            row.update(tokenFileOffset=total_ints,documentTokenCount=len(d['tokens']),family=d['family'],component=d['component'],url=d['url'],revision=d['revision'],license=d['license'],humanStatus=d['humanStatus'],admission=d['admission'],
                partition='train',normalizedArticleBodySha256=d['normalizedArticleBodySha256'],normalizedArticleBodyShaMeaning='UTF8 normalized kept paragraphs joined by exactly two LF; this is a derived article body, not a raw-source hash')
            native_index.append(row);total_ints+=len(seq);add(source_dose[w['source']],dose(seq))
    schedule=a.output/'schedule.jsonl.gz';step_targets=[]
    with schedule.open('wb')as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0)as compressed:
            for step in range(2048):
                shared=common[2*step:2*step+2];replacement=matched[2*step:2*step+2];native_positions=[2*step,2*step+1]
                c=collections.Counter();t=collections.Counter()
                for i in shared:
                    w=rp_windows[i];v=np.asarray(values[w['offset']:w['offset']+w['length']],dtype=np.int64).tolist();add(c,dose(v));add(t,dose(v))
                for i,j in zip(replacement,native_positions):
                    w=rp_windows[i];v=np.asarray(values[w['offset']:w['offset']+w['length']],dtype=np.int64).tolist();native=selected[j];d=docs[native['documentId']];nv=d['tokens'][native['offset']:native['offset']+native['length']].tolist()
                    if len(v)!=len(nv):raise AssertionError('Paired active-length mismatch')
                    add(c,dose(v));add(t,dose(nv))
                if c['targets']!=t['targets']:raise AssertionError('Per-step genuine target count mismatch')
                add(control,c);add(treatment,t);step_targets.append(c['targets'])
                row=dict(step=step+1,sharedRpWindowIndices=shared,controlReplacementRpWindowIndices=replacement,
                    treatmentNativeWindowPositions=native_positions,activeTargetCountBoth=c['targets'],paddedTensorShape=[4,256],
                    activeTargetLengths=[rp_windows[i]['length']-1 for i in shared+replacement],controlDose=dict(c),treatmentDose=dict(t))
                compressed.write((json.dumps(row,separators=(',',':'))+'\n').encode())
    source_selected=collections.Counter(w['source']for w in selected)
    report=dict(status='FEASIBLE_MATCHED_LENGTH_SCHEDULE_CANDIDATE_ONLY_NOT_AUTHORIZED',modelObjectsCreated=0,optimizerUpdates=0,
        sourceDocumentsPath=str(a.documents),sourceDocumentsSha256=sha(a.documents),finalSplitManifestSha256=sha(a.split_manifest),
        ownTokenizerSha256=sha(tok_path),rpDataManifestSha256=sha(data_path),rpTokensSha256=data['trainTokensSha256'],
        fixedOrderRule='SHA256(foundation-matched-length-v1|scope|ID); native first4096 with RP target-length availability; sharedRP first4096 unused windows',
        retainedUpdatesPerArm=2048,paddedBatchShape=[4,256],commonRpWindows=4096,controlReplacementRpWindows=4096,
        nativeDistinctWindows=4096,nativeDistinctDocuments=len({w['documentId']for w in selected}),
        nativePoolWindows=len(pool),nativePoolBySource=dict(source_pool),nativePoolTrueEnds=dict(source_ends),
        nativeNonemptyTrainDocuments=len(docs),emptyAfterDedupTrainDocumentsSkipped=empty_train_docs,
        nativeJoinedBodyTokens=sum(len(d['tokens'])-2 for d in docs.values()),
        nativePoolGenuineTargets=sum(w['targetLength']for w in pool),
        selectedNativeBySource=dict(source_selected),selectedNativeTrueEnds=dict(chosen_ends),selectedNativeTrueEndsTotal=sum(chosen_ends.values()),
        endingCoverageGuard=dict(minTotalTrueEnds=32,minPerSource=1,passed=True),
        controlDose=dict(control),treatmentDose=dict(treatment),sourceNativeDose={s:dict(v)for s,v in source_dose.items()},
        allTargetBudgetExactlyEqual=True,bodyEosRoleDoseNotClaimedEqual=True,
        minimumActiveTargetsPerStep=min(step_targets),maximumActiveTargetsPerStep=max(step_targets),
        paddingTargetPositionsIgnoredPerArm=2048*4*256-control['targets'],
        allControlWindowIdsDistinct=len(set(common+matched))==8192,
        sharedRpAndReplacementDisjoint=not(set(common)&set(matched)),nativeWindowsNoReplacement=True,
        retainedTargetPositionOverlapWithinSource=0,
        overlapAudit='Original stride256 windows have disjoint target intervals; repeated single input/context boundary is not an extra target. Does not establish semantic raw-text uniqueness.',
        unmatchedNativeCandidatesSkippedByLength=dict(skipped),
        selectionBias='Length availability matching can alter native-source/length frequencies; selected source/length distributions and true endings are reported. Common RP selected only after replacement matching.',
        trueEosNotInsertedOrMasked=True,allSelectedNativePartitions='train',allNativeSourceAdmission='candidate-not-admitted',
        scheduleSha256=sha(schedule),nativeWindowBinarySha256=sha(binary),nativeWindowBinaryU32Count=total_ints,
        elapsedSeconds=time.monotonic()-start,trainingAuthorized=False,learningGo=False,sealedTestRead=False,
        noSealedTestClaim='Pipeline-visible reserve is not independent sealedTEST; no reserved payload used in schedule')
    (a.output/'native-window-index.json').write_text(json.dumps(native_index,ensure_ascii=False,indent=2)+'\n')
    (a.output/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--documents',type=pathlib.Path,required=True);p.add_argument('--split-manifest',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);main(p.parse_args())
