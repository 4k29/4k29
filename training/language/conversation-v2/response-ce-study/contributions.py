"""Prospective teacher contributions; never recorded as processed training targets."""
import json,pathlib,re,statistics,collections
P=pathlib.Path(__file__).resolve().parent
load=lambda n:json.loads((P/n).read_text())
def main():
 pack=load('CANDIDATE_SPANS.json')['parts'];cards=load('LOCAL_REVIEW_CARDS.json');cards['train']+=load('LOCAL_SUPPLEMENT_CARDS.json');by={r['id']:r for rr in cards.values()for r in rr};counter={};profiles={}
 for part,rs in pack.items():
  groups={};speakers=collections.Counter();lens=[];genres=collections.Counter()
  for r in rs:
   z=groups.setdefault(r['semantic_type'],collections.Counter());start=r['response_body_start'];ys=r['tokens'][1:];mask=r['response_ce_mask'];z['responses']+=1;z['input_nonpadding']+=len(ys);z['A_loss']+=len(ys);z['B_loss']+=sum(mask);z['response_body']+=len(r['tokens'])-start-1;z['B_EOS']+=1;z['A_role']+=sum(t in [3,4]for t in ys);z['A_EOS']+=sum(t==2 for t in ys);speakers.update(r['speakers']);lens.append(len(ys));text='\n'.join(by[r['id']]['history_text']+[by[r['id']]['response_text']])
   for key,pat in {'food':'料理|食べ|ご飯|カレー|餃子|アイス|パスタ','hobby_media':'映画|ドラマ|アニメ|漫画|ゲーム|音楽|読書','pets':'犬|猫|ペット|ウサギ','travel':'旅行|観光|温泉|海外','work_study':'仕事|学校|勉強|職場|バイト','daily_life':'天気|暑|寒|寝|起き|家事|買い物|洗濯'}.items():genres[key]+=bool(re.search(pat,text))
  counter[part]={k:dict(z)for k,z in groups.items()};profiles[part]=dict(input_length=dict(min=min(lens),median=statistics.median(lens),max=max(lens),mean=statistics.mean(lens)),max_conversations_per_source_speaker=max(speakers.values()),source_speakers=len(speakers),genre_multilabel_keyword_proxy=dict(genres),genre_proxy_is_not_semantic_annotation=True,all_full_histories_fit_context256=True)
 (P/'CONTRIBUTIONS.json').write_text(json.dumps(dict(per_type=counter,profiles=profiles,only_source='RealPersona',held_tokens_published=False,optimizer_calls=0),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
