from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.extras import router as extras_router

from app.graph import app_graph

app = FastAPI(title="Resume vs JD Matcher")
app.include_router(extras_router)

class MatchRequest(BaseModel):
    resume_text: str
    jd_text: str


@app.post("/match")
def match_resume(request: MatchRequest):
    result = app_graph.invoke({
        "resume_text": request.resume_text,
        "jd_text": request.jd_text,
    })
    return {
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "match_percentage": result["match_percentage"],
        "advice": result["advice"],
    }


PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Resume vs JD Matcher</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#e9edf6; --sheet:#ffffff; --ink:#121a33; --muted:#5b6482; --line:#cfd6e8;
    --cobalt:#2d4bff; --teal:#0e9f84; --amber:#d97a06;
  }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body {
    margin:0; min-height:100vh; color:var(--ink); background:var(--bg);
    font-family:"Bricolage Grotesque", system-ui, -apple-system, "Segoe UI", sans-serif;
    overflow-x:hidden;
  }
  .bg { position:fixed; inset:0; z-index:-1; overflow:hidden; }
  .blob { position:absolute; border-radius:50%; filter:blur(90px); opacity:.55; }
  .b1 { width:480px; height:480px; background:#b9c6ff; top:-120px; left:-80px; animation:drift1 18s ease-in-out infinite alternate; }
  .b2 { width:420px; height:420px; background:#b8f0df; bottom:-140px; right:-60px; animation:drift2 22s ease-in-out infinite alternate; }
  @keyframes drift1 { to { transform:translate(220px,160px) scale(1.15); } }
  @keyframes drift2 { to { transform:translate(-240px,-120px) scale(1.2); } }

  .wrap { max-width:1040px; margin:0 auto; padding:56px 22px 80px; }
  h1 { font-size:clamp(34px,6vw,60px); line-height:1.02; letter-spacing:-.03em; font-weight:800; margin:0 0 14px; }
  .lead { font-size:18px; color:var(--muted); max-width:52ch; margin:0 0 36px; line-height:1.5; }

  .sheets { display:grid; grid-template-columns:1fr 1fr; gap:22px; }
  @media (max-width:760px) { .sheets { grid-template-columns:1fr; } }
  .sheet {
    position:relative; background:var(--sheet); border:1px solid var(--line); border-radius:6px;
    box-shadow:0 1px 0 #fff inset, 0 14px 34px -18px rgba(18,26,51,.35);
    overflow:hidden; transition:box-shadow .25s, transform .25s;
  }
  .sheet:focus-within { box-shadow:0 0 0 2px var(--cobalt), 0 18px 40px -18px rgba(45,75,255,.45); transform:translateY(-2px); }
  .sheet.l { animation:inL .8s cubic-bezier(.2,.8,.2,1) both; }
  .sheet.r { animation:inR .8s cubic-bezier(.2,.8,.2,1) both; }
  @keyframes inL { from { opacity:0; transform:translateX(-60px) rotate(-1.5deg); } }
  @keyframes inR { from { opacity:0; transform:translateX(60px) rotate(1.5deg); } }
  .sheet header { display:flex; justify-content:space-between; align-items:baseline; padding:14px 18px 0; }
  .sheet header b { font-size:17px; }
  .sheet header span { font-size:13px; color:var(--muted); font-variant-numeric:tabular-nums; }
  textarea {
    display:block; width:100%; height:290px; border:0; outline:0; resize:vertical; background:transparent;
    padding:12px 18px 18px; font:inherit; font-size:15px; line-height:1.6; color:var(--ink);
    background-image:repeating-linear-gradient(transparent, transparent 23px, #eef1f8 24px);
    background-attachment:local;
  }
  textarea::placeholder { color:#9aa3bd; }
  .beam {
    position:absolute; left:0; right:0; top:0; height:70px; pointer-events:none; opacity:0;
    background:linear-gradient(to bottom, rgba(45,75,255,0), rgba(45,75,255,.22) 80%, rgba(45,75,255,.9));
    border-bottom:2px solid var(--cobalt);
  }
  .scanning .beam { opacity:1; animation:scan 1.6s ease-in-out infinite; }
  .scanning .sheet.r .beam { animation-delay:.35s; }
  @keyframes scan { 0% { transform:translateY(-70px); } 100% { transform:translateY(420px); } }

  .actions { display:flex; gap:14px; align-items:center; margin-top:24px; flex-wrap:wrap; }
  .go {
    position:relative; overflow:hidden; border:0; cursor:pointer; border-radius:999px;
    background:var(--ink); color:#fff; font:inherit; font-weight:600; font-size:16px; padding:15px 30px;
    transition:transform .2s, box-shadow .2s, background .3s;
  }
  .go:hover { transform:translateY(-2px); box-shadow:0 14px 26px -12px rgba(18,26,51,.7); background:var(--cobalt); }
  .go::after {
    content:""; position:absolute; top:0; bottom:0; width:60px; left:-80px; transform:skewX(-20deg);
    background:rgba(255,255,255,.28); animation:shine 3.2s ease-in-out infinite;
  }
  @keyframes shine { 0%,60% { left:-80px; } 100% { left:130%; } }
  .go:disabled { cursor:progress; opacity:.85; }
  .ghost { border:0; background:none; cursor:pointer; font:inherit; font-size:15px; color:var(--muted); text-decoration:underline; text-underline-offset:4px; padding:8px; }
  .ghost:hover { color:var(--ink); }
  button:focus-visible { outline:3px solid var(--cobalt); outline-offset:3px; }

  .status { margin-top:18px; min-height:24px; color:var(--cobalt); font-weight:600; }
  .status.err { color:#c62828; white-space:pre-wrap; font-weight:500; }
  .dots i { display:inline-block; width:6px; height:6px; margin-left:4px; border-radius:50%; background:currentColor; animation:bounce 1s infinite; }
  .dots i:nth-child(2) { animation-delay:.15s; } .dots i:nth-child(3) { animation-delay:.3s; }
  @keyframes bounce { 50% { transform:translateY(-6px); opacity:.4; } }

  #out { display:none; margin-top:40px; }
  #out.show { display:block; }
  .score { display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }
  .num { font-size:clamp(76px,16vw,150px); line-height:.9; font-weight:800; letter-spacing:-.05em; font-variant-numeric:tabular-nums; }
  .score .u { font-size:36px; font-weight:600; color:var(--muted); }
  .verdict { font-size:20px; font-weight:600; }
  .track { height:14px; margin:20px 0 34px; background:#d9dff0; border-radius:999px; overflow:hidden; }
  .track i { display:block; height:100%; width:0; border-radius:999px; background:var(--teal); transition:width 1.8s cubic-bezier(.2,.8,.2,1), background .4s; }
  .cols { display:grid; grid-template-columns:1fr 1fr; gap:34px; }
  @media (max-width:760px) { .cols { grid-template-columns:1fr; gap:24px; } }
  h3 { margin:0 0 12px; font-size:19px; }
  .chips { display:flex; flex-wrap:wrap; gap:8px; }
  .chip { padding:7px 14px; border-radius:999px; font-size:14px; font-weight:600; animation:pop .5s cubic-bezier(.3,1.6,.5,1) both; }
  .chip.ok { background:#d4f3ea; color:#08705d; }
  .chip.no { background:#fbe6c8; color:#8f4f02; }
  .none { color:var(--muted); }
  @keyframes pop { from { opacity:0; transform:scale(.3) translateY(14px); } }
  .note { margin-top:34px; background:var(--sheet); border:1px solid var(--line); border-left:5px solid var(--cobalt); border-radius:6px; padding:20px 24px; }
  .note p { margin:0; line-height:1.65; font-size:16px; white-space:pre-wrap; max-width:75ch; }
  .typing::after { content:""; display:inline-block; width:2px; height:1.1em; margin-left:2px; vertical-align:-3px; background:var(--cobalt); animation:blink .8s steps(2) infinite; }
  @keyframes blink { 50% { opacity:0; } }
  @media (prefers-reduced-motion:reduce) { *, *::before, *::after { animation:none !important; transition:none !important; } }
</style>
</head>
<body>
<div class="bg"><div class="blob b1"></div><div class="blob b2"></div></div>
<main class="wrap" id="app">
  <h1>Resume tera,<br>job ki zarurat se kitna milta hai?</h1>
  <p class="lead">Resume aur job description paste kar. Skills match hoti hain ya nahi, aur kya sudharna hai, sab dikh jayega.</p>

  <div class="sheets">
    <div class="sheet l">
      <header><b>Resume</b><span id="c1">0 characters</span></header>
      <textarea id="resume" placeholder="Apna resume yahan paste kar..."></textarea>
      <div class="beam"></div>
    </div>
    <div class="sheet r">
      <header><b>Job description</b><span id="c2">0 characters</span></header>
      <textarea id="jd" placeholder="Job description yahan paste kar..."></textarea>
      <div class="beam"></div>
    </div>
  </div>

  <div class="actions">
    <button class="go" id="btn">Match check karo</button>
    <button class="ghost" id="sample" type="button">Example daalo</button>
  </div>
  <div class="status" id="status" role="status"></div>

  <section id="out" aria-live="polite">
    <div class="score"><span class="num" id="num">0</span><span class="u">%</span><span class="verdict" id="verdict"></span></div>
    <div class="track"><i id="fill"></i></div>
    <div class="cols">
      <div><h3>Skills jo mil gayi</h3><div class="chips" id="matched"></div></div>
      <div><h3>Jo resume mein nahi hai</h3><div class="chips" id="missing"></div></div>
    </div>
    <div class="note"><h3>Kya sudharna hai</h3><p id="advice"></p></div>
  </section>
</main>
<script>
  const $ = function (id) { return document.getElementById(id); };
  const app = $("app"), btn = $("btn"), statusBox = $("status"), out = $("out");
  const steps = ["Resume padh raha hu", "Skills nikal raha hu", "Job description se compare kar raha hu", "Advice bana raha hu"];
  let stepTimer, typeTimer;

  function count(id, ta) { $(ta).addEventListener("input", function () { $(id).textContent = $(ta).value.length + " characters"; }); }
  count("c1", "resume"); count("c2", "jd");

  $("sample").addEventListener("click", function () {
    $("resume").value = "Python developer with 2 years of experience building REST APIs with FastAPI and Flask. Skills: Python, SQL, PostgreSQL, FastAPI, Git, Linux.";
    $("jd").value = "We are hiring a backend developer. Required: Python, SQL, FastAPI, Docker, AWS and CI/CD. Nice to have: Kubernetes.";
    $("resume").dispatchEvent(new Event("input")); $("jd").dispatchEvent(new Event("input"));
  });

  function startLoading() {
    app.classList.add("scanning");
    let i = 0;
    statusBox.className = "status";
    statusBox.innerHTML = steps[0] + '<span class="dots"><i></i><i></i><i></i></span>';
    stepTimer = setInterval(function () {
      i = (i + 1) % steps.length;
      statusBox.innerHTML = steps[i] + '<span class="dots"><i></i><i></i><i></i></span>';
    }, 1500);
  }
  function stopLoading() { app.classList.remove("scanning"); clearInterval(stepTimer); statusBox.textContent = ""; }

  function chips(el, items, cls, empty) {
    el.innerHTML = "";
    if (!items || !items.length) { const p = document.createElement("span"); p.className = "none"; p.textContent = empty; el.appendChild(p); return; }
    items.forEach(function (s, i) {
      const c = document.createElement("span");
      c.className = "chip " + cls; c.style.animationDelay = (0.9 + i * 0.08) + "s"; c.textContent = s;
      el.appendChild(c);
    });
  }
  function countUp(to) {
    const el = $("num"), t0 = performance.now(), dur = 1800;
    (function tick(now) {
      const p = Math.min((now - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(to * e);
      if (p < 1) requestAnimationFrame(tick);
    })(t0);
  }
  function typeText(el, text) {
    clearInterval(typeTimer); el.textContent = ""; el.classList.add("typing"); let i = 0;
    typeTimer = setInterval(function () {
      el.textContent += text.slice(i, i + 2); i += 2;
      if (i >= text.length) { clearInterval(typeTimer); el.classList.remove("typing"); }
    }, 16);
  }
  function show(data) {
    let v = Number(data.match_percentage) || 0;
    if (v > 0 && v <= 1 && !Number.isInteger(v)) v = v * 100;
    v = Math.max(0, Math.min(100, Math.round(v)));
    out.classList.remove("show"); void out.offsetWidth; out.classList.add("show");
    const fill = $("fill");
    fill.style.width = "0"; fill.style.background = v >= 70 ? "var(--teal)" : v >= 40 ? "var(--amber)" : "#d64545";
    $("verdict").textContent = v >= 75 ? "Kaafi strong match" : v >= 50 ? "Thoda aur kaam chahiye" : "Abhi match kam hai";
    chips($("matched"), data.matched_skills, "ok", "Koi skill match nahi hui.");
    chips($("missing"), data.missing_skills, "no", "Kuch missing nahi, badhiya!");
    requestAnimationFrame(function () { fill.style.width = v + "%"; });
    countUp(v);
    typeText($("advice"), data.advice || "Koi advice nahi mili.");
    setTimeout(function () { out.scrollIntoView({ behavior: "smooth", block: "start" }); }, 150);
  }

  btn.addEventListener("click", async function () {
    const resume = $("resume").value.trim(), jd = $("jd").value.trim();
    if (!resume || !jd) { statusBox.className = "status err"; statusBox.textContent = "Resume aur job description dono bhar, phir dobara try kar."; return; }
    btn.disabled = true; out.classList.remove("show"); startLoading();
    try {
      const res = await fetch("/match", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resume_text: resume, jd_text: jd }) });
      if (!res.ok) throw new Error("Server ne error diya (" + res.status + "). Terminal ke logs check kar.");
      const data = await res.json();
      stopLoading(); show(data);
    } catch (e) {
      stopLoading(); statusBox.className = "status err"; statusBox.textContent = String(e.message || e);
    } finally { btn.disabled = false; }
  });
</script>
<script src="/extras.js"></script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE
