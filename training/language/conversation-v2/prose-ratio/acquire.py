"""Capture versioned Wikimedia plain-text extracts and site rights."""
import json
import runpy
from pathlib import Path

fetch = runpy.run_path(str(Path(__file__).resolve().parents[1] / "prose-development/acquire.py"))["fetch"]

TITLES = '''
湯煎 落とし蓋 灰汁抜き 下茹で 打ち水 乾燥剤 除湿機 湯たんぽ 風呂敷
繕い物 仕付け糸 刺し子 草履 裁縫 箸置き 茶漉し 障子 襖 すだれ
網戸 棕櫚箒 はたき ちりとり 砕石 竹垣 生垣 雨樋 手水鉢 打掛 八掛
縁台 間伐 挿し木 取り木 接ぎ木 剪定 コンポスト 落ち葉 連作障害
あく巻き 焼き芋 枝豆 発芽玄米 保存食 氷室 ぬか床 飯寿司 きりたんぽ
羊羹 べっこう飴 わらび餅 おやき 梅干し 酒粕 茶筅 水出しコーヒー
袱紗 花札 福笑い けん玉 竹馬 紙飛行機 張り子 七宝焼 型染め
小紋 麻の葉文様 亀甲文様 縄文土器 おはじき 蚊取り線香 蛇口
スノーシュー 水切り 水筒 上靴 黒板消し 登山靴 かんじき 地図記号
'''.split()

if __name__ == '__main__':
    import hashlib
    import re
    from concurrent.futures import ThreadPoolExecutor
    from urllib.parse import quote
    from urllib.request import Request, urlopen
    from bs4 import BeautifulSoup

    def page(title):
        url = 'https://ja.wikipedia.org/wiki/' + quote(title)
        try:
            with urlopen(Request(url,headers={'User-Agent':'4k29-research/1.0 (GitHub 4k29/4k29)'}),timeout=12) as res:
                raw = res.read()
        except OSError as exc:
            return dict(title=title,error=str(exc))
        soup = BeautifulSoup(raw, 'html.parser')
        revision = re.search(rb'"wgRevisionId":(\d+)', raw)
        identity = soup.select_one('h1')
        if not revision or not identity or identity.get_text(strip=True) != title:
            return dict(title=title,error='Redirect or missing revision')
        body = soup.select_one('.mw-parser-output')
        if body is None:
            return dict(title=title,error='Missing prose')
        paras = []
        for p in body.select('p'):
            if p.find_parent(['table','blockquote','aside','figure']):
                continue
            for n in p.select('sup.reference'):
                n.decompose()
            text = p.get_text().strip()
            if text.count('。') >= 3:
                paras.append(text)
        return dict(title=title,revision=int(revision[1]),html_sha=hashlib.sha256(raw).hexdigest(),
                    paragraphs=paras[:6],url=url)

    with ThreadPoolExecutor(max_workers=5) as workers:
        records = list(workers.map(page,TITLES))
    Path('SOURCES.json').write_text(json.dumps(records, ensure_ascii=False))
    if not Path('RIGHTS.json').exists():
        rights = fetch(dict(action='query',meta='siteinfo',siprop='rightsinfo',format='json'))
        Path('RIGHTS.json').write_text(json.dumps(rights, ensure_ascii=False))
