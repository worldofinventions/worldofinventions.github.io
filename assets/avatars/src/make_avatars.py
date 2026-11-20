"""Builds the two bot avatars (640x640 PNG) from one SVG template with headless Chrome.
Run from the project root:  python assets/avatars/src/make_avatars.py
Same composition for both bots (blueprint disc, brass ring, engraved bulb-globe);
the colour of the disc and the caption tell them apart."""
import math, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "assets" / "avatars"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
F = lambda p: (ROOT / p).as_uri()
FONTS = f"""
@font-face {{ font-family: Fraunces; src: url({F('site/node_modules/@fontsource-variable/fraunces/files/fraunces-latin-full-normal.woff2')}); font-weight: 100 900; }}
@font-face {{ font-family: Literata; src: url({F('ru/miniapp/ui/node_modules/@fontsource-variable/literata/files/literata-cyrillic-opsz-normal.woff2')}); font-weight: 200 900; }}
@font-face {{ font-family: Plex; src: url({F('ru/miniapp/ui/node_modules/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2')}); }}
@font-face {{ font-family: PlexCyr; src: url({F('ru/miniapp/ui/node_modules/@fontsource/ibm-plex-mono/files/ibm-plex-mono-cyrillic-500-normal.woff2')}); }}
"""

def bulb(ink: str, hi: str) -> str:
    cx, cy, r = 320, 282, 112
    parts = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{ink}" stroke-width="7"/>']
    # engraved globe inside the bulb: parallels and meridians
    for k in (-2, -1, 0, 1, 2):
        y = cy + k * r * 0.36
        half = math.sqrt(max(r * r - (y - cy) ** 2, 0))
        parts.append(f'<line x1="{cx-half+6:.1f}" y1="{y:.1f}" x2="{cx+half-6:.1f}" y2="{y:.1f}" stroke="{ink}" stroke-width="2.4" opacity="0.75"/>')
    for rx in (0.33, 0.7):
        parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r*rx:.1f}" ry="{r-4}" fill="none" stroke="{ink}" stroke-width="2.4" opacity="0.75"/>')
    parts.append(f'<line x1="{cx}" y1="{cy-r+4}" x2="{cx}" y2="{cy+r-4}" stroke="{ink}" stroke-width="2.4" opacity="0.75"/>')
    # filament: the one warm line, like the site's blueprint highlight
    parts.append(f'<path d="M {cx-30} {cy+150} L {cx-30} {cy+40} Q {cx-30} {cy+10} {cx-12} {cy+22} Q {cx} {cy-14} {cx+12} {cy+22} Q {cx+30} {cy+10} {cx+30} {cy+40} L {cx+30} {cy+150}" fill="none" stroke="{hi}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    # neck and screw base
    parts.append(f'<path d="M {cx-62} {cy+92} Q {cx-50} {cy+128} {cx-50} {cy+150} L {cx+50} {cy+150} Q {cx+50} {cy+128} {cx+62} {cy+92}" fill="none" stroke="{ink}" stroke-width="7" stroke-linejoin="round"/>')
    for i, w in enumerate((56, 52, 48, 44)):
        y = cy + 164 + i * 15
        parts.append(f'<rect x="{cx-w}" y="{y-5}" width="{2*w}" height="10" rx="5" fill="{ink}"/>')
    parts.append(f'<path d="M {cx-28} {cy+220} L {cx+28} {cy+220} L {cx+14} {cy+236} L {cx-14} {cy+236} Z" fill="{ink}"/>')
    return "\n".join(parts)

def svg(bg: str, title: str, title_font: str, tag: str, tag_font: str) -> str:
    ink, brass, hi = "#f2ebdb", "#d2ab57", "#ffd27a"
    grid = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="640" /><line x1="0" y1="{x}" x2="640" y2="{x}" />' for x in range(0, 641, 32))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="640" viewBox="0 0 640 640">
<defs>
  <path id="top" d="M 92 320 A 228 228 0 0 1 548 320"/>
  <path id="bottom" d="M 70 320 A 250 250 0 0 0 570 320"/>
</defs>
<rect width="640" height="640" fill="{bg}"/>
<g stroke="{ink}" stroke-opacity="0.07" stroke-width="1">{grid}</g>
<circle cx="320" cy="320" r="292" fill="none" stroke="{brass}" stroke-width="5"/>
<circle cx="320" cy="320" r="278" fill="none" stroke="{brass}" stroke-width="1.6" opacity="0.8"/>
{bulb(ink, hi)}
<text font-family="{title_font}" font-size="35" font-weight="560" letter-spacing="3" fill="{ink}" text-anchor="middle"><textPath href="#top" startOffset="50%">{title}</textPath></text>
<text font-family="{tag_font}" font-size="26" letter-spacing="9" fill="{brass}" text-anchor="middle"><textPath href="#bottom" startOffset="50%" dominant-baseline="hanging">{tag}</textPath></text>
</svg>"""

def render(name: str, markup: str) -> None:
    html = OUT / "src" / f"{name}.html"
    html.write_text(f"<!doctype html><meta charset=utf-8><style>{FONTS} html,body{{margin:0;background:#000}} svg{{display:block}}</style>{markup}", encoding="utf-8")
    (OUT / "src" / f"{name}.svg").write_text(markup, encoding="utf-8")
    png = OUT / f"{name}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    "--force-device-scale-factor=1", "--window-size=640,640", "--virtual-time-budget=3000",
                    f"--screenshot={png}", html.as_uri()], check=True, capture_output=True)
    print("wrote", png)

render("world-global", svg("#12294a", "WORLD OF INVENTIONS", "Fraunces", "GLOBAL", "Plex"))
render("world-russia", svg("#5a2210", "МИР ИЗОБРЕТЕНИЙ", "Literata", "РОССИЯ", "PlexCyr"))
