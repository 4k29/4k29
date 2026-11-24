"""Data-only R46 native-prefix coverage; never alter the fixed v2 benchmark."""
import argparse,hashlib,importlib.util,json,pathlib,statistics
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(a):
    bench=json.loads(a.benchmark.read_text());tokpath=ROOT/'training/language/round46/multiview/tokenizer.json';tok=json.loads(tokpath.read_text())
    spec=importlib.util.spec_from_file_location('_v2_legacy_byte_bpe',ROOT/'training/dialogue/tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    rows=[]
    for c in bench['cases']:
        prefix=[1]+m.encode_stream(c['prefixText'],tok);gold=m.encode_stream(c['targetText'],tok)
        assert b''.join(bytes.fromhex(tok['bytes'][t])for t in prefix[1:])==c['prefixText'].encode()
        rows.append({'id':c['id'],'document':c['document'],'oldPrefixTokens':len(prefix),'newPrefixTokens':len(c['prefixTokens']),
            'oldGoldTokens':len(gold),'newGoldTokens':len(c['goldTokens']),'oldSupportsFixed192WithoutCrop':len(prefix)+192<=256,
            'oldPrefixTokensIncludingBos':prefix,'oldGoldTokensExcludingEos':gold})
    lengths=[x['oldPrefixTokens']for x in rows]
    result={'scope':'R46 is an exposed old-TRAIN reference using its native plain-text prefix; not an unseen or single-factor new-series comparison',
        'benchmarkSha256':sha(a.benchmark),'legacyTokenizerSha256':sha(tokpath),'fixedMaxNewTokens':192,'legacyContext':256,
        'supportedCasesWithoutCrop':sum(x['oldSupportsFixed192WithoutCrop']for x in rows),'totalCases':len(rows),
        'legacyPrefixLength':{'min':min(lengths),'median':statistics.median(lengths),'max':max(lengths)},
        'selectorChanged':False,'silentCrop':False,'perCaseGenerationBudgetChanged':False,'optimizerUpdates':0,'modelInstantiated':False,
        'oldTokenizerTrainExposure':True,'newTokenizerDevFitExposure':False,'rows':rows}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--benchmark',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);main(p.parse_args())
