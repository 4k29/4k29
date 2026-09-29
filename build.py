from pathlib import Path

P = Path(__file__).parent
THEMES = {
    "dark": {"bg":"#111315","side":"#171a1d","top":"#15181b","panel":"#1a1d20","line":"#2a2f34","fg":"#e7e9ea","muted":"#8b949e","selected":"#22272b","subtle":"#202428"},
    "light":{"bg":"#ffffff","side":"#f4f5f6","top":"#f8f9fa","panel":"#f3f4f6","line":"#d9dde2","fg":"#22262a","muted":"#6e7781","selected":"#e9ecef","subtle":"#f0f2f4"},
}

def svg(c):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="560" viewBox="0 0 900 560" role="img" aria-labelledby="title desc">
<title id="title">4k29 — agent session</title><desc id="desc">A minimal AI coding-agent inspired GitHub profile for 4k29. The profile generation stops at a fictional usage limit.</desc>
<style>text{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Hiragino Kaku Gothic ProN','Yu Gothic','Noto Sans CJK JP',sans-serif;font-size:14px;fill:{c["fg"]}}}.muted{{fill:{c["muted"]}}}.medium{{font-weight:600}}.mono{{font-family:'SFMono-Regular',Menlo,Consolas,'Liberation Mono',monospace}}</style>
<defs><clipPath id="window"><rect x=".5" y=".5" width="899" height="559" rx="16"/></clipPath></defs><g clip-path="url(#window)">
<rect width="900" height="560" fill="{c["bg"]}"/><rect width="182" height="560" fill="{c["side"]}"/><path d="M182 0V560" stroke="{c["line"]}"/><path d="M0 48H900" stroke="{c["line"]}"/><rect x="182" width="718" height="48" fill="{c["top"]}"/>
<circle cx="22" cy="24" r="5" fill="#ff5f57"/><circle cx="42" cy="24" r="5" fill="#febc2e"/><circle cx="62" cy="24" r="5" fill="#28c840"/><text x="541" y="29" text-anchor="middle" class="muted">4k29 — agent session</text>
<text x="18" y="78" class="muted">Workspace</text><text x="18" y="112" class="medium">4k29</text><rect x="10" y="128" width="162" height="34" rx="8" fill="{c["selected"]}"/><text x="24" y="150" class="medium">GitHub profile</text><text x="24" y="184">Tecirc</text>
<text x="18" y="232" class="muted">Sessions</text><text x="24" y="266">Profile draft</text><text x="24" y="298" class="muted">Tecirc notes</text><text x="18" y="530" class="muted mono">vibe-coding</text>
<rect x="214" y="76" width="652" height="54" rx="12" fill="{c["panel"]}"/><text x="232" y="109">このGitHub、いい感じにしといて。</text>
<circle cx="220" cy="164" r="3" fill="{c["muted"]}"/><text x="232" y="169" class="medium">I’ll take a look.</text>
<path d="M220 188V252" stroke="{c["line"]}" stroke-width="1.5"/>
<path d="m232 193 3 3 6-7" fill="none" stroke="{c["muted"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><text x="252" y="198" class="muted mono">Read profile</text>
<path d="m232 219 3 3 6-7" fill="none" stroke="{c["muted"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><text x="252" y="224" class="muted mono">Inspected repositories</text>
<path d="m232 245 3 3 6-7" fill="none" stroke="{c["muted"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><text x="252" y="250" class="muted mono">Checked recent activity</text>
<text x="214" y="292" class="medium">4k29</text><text x="214" y="320">Student · Vibe coder · Building Tecirc</text><text x="214" y="348">Most of the code here was written with ChatGPT.</text><text x="214" y="376">The ideas, direction, complaints, and &quot;なんか違</text><rect x="545" y="363" width="1.5" height="17" fill="{c["muted"]}"/>
<rect x="214" y="404" width="652" height="64" rx="12" fill="{c["subtle"]}" stroke="{c["line"]}"/><text x="232" y="431" class="medium">Usage limit reached</text><text x="232" y="453" class="muted">Try again later.</text>
<rect x="214" y="492" width="652" height="44" rx="12" fill="{c["panel"]}" stroke="{c["line"]}"/><text x="232" y="520" class="muted">Ask anything…</text><text x="848" y="520" class="muted" text-anchor="end">Limit reached</text>
</g><rect x=".5" y=".5" width="899" height="559" rx="16" fill="none" stroke="{c["line"]}"/></svg>'''

for name, colors in THEMES.items():
    (P / f"card-{name}.svg").write_text(svg(colors), encoding="utf-8")
