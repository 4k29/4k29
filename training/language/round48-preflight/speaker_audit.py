"""Stage1 only: verify authentic TRAIN speakers, spans and fixed semantic sample.

Never imports the model/trainer, reads heldout text, changes examples, or trains.
Speaker alternation establishes adjacent other-speaker turns, not semantic reply-to.
"""
import argparse
import collections
import datetime
import hashlib
import heapq
import json
import pathlib
import shutil
import time

import numpy as np


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def main(args):
    begun=time.monotonic();out=args.out;out.mkdir(parents=True,exist_ok=True)
    prereg=read(out/'PREREGISTRATION.json');criteria=prereg['speakerCriteria']
    assert criteria['semanticSampleSalt']=='r48-reply-semantic-audit-v1'
    assert criteria['semanticSamplePairsPerSource']==12
    assert criteria['minimumClearlyConnectedPairsPerSource']==10
    feature_source=args.feature;feature=read(feature_source)
    assert feature['partition']=='TRAIN ONLY'
    assert sha(feature_source)=='e73c13d7adeb06253feb5dfa1df74ff9041b8f345b10a9912019a5b050020791'
    root=args.root;index_path=root/'multiview/train.index.json';token_path=root/'multiview/train.tokens.bin';tokenizer_path=root/'multiview/tokenizer.json';docs_path=root/'sources/documents.jsonl';added_docs=root/'added-human-source/documents.jsonl'
    for path,key in [(index_path,'trainIndexSha256'),(token_path,'trainTokensSha256'),(tokenizer_path,'tokenizerSha256'),(docs_path,'sourceDocumentsSha256'),(added_docs,'addedSourceDocumentsSha256')]:
        assert sha(path)==feature[key],key
    index=read(index_path);tokens=np.memmap(token_path,dtype='<u4',mode='r')
    pieces=[bytes.fromhex(s) for s in read(tokenizer_path)['bytes']]
    lengths=np.array([len(s) for s in pieces],dtype=np.int64)
    docs=[json.loads(line) for line in docs_path.open()]
    assert len({d['originalDocument'] for d in docs})==len(docs)
    raw_jmrd_sha=sha(args.jmrd_train)
    assert raw_jmrd_sha==feature['rawJmrdTrainSha256']
    jmrd={d['dialog_id']:d for d in read(args.jmrd_train)}
    stats=collections.defaultdict(collections.Counter)
    keys=collections.defaultdict(collections.Counter)
    licenses=collections.defaultdict(collections.Counter)
    originals={};receipts=[];pair_ranks=collections.defaultdict(list)
    salt=criteria['semanticSampleSalt']
    for d in docs:
        assert d['partition']=='train' and d['site']=='human-chat'
        source='jmrd' if d['id'].startswith('jmrd:') else 'realpersona'
        g=stats[source];g['documents']+=1;licenses[source][d['license']]+=1
        if source=='jmrd':
            assert d['upstreamPartition']=='train' and d['sourceSha256']==raw_jmrd_sha
            raw=jmrd[d['dialogueIdMetadata']];utterances=raw['dialog'];speaker_key='speaker';allowed={'recommender','seeker'}
            g['firstSpeakerMatchesFirstUtterance']+=bool(utterances and raw['first_speaker']==utterances[0].get(speaker_key))
        else:
            raw_path=args.realpersona_train/pathlib.PurePosixPath(d['sourcePath']).name
            payload=raw_path.read_bytes();assert hashlib.sha256(payload).hexdigest()==d['sourceSha256']
            raw=json.loads(payload);utterances=raw['utterances'];speaker_key='interlocutor_id';allowed=set(raw['interlocutors'])
            g['declaredTwoDistinctParticipants']+=len(allowed)==2
        texts=[u['text'] for u in utterances]
        assert '\n'.join(texts)==d['text'] and len(texts)==d['utteranceCount']
        assert hashlib.sha256(d['text'].encode()).hexdigest()==d['textSha256']
        receipts.append((d['originalDocument'],d['sourceSha256']))
        speakers=[];ids=[];times=[]
        for key in raw:keys[source+':top'][key]+=1
        for j,u in enumerate(utterances):
            for key in u:keys[source+':utterance'][key]+=1
            g['utterances']+=1;speaker=u.get(speaker_key);speakers.append(speaker);ids.append(u['utterance_id'])
            g['missingSpeaker']+=speaker is None;g['speakerOutsideDeclaredSet']+=speaker not in allowed;g['emptyText']+=not bool(u['text'])
            expected_id=j if source=='realpersona' else f"{d['dialogueIdMetadata']}_{j:02d}"
            g['idEqualsOriginalOrdinal']+=u['utterance_id']==expected_id
            if source=='realpersona':
                try:parsed=datetime.datetime.fromisoformat(u['timestamp'])
                except (ValueError,TypeError):
                    parsed=None;g['invalidTimestampUtterances']+=1;g['NaTTimestampUtterances']+=u['timestamp']=='NaT'
                times.append(parsed)
            if j:
                g['adjacentPairs']+=1;g['sameSpeakerPairs']+=speaker==speakers[j-1];g['differentSpeakerPairs']+=speaker!=speakers[j-1]
                rank_key=f"{salt}|{d['originalDocument']}|{j-1}|{j}"
                digest=hashlib.sha256(rank_key.encode('utf-8')).hexdigest()
                pair_ranks[source].append((digest,d['originalDocument'],j,rank_key))
        g['documentsWithUniqueUtteranceIds']+=len(ids)==len(set(ids))
        g['documentsWithExactlyTwoObservedSpeakers']+=len(set(speakers))==2
        for a,b in zip(times,times[1:]):
            if a is not None and b is not None:
                g['bothParsedTimestampPairs']+=1;g['decreasingParsedPairs']+=b<a;g['equalParsedPairs']+=b==a
            else:g['pairsWithInvalidTimestamp']+=1
        originals[d['originalDocument']]=dict(source=source,metadata=d,texts=texts,speakers=speakers,ids=ids)

    # Independent all-unit source-byte/span validation. Do not use the old
    # aligned-only map to infer authentic adjacency.
    unit_info={d['id']:d for d in index['documents']}
    span_stats=collections.defaultdict(collections.Counter)
    assert set(feature['turnsByUnit'])=={d['id'] for d in index['documents'] if d['site']=='human-chat'}
    for name,turns in feature['turnsByUnit'].items():
        u=unit_info[name];original=originals[u['sourceDocument']];ts=original['texts'];sp=original['speakers'];g=span_stats[original['source']]
        seq=tokens[u['offset']:u['offset']+u['length']];assert int(seq[0])==1 and int(seq[-1])==2
        payload='\n'.join(ts).encode();assert b''.join(pieces[int(t)] for t in seq)==payload
        cumulative=np.r_[0,np.cumsum(lengths[seq])];offset=0
        assert len(turns)==len(ts)
        for j,(ordinal,a,b) in enumerate(turns):
            assert ordinal==j;startbyte=offset;offset+=len(ts[j].encode())+(j<len(ts)-1)
            for coordinate,byte in [(a,startbyte),(b,offset)]:
                if coordinate is None:assert not bool(np.any(cumulative==byte))
                else:assert int(cumulative[coordinate])==byte
            if j==0:assert a==1
            if j==len(ts)-1:assert b==len(seq)-1
            g['authenticTurnSpans']+=1
            if j:
                g['adjacentPairsAcrossViews']+=1
                aligned=None not in (turns[j-1][1],turns[j-1][2],a,b)
                if aligned:
                    g['bothCompleteTokenAligned']+=1
                    g['alignedDifferentSpeaker']+=sp[j]!=sp[j-1]
                    g['alignedSameSpeaker']+=sp[j]==sp[j-1]
        assert offset==len(payload)
        g['tokenUnits']+=1

    # Reproduce original proposed candidate coverage; no speaker filter can
    # alter it when every adjacent original pair already alternates speakers.
    old_ends=read(root/'human-turn-token-boundaries.json')['boundariesByUnit']
    row_stats=collections.defaultdict(collections.Counter)
    for r in index['rows']:
        if r['site']!='human-chat':continue
        u=unit_info[r['unit']];o=originals[u['sourceDocument']];g=row_stats[f"{o['source']}:view{r['variant']}"];g['rows']+=1
        seq=tokens[u['offset']:u['offset']+u['length']];first=int(seq[r['start']]);clean=first==1 or first>=6 and bool(pieces[first]) and not 0x80<=pieces[first][0]<0xc0
        start=r['start'];low=start+r['prefixLength'];high=start+r['length'];eligible=0
        if clean:
            turns=feature['turnsByUnit'][r['unit']]
            for j in range(1,len(turns)):
                _,a,b=turns[j-1];_,c,e=turns[j]
                if None in (a,b,c,e):continue
                if not start<=a<b==c<e<=high or c<low:continue
                # Preserve prior newline exclusions and original BOS/EOS.
                removed=sum(c<=end-1<e and int(seq[end-1])==16 for end in old_ends[r['unit']])
                protected=sum(int(t) in (1,2) for t in seq[c:e])
                if e-c-removed-protected<=0:continue
                eligible+=1;g['eligibleCandidatePairs']+=1;g['eligibleOtherSpeakerCandidatePairs']+=o['speakers'][j]!=o['speakers'][j-1]
        g['eligibleRows']+=eligible>0

    samples=[]
    for source in ['realpersona','jmrd']:
        selected=heapq.nsmallest(criteria['semanticSamplePairsPerSource'],pair_ranks[source])
        assert len(selected)==12
        for rank,(digest,source_id,j,key) in enumerate(selected,1):
            o=originals[source_id];d=o['metadata']
            full=lambda k:dict(ordinal=k,utteranceId=o['ids'][k],speakerId=o['speakers'][k],text=o['texts'][k])
            samples.append(dict(source=source,rankWithinSource=rank,rankSha256=digest,rankKey=key,document=source_id,sourceSha256=d['sourceSha256'],sourceTextSha256=d['textSha256'],license=d['license'],attribution=d['attribution'],sourceUrl=d['url'],context=[full(k) for k in range(max(0,j-2),j)],previous=full(j-1),next=full(j),differentDeclaredSpeaker=o['speakers'][j]!=o['speakers'][j-1],relation='adjacent_other_speaker_turn',explicitReplyTo=False,semanticReplyVerified=False,manualJudgment=None))
    sample=dict(schemaVersion=1,scope='TRAIN ONLY; fixed original adjacent-pair sample, no model outputs',preregistrationSha256=sha(out/'PREREGISTRATION.json'),codeSha256=sha(pathlib.Path(__file__)),salt=salt,rankKeyFormat="UTF8 f'{salt}|{sourceDocument}|{previousOrdinal}|{nextOrdinal}', ascending SHA256; tie document/nextOrdinal",selectionUniverse={s:len(rs) for s,rs in pair_ranks.items()},contextConvention='At target j, full unchanged original utterances[max(0,j-2):j], including immediately preceding j-1; target j separate',pairsPerSource=12,minimumClearlyConnectedPerSource=10,ambiguousCountsAsNotEstablished=True,semanticReviewPending=True,semanticScoresGuessed=False,noSemanticTrainingFilter=True,rows=samples)
    write(out/'semantic-sample.json',sample)
    destination=out/'response-turns.json'
    if destination.exists():assert sha(destination)==sha(feature_source)
    else:shutil.copyfile(feature_source,destination)
    observed_reply_fields=[]
    for location,keycounts in keys.items():
        for key in keycounts:
            if any(marker in key.lower().replace('_','') for marker in ['replyto','inreply','parentmessage','parentid','referencedmessage']):observed_reply_fields.append((location,key))
    speaker_pass=all(g['missingSpeaker']==g['speakerOutsideDeclaredSet']==g['sameSpeakerPairs']==g['emptyText']==0 and g['idEqualsOriginalOrdinal']==g['utterances'] for g in stats.values())
    combined_manifest=read(root/'sources/manifest.json')
    rp_manifest=combined_manifest['existingRealPersonaManifest'];jmrd_manifest=read(root/'added-human-source/manifest.json')
    source_provenance={
        'realpersona':dict(repository=rp_manifest['sourceRepository'],commit=rp_manifest['sourceCommit'],license=rp_manifest['license'],attribution=rp_manifest['attribution'],url=f"https://github.com/{rp_manifest['sourceRepository']}/tree/{rp_manifest['sourceCommit']}",licenseUrl='https://creativecommons.org/licenses/by-sa/4.0/',split='Existing admitted RealPersona TRAIN fold; original split preserved'),
        'jmrd':dict(repository=jmrd_manifest['sourceRepository'],commit=jmrd_manifest['sourceCommit'],license=jmrd_manifest['license'],attribution=next(d['attribution'] for d in docs if d['id'].startswith('jmrd:')),url=jmrd_manifest['rawTrainUrl'],licenseUrl='https://creativecommons.org/licenses/by-sa/4.0/',split='Official upstream TRAIN only; no valid/test source read')}
    audit=dict(schemaVersion=1,scope='Authentic admitted TRAIN originals only; no DEV/TEST source opened',stage='1 metadata and sample production; semantic reading pending',preregistrationSha256=sha(out/'PREREGISTRATION.json'),codeSha256=sha(pathlib.Path(__file__)),sourceDocumentsSha256=sha(docs_path),addedSourceDocumentsSha256=sha(added_docs),rawTrainReceiptManifestSha256=hashlib.sha256(json.dumps(sorted(receipts),separators=(',',':')).encode()).hexdigest(),rawJmrdTrainSha256=sha(args.jmrd_train),trainIndexSha256=sha(index_path),trainTokensSha256=sha(token_path),tokenizerSha256=sha(tokenizer_path),responseTurnsSha256=sha(destination),semanticSampleSha256=sha(out/'semantic-sample.json'),sourceProvenance=source_provenance,perSource=dict(stats),schemaKeyOccurrenceCounts=dict(keys),licenseDocumentCounts=dict(licenses),perSourceTokenSpanCoverage=dict(span_stats),perSourceViewWindowCoverage=dict(row_stats),speakerMetadataCriteriaPass=speaker_pass,explicitReplyToFieldsObserved=observed_reply_fields,explicitReplyToAbsent=True,relationEstablished='adjacent other-declared-speaker next utterance in original ordinal order',semanticReplyToEstablishedForAllPairs=False,semanticReviewPending=True,stage1Passed=False,stage1PassNotDecidedUntilActualSampleReading=True,noTimestampReordering=True,noSpeakerTextInsertedIntoModelInput=True,samplingOrSourceTextChanged=False,eligibilitySpeakerCriterionChangesExistingCoverage=False,originalUtteranceIdsPreserved=True,additionalOptimizerUpdates=0,modelInstantiated=False,gradientComputed=False,heldoutSourceOpened=False,elapsedSeconds=time.monotonic()-begun,cautions=['No explicit reply-to annotation; speaker alternation does not establish semantic response quality','RP invalid/decreasing timestamps are disclosed; original ordinal remains authoritative','JMRD public roles are not participant identities; no cross-source speaker-disjointness claim','Both sources CC-BY-SA-4.0 with existing attribution/provenance retained'])
    write(out/'speaker-audit.json',audit)
    print(json.dumps(dict(speakerMetadataCriteriaPass=speaker_pass,semanticReviewPending=True,stage1Passed=False,perSource=dict(stats),responseTurnsSha256=sha(destination),semanticSampleSha256=sha(out/'semantic-sample.json'),speakerAuditSha256=sha(out/'speaker-audit.json'),codeSha256=sha(pathlib.Path(__file__)),additionalOptimizerUpdates=0,elapsedSeconds=time.monotonic()-begun)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=pathlib.Path,default=pathlib.Path('/workspace/4k29/training/language/round47'))
    parser.add_argument('--out',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent)
    parser.add_argument('--feature',type=pathlib.Path,default=pathlib.Path('/workspace/round48-response-turns.json'))
    parser.add_argument('--realpersona-train',type=pathlib.Path,default=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train'))
    parser.add_argument('--jmrd-train',type=pathlib.Path,default=pathlib.Path('/workspace/next-source-candidate-jmrd/upstream-train.json'))
    main(parser.parse_args())
