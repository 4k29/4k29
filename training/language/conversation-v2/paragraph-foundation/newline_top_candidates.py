"""Eight fixed B next-token distributions; exclusion is reporting-only, never decoding."""
import argparse
import gzip
import json
import pathlib
import sys
from newline_separator_probe import sha, rank

P = pathlib.Path(__file__).resolve().parent

def candidate_summary(values, probabilities, pieces, nl, gold):
    order = sorted(range(len(values)), key=lambda t: (-values[t], t))
    def row(t):
        try:
            text = pieces[t].decode('utf-8')
        except UnicodeDecodeError:
            text = None
        return dict(token=t, raw_hex=pieces[t].hex(), text=text,
                    full_vocabulary_rank=rank(values,t), probability=probabilities[t],
                    special=t<6, whitespace_only=bool(text) and not text.strip(),
                    incomplete_UTF8_piece=text is None)
    top = next(t for t in order if t != nl)
    return dict(top10=[row(t) for t in order[:10]], gold=row(gold),
                top_non_newline=dict(row(top), conditional_probability_given_not_newline=probabilities[top]/(1-probabilities[nl])),
                newline=row(nl))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--out', type=pathlib.Path, default=P/'newline-followup/top-candidates')
    a = ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    assert not (a.out/'RESULTS.json').exists(), 'Do not overwrite completed diagnostics'
    source = P/'newline-followup/EIGHT_CASE_AUDIT.json'
    previous = P/'newline-followup/single-lf/RESULTS.json'
    tok = P.parent/'data/tokenizer.json'
    manifest = P/'artifacts/B-579/checkpoint.json'
    cases = json.loads(source.read_text())['cases']
    pieces = [bytes.fromhex(s) for s in json.loads(tok.read_text())['bytes']]
    meta = json.loads(manifest.read_text())
    assert len(cases)==8 and pieces[16]==b'\n'
    assert meta['sha256']=='3cebff9801302bd9969601e539adccaca7e0ea83943cc96bf2dc0b35f0906b9c'
    watched = [source,previous,tok,manifest,P/'ACTUAL_UPDATES_B.jsonl',P/'PLAN.json']
    before = {str(f):sha(f) for f in watched}
    protocol = dict(checkpoint_sha256=meta['sha256'], selection='Exactly the previously fixed8 LF2 histories; no reselection',
        top_k=10, exclusion='Only token16 removed from a sorted reporting list; all original probabilities remain unchanged. Conditional probability is separately labeled. Special tokens, spaces and byte fragments are not silently skipped.',
        interpretation='A one-token candidate is not evidence of a coherent full continuation. No candidate is fed back to the model.',
        model_forward_calls=8, optimizer_updates=0, autoregressive_generations=0,
        numerical='Raw FP32 logits; FP64 full-vocabulary softmax at temperature1. Rank uses minimum tie rank; display order breaks exact ties by token ID.',
        existing_probability_reproduction_tolerance=1e-5, input_sha256=before,
        implementation_sha256={str(f):sha(f) for f in [pathlib.Path(__file__),P/'newline_separator_probe.py',P.parent/'core.py',P.parent.parent/'model.py']})
    (a.out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2)+'\n')
    import torch
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    sys.path.insert(0,str(P.parent))
    import core
    assert sha(a.checkpoint)==meta['sha256']
    obj=torch.load(a.checkpoint,map_location='cpu',weights_only=False)
    assert core.digest(obj)==meta['full_state_digest'] and obj['active_cursor']==579
    with torch.random.fork_rng(devices=[]):
        model=core.decoder(obj['trajectory']['config'])
    model.load_state_dict(obj['trajectory']['model'],strict=True)
    model.eval()
    del obj
    model_hash=core.digest(model.state_dict())
    prior=json.loads(previous.read_text())['cases']
    rows=[];all_logits=[]
    with torch.inference_mode():
        for case,old in zip(cases,prior):
            assert case['index']==old['index']
            ids=case['history_tokens']
            assert ids==old['predictions']['LF2']['input_tokens'] and ids[-2:]==[16,16]
            assert b''.join(pieces[t]for t in ids).hex()==case['history_raw_hex']
            log=model(torch.tensor([ids],dtype=torch.long))[0,-1]
            values=log.tolist();prob=log.double().softmax(-1).tolist()
            summary=candidate_summary(values,prob,pieces,16,case['gold'])
            assert abs(summary['newline']['probability']-old['predictions']['LF2']['P_newline'])<=1e-5
            assert summary['gold']['full_vocabulary_rank']==old['predictions']['LF2']['rank_original_nonnewline_gold']
            assert abs(summary['gold']['probability']-old['predictions']['LF2']['P_original_nonnewline_gold'])<=1e-5
            rows.append(dict(index=case['index'],source_id=case['source_id'],source_offset=case['source_offset'],input_tokens=ids,
                             history_text=case['history_text'],original_following_text=case['following_original_text'],**summary))
            all_logits.append(dict(index=case['index'],input_tokens=ids,logits_FP32=values))
    assert core.digest(model.state_dict())==model_hash and sha(a.checkpoint)==meta['sha256']
    assert before=={str(f):sha(f)for f in watched}
    with (a.out/'LOGITS.json.gz').open('wb')as f:
        with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,filename='')as z:
            z.write(json.dumps(all_logits,separators=(',',':'),allow_nan=False).encode())
    result=dict(protocol_sha256=sha(a.out/'PROTOCOL.json'),checkpoint_sha256=meta['sha256'],cases=rows,
                all_logits_archive_sha256=sha(a.out/'LOGITS.json.gz'),model_forward_calls=8,optimizer_updates=0,
                autoregressive_generations=0,decoder_suppression_added=False,model_and_checkpoint_unchanged=True,
                stored_inputs_and_results_unchanged=True,not_a_new_DEV_or_TEST=True)
    (a.out/'RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([dict(index=r['index'],top_non_newline=r['top_non_newline'],gold=r['gold'])for r in rows],ensure_ascii=False))

if __name__=='__main__':main()
