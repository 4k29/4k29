"""Acquire versioned Japanese Wikipedia lead extracts for a new holdout."""
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

TITLES = '''
石臼 火鉢 囲炉裏 唐箕 招き猫 千代紙 短冊 文箱 印籠 根付 紙縒 簾 桶 木槌 糸車
鋸 鉋 鑿 錐 金槌 砥石 はさみ 糸鋸 彫刻刀 縫い針 紐 ろくろ 陶芸 筆 筆記具
犬ぞり 打楽器 指揮棒 音叉 メトロノーム 譜面台 鍵盤楽器 手風琴 アコーディオン
墨 浮世絵 石版画 銅版画 紙版画 モザイク 西陣織 ランプ 油灯 蝋燭 提げ灯
笛 口琴 笙 横笛 太鼓 撥 拍子木 鐘 風車 水車 天秤 計量器 砂時計 水時計
金継ぎ 革細工 漆塗り 草木染め 絞り染め 組紐 寄せ木 結び目 編み針 機織り
葦簀 籠 籠細工 藁細工 藁靴 草履 足袋 下駄 木靴 旅籠 道標 一里塚 早馬 手押し車
懐中時計 拡大鏡 顕微鏡 双眼鏡 万華鏡 掛け時計 木琴 蓄音機 写真機 水準器
把手 栓抜き 火打石 灰皿 茶こし 急須 薬缶 ざる 漏斗 溝蓋 籐細工
'''.split()
ENDPOINT = 'https://ja.wikipedia.org/w/api.php'

def fetch(params):
    req = Request(ENDPOINT+'?'+urlencode(params), headers={'User-Agent':'4k29-research/1.0 (GitHub 4k29/4k29)'})
    with urlopen(req,timeout=30) as response:
        return json.load(response)

if __name__ == '__main__':
    records = []
    for i in range(0,len(TITLES),18):
        data = fetch(dict(action='query', prop='extracts|revisions', exintro=1, explaintext=1, exlimit='max',
                          rvprop='ids|timestamp',formatversion=2,format='json',titles='|'.join(TITLES[i:i+18])))
        records.extend(data['query']['pages'])
    with open('SOURCES.json','w') as file:
        json.dump(records,file,ensure_ascii=False,indent=2)
    with open('RIGHTS.json','w') as file:
        json.dump(fetch(dict(action='query',meta='siteinfo',siprop='rightsinfo',format='json')),file,ensure_ascii=False)
