"""Render the 30 feed posts (1080x1350) and 30 verticals (1080x1920) to ../media as JPEG,
then turn each vertical into a short reel (mp4). Usage: python render.py [day ...]"""
import html, re, subprocess, sys
from datetime import date, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright
from content import DAYS

HERE = Path(__file__).resolve().parent
MEDIA = HERE.parent / "media"
ICONS = HERE / "node_modules/lucide-static/icons"
BRAND = Path("/home/claude/tgaccess/web/static/img/brand")
START = date(2026, 11, 14)

MARK = (BRAND / "tgaccess-icon.svg").read_text()

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:W_px;height:H_px;font-family:Poppins,sans-serif;overflow:hidden;position:relative}
.bg{position:absolute;inset:0}
.light .bg{background:#F3F5FF}
.bold .bg{background:linear-gradient(140deg,#3D8BFF 0%,#5B5CF6 52%,#8B3DF0 100%)}
.dark .bg{background:#0B1136}
.blob{position:absolute;border-radius:50%;filter:blur(90px)}
.light .b1{width:720px;height:720px;right:-260px;top:-240px;background:#8B3DF0;opacity:.22}
.light .b2{width:680px;height:680px;left:-280px;bottom:-260px;background:#3D8BFF;opacity:.24}
.bold .b1{width:760px;height:760px;right:-280px;top:-300px;background:#fff;opacity:.2}
.bold .b2{width:700px;height:700px;left:-300px;bottom:-320px;background:#2A1A9E;opacity:.5}
.dark .b1{width:760px;height:760px;right:-300px;top:-280px;background:#5B5CF6;opacity:.5}
.dark .b2{width:700px;height:700px;left:-320px;bottom:-320px;background:#3D8BFF;opacity:.35}
.ring{position:absolute;border-radius:50%;border:2px solid;opacity:.14}
.light .ring{border-color:#5B5CF6}.bold .ring,.dark .ring{border-color:#fff}
.r1{width:520px;height:520px;right:-170px;bottom:PAD_Bpx}.r2{width:300px;height:300px;right:-60px;bottom:calc(PAD_Bpx + 110px)}
.wrap{position:absolute;gap:0;inset:PAD_Tpx 84px PAD_Bpx 84px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:20px;font-size:46px;font-weight:700;letter-spacing:-.5px}
.logo svg{height:92px;width:92px;display:block;border-radius:22px}
.light .logo b{font-weight:800;background:linear-gradient(90deg,#3D8BFF,#8B3DF0);-webkit-background-clip:text;color:transparent}
.light .logo{color:#0F1B4D}.bold .logo,.dark .logo{color:#fff}
.bold .logo b,.dark .logo b{font-weight:800;color:#FFD34D}
.tag{font-size:25px;font-weight:600;padding:12px 24px;border-radius:99px;letter-spacing:.3px}
.light .tag{background:#fff;color:#5B5CF6;box-shadow:0 6px 20px rgba(60,60,160,.12)}
.bold .tag{background:rgba(255,255,255,.2);color:#fff}
.dark .tag{background:rgba(255,255,255,.1);color:#FFD34D}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center}
.tile{width:150px;height:150px;border-radius:40px;display:flex;align-items:center;justify-content:center;margin-bottom:44px}
.tile svg{width:78px;height:78px;stroke-width:1.9}
.light .tile{background:linear-gradient(140deg,#3D8BFF,#8B3DF0);color:#fff;box-shadow:0 22px 44px rgba(91,92,246,.38)}
.bold .tile{background:#fff;color:#5B5CF6;box-shadow:0 22px 44px rgba(20,10,90,.3)}
.dark .tile{background:linear-gradient(180deg,#FFE27A,#F5A300);color:#0B1136;box-shadow:0 22px 50px rgba(245,163,0,.3)}
h1{font-size:HS_px;line-height:1.1;font-weight:800;letter-spacing:-1.5px}
.light h1{color:#0F1B4D}.bold h1,.dark h1{color:#fff}
.light h1 em{font-style:normal;background:linear-gradient(90deg,#3D8BFF,#8B3DF0);-webkit-background-clip:text;color:transparent}
.bold h1 em,.dark h1 em{font-style:normal;color:#FFD34D}
.sub{font-size:SS_px;line-height:1.42;font-weight:500;margin-top:36px;max-width:860px}
.light .sub{color:#46508A}.bold .sub{color:rgba(255,255,255,.93)}.dark .sub{color:#C5CCF5}
ul{list-style:none;margin-top:44px;display:flex;flex-direction:column;gap:GAP_px}
li{display:flex;align-items:center;gap:24px;font-size:LS_px;line-height:1.3;font-weight:500;color:#1D285F;background:#fff;
   padding:26px 30px;border-radius:26px;box-shadow:0 10px 30px rgba(60,60,160,.1)}
li i{flex:none;width:52px;height:52px;border-radius:50%;background:linear-gradient(140deg,#3D8BFF,#8B3DF0);color:#fff;display:flex;align-items:center;justify-content:center}
li i svg{width:30px;height:30px;stroke-width:3}
.steps li{align-items:center}
.steps li i{width:72px;height:72px;font-style:normal;font-weight:800;font-size:36px;border-radius:22px}
.steps b{display:block;font-size:LS_px;font-weight:700;color:#0F1B4D}
.steps span{display:block;font-size:calc(LS_px - 8px);color:#5A649B;font-weight:500;margin-top:2px}
.tiers{display:grid;grid-template-columns:1fr 1fr;gap:26px;margin-top:48px}
.tier{background:#fff;border-radius:30px;padding:34px 34px 38px;box-shadow:0 10px 30px rgba(60,60,160,.1)}
.tier small{font-size:30px;font-weight:700;color:#5B5CF6}
.tier strong{display:block;font-size:58px;font-weight:800;color:#0F1B4D;letter-spacing:-1px;margin:6px 0 10px}
.tier p{font-size:28px;font-weight:600;color:#46508A}
.tier.max{background:linear-gradient(140deg,#3D8BFF,#8B3DF0)}
.tier.max small{color:#FFD34D}.tier.max strong,.tier.max p{color:#fff}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:40px}
.cell{background:#fff;border-radius:28px;padding:26px 26px 28px;box-shadow:0 10px 30px rgba(60,60,160,.1)}
.cell i{width:62px;height:62px;border-radius:18px;background:linear-gradient(140deg,#3D8BFF,#8B3DF0);color:#fff;display:flex;align-items:center;justify-content:center;margin-bottom:16px}
.cell i svg{width:34px;height:34px;stroke-width:2.2}
.cell b{display:block;font-size:29px;line-height:1.2;font-weight:700;color:#0F1B4D}
.cell span{display:block;font-size:22px;line-height:1.35;font-weight:500;color:#5A649B;margin-top:6px}
.compact h1{font-size:76px}.compact .grid{margin-top:34px;gap:16px}.compact .cell{padding:22px 24px}
.compact .cell i{width:54px;height:54px;margin-bottom:12px}.compact .cell b{font-size:27px}.compact .cell span{font-size:21px}
.foot{display:flex;align-items:center;justify-content:space-between}
.cta{font-size:34px;font-weight:700;padding:22px 44px;border-radius:99px;background:linear-gradient(180deg,#FFE27A,#F5A300);color:#17104F;
     box-shadow:0 14px 30px rgba(245,163,0,.32);display:flex;align-items:center;gap:14px}
.cta svg{width:34px;height:34px;stroke-width:2.6}
.site{font-size:34px;font-weight:700}
.light .site{color:#0F1B4D}.bold .site,.dark .site{color:#fff}
"""

SIZES = {  # format -> (W, H, pad top, pad bottom, headline, sub, list, gap)
    "post": (1080, 1350, 76, 76, 92, 38, 34, 22),
    "vert": (1080, 1920, 250, 330, 100, 42, 37, 28),   # padding keeps clear of the reel/story interface
}


def icon(name):
    svg = (ICONS / f"{name}.svg").read_text()
    return re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()


def headline(text):
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", html.escape(text))


def page(day, fmt):
    w, h, pt, pb, hs, ss, ls, gap = SIZES[fmt]
    lay = day["layout"]
    theme = lay if lay in ("bold", "dark") else "light"
    css = CSS
    for k, v in (("W_", w), ("H_", h), ("PAD_T", pt), ("PAD_B", pb), ("HS_", hs), ("SS_", ss), ("LS_", ls), ("GAP_", gap)):
        css = css.replace(k, str(v))
    body = ("" if day.get("compact") else f'<div class="tile">{icon(day["icon"])}</div>') + f'<h1>{headline(day["h"])}</h1>'
    if "sub" in day:
        body += f'<p class="sub">{html.escape(day["sub"])}</p>'
    if "pts" in day:
        body += "<ul>" + "".join(f'<li><i>{icon("check")}</i>{html.escape(p)}</li>' for p in day["pts"]) + "</ul>"
    if "steps" in day:
        body += '<ul class="steps">' + "".join(
            f'<li><i>{n}</i><div><b>{html.escape(t)}</b><span>{html.escape(s)}</span></div></li>'
            for n, (t, s) in enumerate(day["steps"], 1)) + "</ul>"
    if "grid" in day:
        body += '<div class="grid">' + "".join(
            f'<div class="cell"><i>{icon(ic)}</i><b>{html.escape(t)}</b><span>{html.escape(d)}</span></div>'
            for ic, t, d in day["grid"]) + "</div>"
    if "tiers" in day:
        body += '<div class="tiers">' + "".join(
            f'<div class="tier{" max" if n == "MAX" else ""}"><small>{n}</small><strong>{p}</strong><p>{c}</p></div>'
            for n, p, c in day["tiers"]) + "</div>"
    logo = MARK + "<span><b>TG</b> Access</span>"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head>
<body class="{theme}{' compact' if day.get('compact') else ''}"><div class="bg"></div><div class="blob b1"></div><div class="blob b2"></div>
<div class="ring r1"></div><div class="ring r2"></div>
<div class="wrap"><div class="top"><div class="logo">{logo}</div><div class="tag">{html.escape(day["tag"])}</div></div>
<div class="mid">{body}</div>
<div class="foot"><div class="site">tgaccess.net</div><div class="cta">Start free {icon("arrow-right")}</div></div></div>
</body></html>"""


def names(i):
    d = (START + timedelta(days=i)).isoformat()
    return f"{d}-post.jpg", f"{d}-vertical.jpg", f"{d}-reel.mp4"


def main():
    MEDIA.mkdir(exist_ok=True)
    todo = [int(a) - 1 for a in sys.argv[1:]] or range(len(DAYS))
    with sync_playwright() as p:
        br = p.chromium.launch()
        for i in todo:
            post, vert, reel = names(i)
            for fmt, name in (("post", post), ("vert", vert)):
                w, h = SIZES[fmt][:2]
                pg = br.new_page(viewport={"width": w, "height": h})
                pg.set_content(page(DAYS[i], fmt), wait_until="networkidle")
                over = pg.evaluate("(()=>{const m=document.querySelector('.mid');return m.scrollHeight-m.clientHeight})()")
                if over > 0:
                    raise SystemExit(f"day {i + 1} {fmt}: content overflows by {over}px")
                pg.screenshot(path=str(MEDIA / name), type="jpeg", quality=93)
                pg.close()
            # reel: 8 seconds, slow zoom in, silent audio track so every player accepts it
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(MEDIA / vert),
                            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "8",
                            "-vf", "scale=2160:3840,zoompan=z='1+0.05*on/240':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "20", "-r", "30",
                            "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(MEDIA / reel)], check=True)
            print("day", i + 1, "ok", flush=True)
        br.close()


if __name__ == "__main__":
    main()
