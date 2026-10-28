"""Films the Vigi-Track demo in 1080p: kinetic intro, live app walkthrough, kinetic outro, then adds the music.
Needs: playwright (Chromium), ffmpeg, numpy, and `npm install` in this folder for the offline fonts."""
import pathlib, shutil, subprocess
from playwright.sync_api import sync_playwright
from build_preview import build, ROOT

OUT = ROOT / "clips"
FINAL = ROOT.parent / "video" / "Vigi-Track-demo.mp4" if (ROOT.parent / "video").exists() else ROOT.parent / "Vigi-Track-demo.mp4"
import sys as _s
if "--encode-only" not in _s.argv:
    shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir()

APP_FX = r"""
(() => {
  const st=document.createElement('style'); st.textContent=`
  #vt-cap{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(0);z-index:9998;background:#0F1016;color:#fff;border-radius:999px;
    padding:13px 26px;font:700 22px/1.3 "Instrument Sans",system-ui;box-shadow:0 14px 34px rgba(0,0,0,.25);white-space:nowrap;transition:opacity .3s, transform .4s cubic-bezier(.2,.8,.2,1)}
  #vt-cap b{color:#9FA9FF;font-weight:700}
  #vt-cap.hide{opacity:0;transform:translateX(-50%) translateY(20px)}
  #vt-cur{position:fixed;width:26px;height:26px;border-radius:50%;background:rgba(50,71,245,.25);border:3px solid #3247F5;z-index:9997;left:720px;top:420px;
    transform:translate(-50%,-50%);transition:left .65s cubic-bezier(.3,.7,.2,1),top .65s cubic-bezier(.3,.7,.2,1),transform .15s;pointer-events:none}
  #vt-cur.down{transform:translate(-50%,-50%) scale(.6)}`;
  document.head.append(st);
  const cur=document.createElement('div'); cur.id='vt-cur'; document.body.append(cur);
  const cap=document.createElement('div'); cap.id='vt-cap'; cap.className='hide'; document.body.append(cap);
  window.vtCap=t=>{ if(!t){cap.classList.add('hide');return;} cap.classList.add('hide'); setTimeout(()=>{cap.innerHTML=t;cap.classList.remove('hide');},220); };
  window.vtMove=sel=>{ const r=document.querySelector(sel).getBoundingClientRect(); cur.style.left=(r.left+r.width/2)+'px'; cur.style.top=(r.top+r.height/2)+'px'; };
  window.vtPress=()=>{ cur.classList.add('down'); setTimeout(()=>cur.classList.remove('down'),170); };
  window.vtScroll=(sel,offset=80,ms=1100)=>new Promise(res=>{ const y0=scrollY; const el=document.querySelector(sel);
    const y1=Math.max(0,Math.min(el.getBoundingClientRect().top+scrollY-offset, document.documentElement.scrollHeight-innerHeight)); const t0=performance.now();
    const f=t=>{ const p=Math.min(1,(t-t0)/ms), e=p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2; scrollTo(0,y0+(y1-y0)*e); if(p<1) requestAnimationFrame(f); else res(); }; requestAnimationFrame(f); });
  document.documentElement.style.scrollBehavior='auto';
})();
"""

def record(name, fn, viewport, scale):
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport=viewport, device_scale_factor=scale, record_video_dir=str(OUT / name), record_video_size={"width": 1920, "height": 1080})
        pg = ctx.new_page(); fn(pg); ctx.close(); b.close()
    return next((OUT / name).glob("*.webm"))

def film(which):
    def run(pg):
        pg.goto(f"file://{ROOT}/film.html"); pg.wait_for_timeout(700)
        pg.evaluate(f"{which}()")
    return run

