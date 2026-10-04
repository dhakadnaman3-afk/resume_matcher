import io
import os
import time
from collections import defaultdict, deque

from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from langchain_groq import ChatGroq
from pydantic import BaseModel

load_dotenv()

router = APIRouter()

MAX_TEXT = 8000              # resume / JD ke liye max characters
MAX_FILE = 5 * 1024 * 1024   # upload ka max size (5 MB)
RATE_LIMIT, RATE_WINDOW = 12, 600   # 10 minute mein max 12 requests per user
_hits = defaultdict(deque)


def _check_rate(request: Request):
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    ip = ip or (request.client.host if request.client else "unknown")
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        raise HTTPException(429, "Bahut zyada requests ho gayi. 10 minute baad dobara try kar.")
    q.append(now)


def _llm():
    # agents.py mein jo model use ho raha hai, wahi naam .env mein GROQ_MODEL ke roop mein daal
    return ChatGroq(model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), temperature=0.4)


PROMPTS = {
    "improve": (
        "You are a career coach. Below are a resume and a job description.\n"
        "Pick the 5 weakest or least relevant bullet points in the resume and rewrite each one "
        "to fit this job better. Use ONLY facts already present in the resume, never invent "
        "experience, numbers or tools. Format each as:\nBefore: ...\nAfter: ...\nWhy: ...\n\n"
        "RESUME:\n{resume}\n\nJOB DESCRIPTION:\n{jd}"
    ),
    "interview": (
        "You are an interviewer for the job below. Write 8 likely interview questions for this "
        "candidate, mixing technical and behavioural, focusing on skills the job needs. "
        "After each question add one short line on what the interviewer is checking.\n\n"
        "RESUME:\n{resume}\n\nJOB DESCRIPTION:\n{jd}"
    ),
    "cover": (
        "Write a professional cover letter under 250 words for this job. Use only facts from the "
        "resume, do not invent anything. Highlight the skills that match the job description. "
        "End with a polite closing.\n\nRESUME:\n{resume}\n\nJOB DESCRIPTION:\n{jd}"
    ),
    "roadmap": (
        "Find the skills the job description asks for that the resume does not show. For each "
        "missing skill give: why it matters for this job, a realistic time to learn the basics, "
        "and one hands-on mini project to practice. Order them by importance. "
        "Use simple English.\n\nRESUME:\n{resume}\n\nJOB DESCRIPTION:\n{jd}"
    ),
}


class GenReq(BaseModel):
    kind: str
    resume_text: str
    jd_text: str


