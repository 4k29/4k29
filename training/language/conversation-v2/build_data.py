"""Fresh-series RP corpus: speaker split before tokenizer fit; true turn EOS.

No model/optimizer imports, no new TEST content, no source text rewriting.
Run only after root's data-fit authorization. Existing artifacts are immutable.
"""
import argparse,array,collections,hashlib,json,pathlib,sys,unicodedata
from new_tokenizer import Encoder,fit
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
OLD=ROOT/'training/language/round46';RAW=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train')
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def normalized(s):return ''.join(unicodedata.normalize('NFKC',s).split())
def relative(p):return str(p.relative_to(ROOT))
def exposed_documents():
    names=[ROOT/'training/language/diagnostics/learnability-20261026/candidate-panel.json',
        ROOT/'training/language/diagnostics/context-use-20261025/panel.json',
        ROOT/'training/language/round48-preflight/semantic-sample.json',OLD/'execution/context-auxiliary-pool.json']
    result=set();receipts=[]
    for p in names:
        x=read(p);receipts.append({'path':relative(p),'sha256':sha(p)})
        for row in x.get('cases',x.get('rows',[])):result.add(row['document'])
    return result,receipts
def main(a):
    out=a.output.resolve()
    if out.exists():raise ValueError('New data output directory required; never overwrite frozen artifacts')
    if not out.is_relative_to(H):raise ValueError('Data output must stay inside isolated v2 folder')
    docs={};receipts=[]
    for p in [OLD/'sources/documents.jsonl',OLD/'added-human-source/documents.jsonl']:
        receipts.append({'path':relative(p),'sha256':sha(p)})
        for line in p.open():
            d=json.loads(line)
            if d['originalDocument'].startswith('realpersona:'):
                assert d['partition']=='train'and d['license']=='CC-BY-SA-4.0'
                if d['originalDocument']in docs:assert docs[d['originalDocument']]['textSha256']==d['textSha256']
                docs[d['originalDocument']]=d
    assert len(docs)==8975
    exposed,prior_receipts=exposed_documents();receipts+=prior_receipts
    split=[];parts={'train':[],'dev':[]};families={};original=[];all_speakers=set()
    for ident,d in sorted(docs.items()):
        path=RAW/(ident.split(':')[1]+'.json');raw=read(path);source_sha=sha(path);assert source_sha==d['sourceSha256']
        us=raw['utterances'];assert '\n'.join(u['text']for u in us)==d['text'];assert len(us)==d['utteranceCount']
        speakers=raw['interlocutors'];assert len(set(speakers))==2;all_speakers.update(speakers)
        assert all(u['utterance_id']==j and u['interlocutor_id']in speakers for j,u in enumerate(us))
        assert all(us[j-1]['interlocutor_id']!=us[j]['interlocutor_id']for j in range(1,len(us)))
        sides=['dev'if int(digest('conversation-v2-speaker-split-20261026-v1|'+s),16)%100<20 else'train'for s in speakers]
        partition=sides[0]if sides[0]==sides[1]else'quarantine-cross-speaker'
        if partition=='dev'and ident in exposed:partition='quarantine-prior-exposed-dev'
        family=digest(normalized(d['text']))
        if family in families:raise ValueError('Normalized whole-document duplicate family requires prior policy; stop')
        families[family]=ident
        split.append({'id':ident,'partition':partition,'speakers':speakers,'normalizedDocumentFamily':family,'sourceSha256':source_sha})
        original.append({'path':str(path),'sha256':source_sha})
        if partition in parts:
            roles={s:3+i for i,s in enumerate([us[0]['interlocutor_id'],us[1]['interlocutor_id']])}
            parts[partition].append({'id':ident,'partition':partition,'sourceSha256':source_sha,'sourceTextSha256':d['textSha256'],
                'normalizedDocumentFamily':family,'speakers':speakers,'sourceUrl':d['url'],'license':d['license'],'attribution':d['attribution'],
                'utterances':[{'ordinal':j,'originalUtteranceId':u['utterance_id'],'speakerId':u['interlocutor_id'],
                    'localRoleToken':roles[u['interlocutor_id']],'text':u['text']}for j,u in enumerate(us)]})
    train_speakers={s for d in parts['train']for s in d['speakers']};dev_speakers={s for d in parts['dev']for s in d['speakers']}
    assert not train_speakers&dev_speakers and len(parts['train'])>=3000 and len(parts['dev'])>=64
    out.mkdir();write(out/'split.json',{'rule':'persistent speaker SHA modulo100<20 DEV; cross-speaker and previously exposed DEV documents quarantined',
        'seedString':'conversation-v2-speaker-split-20261026-v1','allAdmittedOriginalTrainDocuments':len(docs),'rows':split,
        'trainSpeakers':sorted(train_speakers),'devSpeakers':sorted(dev_speakers),'exposedDocumentsExcludedFromDev':sorted(exposed),
        'notAnUnseenBaselineForR46':True,'reservedTestRead':False})
    for part,ds in parts.items():
        with (out/(part+'.docs.jsonl')).open('w')as f:
            for d in ds:f.write(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    tok=fit(parts['train'],word_merges=512,sample_character_limit=400000);write(out/'tokenizer.json',tok);enc=Encoder(tok)
    for part in parts:
        sample=sorted([u['text']for d in parts[part]for u in d['utterances']],key=lambda s:digest('v2-encoding-check|'+s))[:256]
        for text in sample:assert enc(text)==enc.reference(text)
    vocab=[bytes.fromhex(s)for s in tok['bytes']];windows={};tokenpaths={};stat={};unknown={};bydoc={}
    for part,ds in parts.items():
        values=array.array('I');rows=[];chars=0;turns=0;unknown_counts=collections.Counter()
        for d in ds:
            full=[1];encoded=[]
            for u in d['utterances']:
                text=u['text'];ids=enc(text);assert b''.join(vocab[t]for t in ids)==text.encode('utf8')
                full.extend([u['localRoleToken']]+ids+[2]);encoded.append(ids);chars+=len(text);turns+=1
                unknown_counts.update(c for c in text if c not in tok['glyphTokenIds'])
            offset=len(values);values.extend(full);bydoc[d['id']]={'encoded':encoded,'full':full,'offset':offset}
            for start in range(0,len(full)-1,256):
                n=min(257,len(full)-start)
                if n>=2:rows.append({'offset':offset+start,'length':n,'document':d['id'],'startToken':start})
        if sys.byteorder!='little':values.byteswap()
        path=out/(part+'.tokens.bin');path.write_bytes(values.tobytes());tokenpaths[part]=path
        if part=='dev':rows=sorted(rows,key=lambda r:digest('v2-dev-tf64|'+r['document']+'|'+str(r['startToken'])))[:64]
        windows[part]=rows
        stat[part]={'documents':len(ds),'utterances':turns,'characters':chars,'streamTokens':len(values),'windows':len(rows),
            'unknownUnicodeTypes':len(unknown_counts),'unknownUnicodeOccurrences':sum(unknown_counts.values()),'unknownUtf8Bytes':sum(len(c.encode())*n for c,n in unknown_counts.items()),
            'byteFallbackPreservesUnknownCharacters':True,'trueTurnEosPositions':turns}
        unknown[part]=dict(unknown_counts)
    cases=[]
    for d in sorted(parts['dev'],key=lambda d:digest('v2-dev-document-v1|'+d['id'])):
        us=d['utterances'];encoded=bydoc[d['id']]['encoded'];candidate=[]
        for target in range(2,len(us)):
            gold=encoded[target]
            if not 8<=len(us[target]['text'])or not 1<=len(gold)<=96:continue
            for history_count in [4,3,2]:
                if target<history_count:continue
                first=target-history_count;prefix=[1]
                for j in range(first,target):prefix.extend([us[j]['localRoleToken']]+encoded[j]+[2])
                prefix.append(us[target]['localRoleToken'])
                if len(prefix)<=64:
                    candidate.append((digest('v2-dev-target-v1|'+d['id']+'|'+str(target)),target,first,prefix));break
        if not candidate:continue
        _,target,first,prefix=min(candidate)
        cases.append({'id':'v2-dev-'+str(len(cases)).zfill(3),'document':d['id'],'split':'v2-DEV-scratch-document-and-speaker-heldout',
            'sourceSha256':d['sourceSha256'],'sourceUrl':d['sourceUrl'],'license':d['license'],'attribution':d['attribution'],
            'prefixTokens':prefix,'goldTokens':encoded[target],'goldEos':2,'targetText':us[target]['text'],'targetOrdinal':target,
            'history':us[first:target],'historyTurns':target-first,'targetLocalRoleToken':us[target]['localRoleToken'],
            'prefixText':'\n'.join(u['text']for u in us[first:target])+'\n','generationMaxNewTokens':192,
            'R46TrainExposure':True,'newTokenizerTrainExposure':False,'referenceIsNotUniqueAcceptableReply':True})
        if len(cases)==32:break
    assert len(cases)==32 and len({c['document']for c in cases})==32
    write(out/'benchmark-dev.json',{'status':'FIXED_INPUTS_PRE_MODEL_OUTPUT; human semantic tags pending','cases':cases,
        'scope':'Scratch-series development benchmark only; original TRAIN already exposed to R46; not sealed TEST',
        'selection':'SHA-ranked documents and original target ordinal, target text>=8chars, complete2-4turn histories, prefix<=64tokens, gold<=96tokens; no model scores'})
    write(out/'unknown-character-audit.json',unknown)
    write(out/'data.json',{'schemaVersion':1,'series':'conversation-v2','source':'Existing original human RealPersona TRAIN only',
        'tokenizerPath':relative(out/'tokenizer.json'),'tokenizerSha256':sha(out/'tokenizer.json'),
        'trainTokensPath':relative(tokenpaths['train']),'trainTokensSha256':sha(tokenpaths['train']),'trainWindows':windows['train'],
        'devTokensPath':relative(tokenpaths['dev']),'devTokensSha256':sha(tokenpaths['dev']),'devWindows':windows['dev'],
        'splitSha256':sha(out/'split.json'),'benchmarkPath':relative(out/'benchmark-dev.json'),'benchmarkSha256':sha(out/'benchmark-dev.json'),
        'statistics':stat,'sourceReceipts':receipts,'originalTrainSourceReceiptsDigest':digest(json.dumps(original,separators=(',',':'))),
        'originalTrainSourceCount':len(original),'windowConvention':'length is seq tokens2..257; xseq[:-1],yseq[1:],PADx0/y-100; stride256; no document mixing',
        'streamConvention':'BOS1 then local human-speaker role3/4, unchanged utterance BPE, EOS2 at every real utterance boundary; role IDs not assistant/user labels',
        'newTokenizerTrainOnly':True,'noParentLearnedTokenizer':True,'noModelOrOptimizerUpdates':True,'reservedTestRead':False,
        'codeReceipts':{relative(p):sha(p)for p in [pathlib.Path(__file__),H/'new_tokenizer.py',ROOT/'training/dialogue/tokenizer.py',ROOT/'training/language/round10/word_bpe.py']}})
    write(out/'build-receipt.json',{'status':'PASS','dataSha256':sha(out/'data.json'),'benchmarkSha256':sha(out/'benchmark-dev.json'),
        'splitCounts':dict(collections.Counter(x['partition']for x in split)),'statistics':stat,'vocabulary':len(tok['bytes']),
        'glyphAssemblyRules':tok['glyphRules'],'wordBpeRules':tok['wordMerges'],'bpeSampleCharacters':tok['fitSubset']['characters'],
        'referenceEncodeTokenIdentityChecks':512,'modelInstantiated':False,'optimizerUpdates':0,'sealedTestRead':False})
    print(json.dumps(read(out/'build-receipt.json'),ensure_ascii=False),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);main(p.parse_args())