def app(pg):
    pg.goto(f"file://{build(with_mock=True)}"); pg.wait_for_timeout(900)
    pg.evaluate(APP_FX)
    W = pg.wait_for_timeout
    cap = lambda t: pg.evaluate("t=>vtCap(t)", t)
    scroll = lambda sel, off=80, ms=1100: pg.evaluate(f"vtScroll('{sel}',{off},{ms})")
    def move(sel, wait=750): pg.evaluate(f"vtMove('{sel}')"); W(wait)
    def click(sel, pause=400): move(sel, 700); pg.evaluate("vtPress()"); pg.click(sel); W(pause)

    cap("This is <b>Vigi-Track</b>."); W(3200)
    scroll("#drugs", 70); cap("Pick a drug. Here, <b>Asmira</b>, an asthma inhaler."); W(700)
    move('.tile[data-d="Zentrolix"]', 600); move('.tile[data-d="Calmarin"]', 500); click('.tile[data-d="Asmira"]', 1800)
    cap("The leaflet already lists these side effects."); move("#leafSummary", 800); click("#leafToggle", 2200); click("#leafToggle", 700)
    cap("One click. <b>The AI reads every review.</b>"); click("#aiLab", 500); click("#run", 300); W(2600)
    scroll("#results", 90, 1200); cap("83% of patients describe a side effect. <b>Two are not in the leaflet.</b>"); W(4200)
    scroll(".acard:nth-child(1)", 80, 900); cap("Every alert comes with <b>the patients’ own words</b>."); move(".acard:nth-child(1) .q:nth-child(1)", 2200); move(".acard:nth-child(1) .stats .stat:nth-child(2)", 2200)
    scroll(".acard:nth-child(2)", 80, 1000); cap("Mood changes. <b>3 patients out of 12.</b> Nobody warned them."); W(3800)
    scroll("#why", 60, 1300); cap("Why AI? Because <b>keywords get fooled.</b>"); W(1500)
    click("#tryText", 200); pg.fill("#tryText", ""); pg.type("#tryText", "No headache at all, but since I started this I have nightmares every night. My cough is much better.", delay=26)
    click("#tryBtn", 1500)
    cap("Keywords see 3 effects. <b>The AI sees the only real one.</b>"); move("#aiList", 3600); move("#agg", 2600)
    scroll("#agent", 80, 1200); cap("Ask the agent. <b>It writes the report for the safety team.</b>"); click("#suggs button:nth-child(1)", 300); W(4800)
    scroll(".bub.ag", 120, 1000); W(6500)
    scroll("#drugs", 70, 1300); cap("Same steps for <b>any drug</b>, even with the full Drugs.com dataset."); click('.tile[data-d="Glucovia"]', 900); click("#run", 300); W(2600)
    scroll("#results", 90, 1100); W(4200)
    cap(""); W(600)

import sys
if "--encode-only" in sys.argv:
    clips = [next((OUT / n).glob("*.webm")) for n in ("intro", "app", "outro")]
else:
  clips = [record("intro", film("intro"), {"width": 1920, "height": 1080}, 1),
         record("app", app, {"width": 1440, "height": 810}, 4 / 3),
         record("outro", film("outro"), {"width": 1920, "height": 1080}, 1)]

def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]).decode())
TRIM = 0.9   # drop page-load frames at the start of each clip
lens = [dur(c) - TRIM for c in clips]
X = 0.5      # crossfade
total = sum(lens) - X * (len(lens) - 1)
subprocess.run(["python3", str(ROOT / "music.py"), str(total + 1), str(ROOT / "music.wav")], check=True)
APPFIT = "crop=1440:810:0:0,scale=1920:1080:flags=lanczos,"   # the app is filmed at 1440x810 CSS px, then scaled to 1080p
fc = "".join(f"[{i}:v]trim=start={TRIM},setpts=PTS-STARTPTS,{APPFIT if i == 1 else ''}fps=30,format=yuv420p[v{i}];" for i in range(3))
fc += f"[v0][v1]xfade=transition=fade:duration={X}:offset={lens[0]-X:.3f}[x1];[x1][v2]xfade=transition=fade:duration={X}:offset={lens[0]+lens[1]-2*X:.3f}[v];"
fc += f"[3:a]loudnorm=I=-18:TP=-1.5:LRA=8,afade=t=out:st={total-4:.2f}:d=4[a]"
cmd = ["ffmpeg", "-y", "-loglevel", "error"] + sum([["-i", str(c)] for c in clips], []) + ["-i", str(ROOT / "music.wav"),
       "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
       "-shortest", "-movflags", "+faststart", str(FINAL)]
subprocess.run(cmd, check=True)
print(FINAL, round(total, 1))