@router.post("/extract")
async def extract(request: Request, file: UploadFile = File(...)):
    _check_rate(request)
    data = await file.read()
    if len(data) > MAX_FILE:
        raise HTTPException(413, "File 5 MB se badi hai.")
    name = (file.filename or "").lower()
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
        elif name.endswith(".docx"):
            from docx import Document
            text = "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
        elif name.endswith(".txt"):
            text = data.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(400, "Sirf PDF, DOCX ya TXT file chalegi.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "File padh nahi payi. Dusri file try kar.")
    text = text.strip()
    if not text:
        raise HTTPException(400, "File mein text nahi mila. Scanned PDF ho sakti hai, text copy karke paste kar.")
    return {"text": text[:MAX_TEXT]}


@router.post("/generate")
def generate(req: GenReq, request: Request):
    _check_rate(request)
    if req.kind not in PROMPTS:
        raise HTTPException(400, "Galat option.")
    if not req.resume_text.strip() or not req.jd_text.strip():
        raise HTTPException(400, "Resume aur job description dono chahiye.")
    if len(req.resume_text) > MAX_TEXT or len(req.jd_text) > MAX_TEXT:
        raise HTTPException(413, "Text bahut lamba hai. Har box mein 8000 characters tak daal.")
    try:
        reply = _llm().invoke(PROMPTS[req.kind].format(resume=req.resume_text, jd=req.jd_text))
    except Exception:
        raise HTTPException(502, "AI se jawab nahi aaya. GROQ_API_KEY aur GROQ_MODEL check kar.")
    return {"text": reply.content}


EXTRAS_JS = r"""
(function () {
  const $ = function (id) { return document.getElementById(id); };
  const css = `
    .up { cursor:pointer; color:var(--cobalt); font-size:13px; font-weight:600; text-decoration:underline; text-underline-offset:3px; }
    .tools { margin-top:60px; padding-top:30px; border-top:1px solid var(--line); }
    .tools h2 { margin:0 0 16px; font-size:28px; letter-spacing:-.02em; }
    .tabs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px; }
    .tab { border:1px solid var(--line); background:var(--sheet); border-radius:999px; padding:9px 18px; font:inherit; font-size:15px; cursor:pointer; transition:background .2s, color .2s, transform .2s; }
    .tab:hover { transform:translateY(-2px); }
    .tab.on { background:var(--cobalt); border-color:var(--cobalt); color:#fff; }
    .tbox { display:none; margin-top:22px; background:var(--sheet); border:1px solid var(--line); border-radius:6px; padding:20px 24px; line-height:1.65; white-space:pre-wrap; animation:boxin .5s ease both; }
    .tbox.show { display:block; }
    .tbox.err { color:#c62828; }
    .copy { margin-top:14px; }
    @keyframes boxin { from { opacity:0; transform:translateY(16px); } }
    @media print {
      .bg, .sheets, .actions, .status, .tabs, #gen, .copy, .lead { display:none !important; }
      body { background:#fff; } .wrap { padding:0; }
    }
  `;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  function setStatus(msg, isErr) { const s = $("status"); s.className = "status" + (isErr ? " err" : ""); s.textContent = msg; }

  // 1) PDF / Word upload har sheet pe
  document.querySelectorAll(".sheet").forEach(function (sheet) {
    const ta = sheet.querySelector("textarea");
    const label = document.createElement("label");
    label.className = "up"; label.textContent = "PDF / Word upload";
    const input = document.createElement("input");
    input.type = "file"; input.accept = ".pdf,.docx,.txt"; input.hidden = true;
    label.appendChild(input);
    const head = sheet.querySelector("header");
    head.insertBefore(label, head.querySelector("span"));
    input.addEventListener("change", async function () {
      const f = input.files[0]; if (!f) return;
      label.firstChild.nodeValue = "Padh raha hu...";
      const fd = new FormData(); fd.append("file", f);
      try {
        const res = await fetch("/extract", { method: "POST", body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Upload nahi hua.");
        ta.value = data.text; ta.dispatchEvent(new Event("input")); setStatus("");
      } catch (e) { setStatus(e.message, true); }
      label.firstChild.nodeValue = "PDF / Word upload"; input.value = "";
    });
  });

  // 2) Report PDF save (browser print)
  const pdfBtn = document.createElement("button");
  pdfBtn.className = "ghost"; pdfBtn.type = "button"; pdfBtn.textContent = "Report PDF save karo";
  pdfBtn.addEventListener("click", function () { window.print(); });
  document.querySelector(".actions").appendChild(pdfBtn);

  // 3) Aur tools: resume sudharo, interview, cover letter, roadmap
  const tools = [["improve", "Resume sudharo"], ["interview", "Interview questions"], ["cover", "Cover letter"], ["roadmap", "Seekhne ka plan"]];
  let kind = "improve";
  const sec = document.createElement("section");
  sec.className = "tools";
  sec.innerHTML = '<h2>Iske baad kya karna hai?</h2><div class="tabs"></div><button class="go" id="gen" type="button">Banao</button><div class="tbox" id="tbox"></div>';
  $("app").appendChild(sec);
  const tabs = sec.querySelector(".tabs");
  tools.forEach(function (t) {
    const b = document.createElement("button");
    b.className = "tab" + (t[0] === kind ? " on" : ""); b.type = "button"; b.textContent = t[1];
    b.addEventListener("click", function () {
      kind = t[0];
      tabs.querySelectorAll(".tab").forEach(function (x) { x.classList.remove("on"); });
      b.classList.add("on"); $("tbox").classList.remove("show");
    });
    tabs.appendChild(b);
  });

  $("gen").addEventListener("click", async function () {
    const resume = $("resume").value.trim(), jd = $("jd").value.trim(), box = $("tbox"), gen = $("gen");
    box.className = "tbox show"; box.textContent = "";
    if (!resume || !jd) { box.classList.add("err"); box.textContent = "Upar resume aur job description dono bhar, phir dobara try kar."; return; }
    gen.disabled = true; gen.textContent = "Bana raha hu...";
    try {
      const res = await fetch("/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ kind: kind, resume_text: resume, jd_text: jd }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kuch gadbad hui.");
      box.textContent = data.text;
      const copy = document.createElement("button");
      copy.className = "ghost copy"; copy.type = "button"; copy.textContent = "Copy karo";
      copy.addEventListener("click", function () { navigator.clipboard.writeText(data.text); copy.textContent = "Copy ho gaya"; });
      box.appendChild(document.createElement("br")); box.appendChild(copy);
    } catch (e) { box.classList.add("err"); box.textContent = String(e.message || e); }
    gen.disabled = false; gen.textContent = "Banao";
  });
})();
"""


@router.get("/extras.js")
def extras_js():
    return Response(EXTRAS_JS, media_type="application/javascript")
