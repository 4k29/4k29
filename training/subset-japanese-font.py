"""Build the regular Japanese webfont from an authorized upstream font file.

Usage: python training/subset-japanese-font.py NotoSansJP[wght].ttf
Build-only dependencies: fonttools==4.66.1 and brotli==1.2.0.
"""
import pathlib
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset

root=pathlib.Path(__file__).resolve().parent.parent
chars={chr(n) for n in range(0x3000,0x3100)}|{chr(n) for n in range(0xff00,0xfff0)}
for lead in range(0xb0,0xd0):
    for tail in range(0xa1,0xff):
        try:
            chars.update(bytes([lead,tail]).decode('euc_jp'))
        except UnicodeDecodeError:
            pass
for path in (root/'docs').rglob('*'):
    if path.suffix in ['.json','.js','.html','.css']:
        chars.update(c for c in path.read_text() if ord(c)>127)
font=instantiateVariableFont(TTFont(sys.argv[1]),{'wght':400},inplace=True)
options=subset.Options();options.flavor='woff2';options.layout_features=['*'];options.notdef_glyph=True
builder=subset.Subsetter(options=options);builder.populate(unicodes=[ord(c) for c in chars]);builder.subset(font)
font.flavor='woff2';target=root/'docs/assets/noto-sans-jp.woff2';font.save(target)
print({'requestedCharacters':len(chars),'fontBytes':target.stat().st_size})
