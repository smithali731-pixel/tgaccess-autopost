"""For each video: a vertical 1080x1920 reel (branded frame, video centered) for Instagram,
and the original landscape file for Facebook."""
import html, re, shutil, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
import render
from videos import VIDEOS

SRC = Path("/mnt/user-data/uploads/tgaccess videos")
MEDIA = render.MEDIA
FRAME = """<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:Poppins,sans-serif;overflow:hidden;position:relative;background:#0B1136}
.blob{position:absolute;border-radius:50%;filter:blur(90px)}
.b1{width:800px;height:800px;right:-300px;top:-260px;background:#5B5CF6;opacity:.55}
.b2{width:760px;height:760px;left:-320px;bottom:-300px;background:#3D8BFF;opacity:.4}
.top{position:absolute;left:84px;right:84px;top:250px}
.logo{display:flex;align-items:center;gap:20px;font-size:46px;font-weight:700;color:#fff}
.logo svg{width:92px;height:92px;border-radius:22px}.logo b{color:#FFD34D;font-weight:800}
.tag{display:inline-block;margin-top:70px;font-size:28px;font-weight:600;padding:12px 26px;border-radius:99px;background:rgba(255,255,255,.1);color:#FFD34D}
h1{margin-top:26px;font-size:76px;line-height:1.1;font-weight:800;color:#fff;letter-spacing:-1px}
h1 em{font-style:normal;color:#FFD34D}
.hole{position:absolute;left:0;top:780px;width:1080px;height:608px;background:#000}
.foot{position:absolute;left:84px;right:84px;bottom:330px;display:flex;justify-content:space-between;align-items:center}
.site{font-size:36px;font-weight:700;color:#fff}
.cta{font-size:34px;font-weight:700;padding:22px 44px;border-radius:99px;background:linear-gradient(180deg,#FFE27A,#F5A300);color:#17104F}
</style></head><body><div class="blob b1"></div><div class="blob b2"></div>
<div class="top"><div class="logo">LOGO<span><b>TG</b> Access</span></div><div class="tag">Tutorial</div><h1>TITLE</h1></div>
<div class="hole"></div><div class="foot"><div class="site">tgaccess.net</div><div class="cta">Start free</div></div></body></html>"""

def main():
    with sync_playwright() as p:
        br = p.chromium.launch()
        for i, (src, slug, title, _) in enumerate(VIDEOS, 1):
            name = f"video-{i:02d}-{slug}"
            png = Path(f"/tmp/{name}.png")
            pg = br.new_page(viewport={"width": 1080, "height": 1920})
            t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html.escape(title))
            pg.set_content(FRAME.replace("LOGO", render.MARK).replace("TITLE", t), wait_until="networkidle")
            pg.screenshot(path=str(png)); pg.close()
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(SRC / src),
                "-filter_complex", "[1:v]scale=1080:608,setsar=1[v];[0:v][v]overlay=0:780:shortest=1,fps=30,format=yuv420p[o]",
                "-map", "[o]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-profile:v", "high",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", str(MEDIA / f"{name}-reel.mp4")], check=True)
            shutil.copyfile(SRC / src, MEDIA / f"{name}-landscape.mp4")
            print(i, name, flush=True)
        br.close()

if __name__ == "__main__":
    main()
