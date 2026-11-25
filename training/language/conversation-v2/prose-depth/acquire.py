"""Freeze independent Japanese Wikipedia lead snapshots before any inference."""
import json
from urllib.request import Request,urlopen

TITLES='手ぬぐい 風呂敷 ふろしき包み 茶筅 茶杓 茶托 硯 筆洗 文鎮 まな板 すり鉢 おろし金 鰹節削り器 蒸籠 蒸し器 盆提灯 提灯 竹細工 寄木細工 刺し子 つまみ細工 織部焼 備前焼 益子焼 小石原焼 曲物 樽 升 絵馬 破魔矢 しめ飾り 飾り結び 水引 折り鶴 けん玉 お手玉 紙風船 影絵 写し絵 紙相撲 竹とんぼ 縄跳び 天体観測 測鉛 編み物 綴織 漆器 缶切り 針山 ものさし 指ぬき'.split()

TITLES += "研ぎ石 菜箸 計量カップ 圧力鍋 たわし ほうき ちりとり 打ち水 巻き簾 鍋敷き チーズおろし 竹箒 一輪挿し 木版画 和綴じ 和紙 水彩画 刺繍 鉄瓶 土鍋 万年筆 そろばん 風鈴 張り子 こま 犬張子 羽根突き 和傘 弁当箱 曲げわっぱ 缶詰".split()
def get(titles):
    from urllib.parse import urlencode
    params=dict(action='query',prop='extracts|revisions',exintro=1,explaintext=1,
                exlimit='max',rvprop='ids|timestamp',formatversion=2,format='json',
                titles='|'.join(titles))
    url='https://ja.wikipedia.org/w/api.php?'+urlencode(params)
    with urlopen(Request(url,headers={'User-Agent':'4k29-research/1.0 (GitHub 4k29/4k29)'}),timeout=30) as f:
        return json.load(f)['query']['pages']

if __name__=='__main__':
    rows=[]
    for offset in range(0,len(TITLES),18):
        rows.extend(get(TITLES[offset:offset+18]))
    with open('SOURCE_SNAPSHOTS.json','w') as f:
        json.dump(rows,f,ensure_ascii=False,indent=2)
