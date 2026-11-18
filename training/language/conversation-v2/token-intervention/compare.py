"""Generate input-level comparison including unavailable interventions."""
from verify import P,base,bykey,plan,pieces,table
import json
def phrase(ids):
    return b''.join(pieces[t] for t in ids).decode(errors='replace')
def main():
    judged={(r['model'],r['id'],r['arm']):r for r in json.loads((P/'REVIEW.json').read_text())}
    out=[]
    for e in plan['selection']:
        k=e['model'],e['id'],e['arm']
        x=base[k[:2]]
        r=bykey.get(k)
        row=dict(model=k[0],id=k[1],arm=k[2],status='executed' if r else ('no suitable candidate' if x['repeat'] else 'baseline did not repeat'),
            baseline_harmful=x['judgment']['harmful_repetition'],baseline_repeat=x['repeat'],baseline_stop=x['stop'])
        if r:
            j=r['j']
            row.update(position=j,original=phrase([e['original']]),replacement=e['piece'],rank=e['rank'],original_p=e['p_original'],replacement_p=e['p'],
                first_autonomous=r['steps'][0],length=len(r['tokens']),stop=r['stop'],recurrence=r['recurrence'],judgment=judged[k])
            rationale={'炭':'入力の炭素鋼の語彙に戻れる。','気':'気圧・気流・気候など気象に関連する語の先頭になり得る。','分':'入力の観測時間の単位を再利用できる。','m':'入力の風速単位 m/s の先頭。数値の妥当性は保証しない。','的':'直前の「国際」を形容表現にできる。','域':'「地」に続けて場所の表現を作れる。','球':'「地」に続く語を形成できる。','見':'見え方を述べる動詞を開始できる。','人':'直前の大学に関する人を示す語の先頭になり得る。','名':'大学に続いて名称を表せる。','社':'入力にある会社名の語彙を再利用できる。','実':'作業に関する実践・実施などの語を開始できる。','温':'気温を扱った直前の語彙と関連する。','使':'「酸素を」に続く動詞を開始できる。','つ':'「水を」に続く動詞の先頭になり得る。','また':'文境界で新事実を加えず次文を開始できる。','」':'直前のかぎ括弧を閉じられる。'}
            row['selection_reason']=rationale.get(e['piece'],'前の名詞句・述語に接続できる機能表現またはその先頭。')
            if r['recurrence']:
                ids=r['recurrence']['tokens']
                row.update(repeated_phrase=phrase(ids),same_as_original=ids==x['repeat']['tokens'])
        out.append(row)
    (P/'COMPARISON.json').write_text(json.dumps(out,indent=1,ensure_ascii=False)+'\n')
    (P/'TABLES.md').write_text(table())
if __name__=='__main__':main()
