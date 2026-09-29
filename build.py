from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os

ROOT = Path(__file__).parent
W, H = 900, 560

THEMES = {
    "dark": {
        "bg":"#111315","side":"#171a1d","top":"#15181b","panel":"#1a1d20",
        "line":"#2a2f34","fg":"#e7e9ea","muted":"#8b949e",
        "selected":"#22272b","subtle":"#202428"
    },
    "light": {
        "bg":"#ffffff","side":"#f4f5f6","top":"#f8f9fa","panel":"#f3f4f6",
        "line":"#d9dde2","fg":"#22262a","muted":"#6e7781",
        "selected":"#e9ecef","subtle":"#f0f2f4"
    },
}

def hexrgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

def find_font():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("No suitable CJK font found")

FONT_PATH = find_font()
FONT = ImageFont.truetype(FONT_PATH, 14)

def draw_text(draw, xy, value, fill, anchor=None):
    draw.text(xy, value, font=FONT, fill=fill, anchor=anchor)

def rounded(draw, box, radius, fill, outline=None):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=1)

def check(draw, x, y, color):
    draw.line((x, y, x+3, y+3, x+9, y-6), fill=color, width=2)

def make_frame(theme_name, stage, cursor=True, pulse=1.0):
    c = {k: hexrgb(v) for k, v in THEMES[theme_name].items()}
    image = Image.new("RGB", (W, H), c["bg"])
    d = ImageDraw.Draw(image)

    # Frame / sidebar
    d.rectangle((0, 0, 182, H), fill=c["side"])
    d.line((182, 0, 182, H), fill=c["line"], width=1)
    d.rectangle((182, 0, W, 48), fill=c["top"])
    d.line((0, 48, W, 48), fill=c["line"], width=1)

    # Mac-like traffic lights, without recreating a real app chrome.
    for x, color in [(22, (255,95,87)), (42, (254,188,46)), (62, (40,200,64))]:
        d.ellipse((x-5, 19, x+5, 29), fill=color)

    draw_text(d, (541, 24), "4k29 — agent session", c["muted"], anchor="mm")

    # Sidebar
    draw_text(d, (18, 78), "Workspace", c["muted"])
    draw_text(d, (18, 112), "4k29", c["fg"])
    rounded(d, (10,128,172,162), 8, c["selected"])
    draw_text(d, (24,150), "GitHub profile", c["fg"])
    draw_text(d, (24,184), "Tecirc", c["fg"])
    draw_text(d, (18,232), "Sessions", c["muted"])
    draw_text(d, (24,266), "Profile draft", c["fg"])
    draw_text(d, (24,298), "Tecirc notes", c["muted"])
    draw_text(d, (18,530), "vibe-coding", c["muted"])

    # User prompt
    rounded(d, (214,76,866,130), 12, c["panel"])
    draw_text(d, (232,109), "このGitHub、いい感じにしといて。", c["fg"])

    # Agent status
    dot = tuple(int(c["muted"][i]*pulse + c["bg"][i]*(1-pulse)) for i in range(3))
    d.ellipse((217,161,223,167), fill=dot)
    draw_text(d, (232,169), "I’ll take a look.", c["fg"])

    # Progressive work log
    d.line((220,188,220,252), fill=c["line"], width=2)
    steps = [("Read profile",1), ("Inspected repositories",2), ("Checked recent activity",3)]
    ys = [198,224,250]
    for (label, needed), y in zip(steps, ys):
        if stage >= needed:
            check(d, 232, y-2, c["muted"])
            draw_text(d, (252,y), label, c["muted"])
        elif stage == needed - 1 and stage > 0:
            d.ellipse((232,y-5,238,y+1), fill=c["muted"])
            draw_text(d, (252,y), label, c["muted"])

    # Result appears line by line.
    if stage >= 4:
        draw_text(d, (214,292), "4k29", c["fg"])
    if stage >= 5:
        draw_text(d, (214,320), "Student · Vibe coder · Building Tecirc", c["fg"])
    if stage >= 6:
        draw_text(d, (214,348), "Most of the code here was written with ChatGPT.", c["fg"])
    if stage >= 7:
        unfinished = 'The ideas, direction, complaints, and "なんか違'
        draw_text(d, (214,376), unfinished, c["fg"])
        if cursor:
            right = d.textbbox((214,376), unfinished, font=FONT)[2]
            d.rectangle((right+2,362,right+4,380), fill=c["muted"])

    # Limit state
    if stage >= 8:
        rounded(d, (214,404,866,468), 12, c["subtle"], c["line"])
        draw_text(d, (232,431), "Usage limit reached", c["fg"])
        draw_text(d, (232,453), "Try again later.", c["muted"])

    # Composer
    rounded(d, (214,492,866,536), 12, c["panel"], c["line"])
    draw_text(d, (232,520), "Ask anything…", c["muted"])
    if stage >= 8:
        draw_text(d, (848,520), "Limit reached", c["muted"], anchor="rm")

    return image

SEQUENCE = [
    (0, True, 0.35, 700),
    (1, True, 0.65, 600),
    (2, True, 0.85, 600),
    (3, True, 1.00, 700),
    (4, True, 0.70, 500),
    (5, True, 0.70, 500),
    (6, True, 0.70, 650),
    (7, True, 0.70, 500),
    (7, False,0.70, 400),
    (7, True, 0.70, 400),
    (8, True, 0.70, 3200),
]

for theme in ("dark", "light"):
    frames = []
    durations = []
    for stage, cursor, pulse, duration in SEQUENCE:
        frame = make_frame(theme, stage, cursor, pulse)
        frames.append(frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=64))
        durations.append(duration)

    frames[0].save(
        ROOT / f"card-{theme}.gif",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=1,
    )
