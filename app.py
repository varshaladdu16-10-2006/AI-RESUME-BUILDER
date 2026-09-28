import base64
import html
import json
import re
from collections import Counter

import ollama
import pandas as pd
import streamlit as st

st.set_page_config(page_title="ResumeAI Studio", page_icon="🌈", layout="wide")

# ============================================================ DATA
THEMES = {
    "Aurora": ("#2563eb", "#7c3aed"),
    "Ocean": ("#0369a1", "#2563eb"),
    "Sunset": ("#b45309", "#be123c"),
    "Forest": ("#047857", "#0f766e"),
    "Royal": ("#3730a3", "#6d28d9"),
    "Berry": ("#9d174d", "#6d28d9"),
    "Gold": ("#a16207", "#92400e"),
    "Slate": ("#334155", "#475569"),
}

COLS = {
    "exp": ["Role", "Company", "Dates", "What you did"],
    "intern": ["Role", "Company", "Dates", "What you did"],
    "edu": ["Degree", "School", "Year", "Grade / CGPA"],
    "proj": ["Project", "Tech used", "Link", "What it does"],
    "award": ["Scholarship / Award", "Provider", "Year"],
    "cert": ["Certificate", "Issuer", "Year"],
    "vol": ["Role", "Organisation", "Details"],
    "lang": ["Language", "Level"],
}

SECTIONS = [
    ("profile", "Profile"), ("exp", "Experience"), ("intern", "Internships"), ("proj", "Projects"),
    ("edu", "Education"), ("award", "Scholarships & Awards"), ("skills", "Skills"),
    ("cert", "Certifications"), ("vol", "Volunteering & Activities"), ("lang", "Languages"),
]

FIELDS = ["p_name", "p_title", "p_email", "p_phone", "p_loc", "p_links", "p_summary", "p_skills", "p_jd"]

SAMPLE_FIELDS = {
    "p_name": "Priya Sharma", "p_title": "Frontend Developer", "p_email": "priya@email.com",
    "p_phone": "+91 98765 43210", "p_loc": "Hyderabad, India", "p_links": "linkedin.com/in/priya · github.com/priya",
    "p_summary": "Web developer who likes clean UI and learns fast.",
    "p_skills": "HTML, CSS, JavaScript, React, Git, Figma",
    "p_jd": "We need a Frontend Developer with React, JavaScript, responsive design, REST APIs, Git and good communication skills.",
}
SAMPLE_TABLES = {
    "exp": [["Junior Developer", "TechNova", "2023 – Present", "Built responsive website pages, fixed bugs, worked with designers"]],
    "intern": [["Web Development Intern", "BrightSoft", "May 2022 – Jul 2022", "Built a landing page in React and learned the Git workflow"]],
    "edu": [["B.Tech Computer Science", "Osmania University", "2019 – 2023", "8.4 CGPA"]],
    "proj": [["Portfolio Website", "React, CSS", "github.com/priya/portfolio", "Personal portfolio with dark mode"],
             ["Weather App", "JavaScript, REST API", "", "Shows live weather from a public API"]],
    "award": [["Merit Scholarship", "Osmania University", "2021"], ["Google Developer Scholarship", "Google", "2022"]],
    "cert": [["Meta Front-End Developer Certificate", "Coursera", "2023"]],
    "vol": [["Tech Club Volunteer", "Osmania Coding Club", "Organised weekend coding workshops for juniors"]],
    "lang": [["English", "Fluent"], ["Telugu", "Native"], ["Hindi", "Fluent"]],
}

# ============================================================ CSS
RESUME_CSS = """
.rs{--a:#6d5dfc;--b:#ec4899;background:#fff;color:#1f2937;font-family:Inter,Arial,sans-serif;font-size:13.5px;line-height:1.55;
border-radius:16px;overflow:hidden;box-shadow:0 20px 60px rgba(30,27,75,.2);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.rs .nm{font-size:31px;font-weight:800;letter-spacing:-.01em;line-height:1.15}
.rs .role{font-size:15px;font-weight:500;margin-top:4px}
.rs .ct{display:flex;flex-wrap:wrap;gap:4px 18px;margin-top:12px;font-size:12.5px}
.rs .hd{margin:20px 0 9px;font-size:11.5px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--a);
position:relative;padding-bottom:6px}
.rs .hd::after{content:"";position:absolute;left:0;bottom:0;width:100%;height:2px;background:linear-gradient(90deg,var(--a),var(--b),transparent)}
.rs .e{margin-bottom:12px}
.rs .eh{display:flex;justify-content:space-between;gap:10px}
.rs .eh b{font-size:14.5px}
.rs .eh span,.rs .co{color:#6b7280;font-size:12.5px}
.rs .dt{font-size:13px;color:#374151}
.rs ul{margin:5px 0 0;padding-left:19px}
.rs li{margin-bottom:2px}
.rs .chips{display:flex;flex-wrap:wrap;gap:6px}
.rs .chips i{font-style:normal;font-size:12px;font-weight:600;padding:3px 11px;border-radius:99px;
background:color-mix(in srgb,var(--a) 12%,#fff);color:var(--a)}
.rs .ph{width:92px;height:92px;border-radius:50%;object-fit:cover;border:3px solid rgba(255,255,255,.75);flex-shrink:0}
/* Modern */
.t-modern .top{display:flex;align-items:center;gap:22px;background:linear-gradient(135deg,var(--a),var(--b));color:#fff;padding:32px 38px}
.t-modern .body{padding:10px 38px 34px}
.t-modern .e{border-left:3px solid color-mix(in srgb,var(--a) 40%,#fff);padding-left:12px}
.t-modern .chips i:nth-child(5n+1){background:#ede9fe;color:#6d28d9}
.t-modern .chips i:nth-child(5n+2){background:#fce7f3;color:#be185d}
.t-modern .chips i:nth-child(5n+3){background:#dbeafe;color:#1d4ed8}
.t-modern .chips i:nth-child(5n+4){background:#d1fae5;color:#047857}
.t-modern .chips i:nth-child(5n+5){background:#ffedd5;color:#c2410c}
/* Sidebar */
.t-side{display:grid;grid-template-columns:34% 66%}
.t-side .side{background:linear-gradient(180deg,var(--a),var(--b));color:#fff;padding:32px 22px}
.t-side .main{padding:32px 30px}
.t-side .av{width:90px;height:90px;border-radius:50%;background:rgba(255,255,255,.22);display:flex;align-items:center;
justify-content:center;font-size:28px;font-weight:800;margin-bottom:8px;overflow:hidden}
.t-side .av img{width:100%;height:100%;object-fit:cover}
.t-side .side .hd{color:#fff}
.t-side .side .hd::after{background:rgba(255,255,255,.45)}
.t-side .side .ct{flex-direction:column;margin-top:0;font-size:12px;word-break:break-word}
.t-side .side .co,.t-side .side .eh span,.t-side .side .dt{color:#eef2ff}
.t-side .side .chips i{background:rgba(255,255,255,.22);color:#fff}
.t-side .side .eh{display:block}
.t-side .main .role{color:var(--a)}
/* Minimal (ATS friendly) */
.t-min{font-family:Georgia,'Times New Roman',serif;padding:36px 42px}
.t-min .top{text-align:center}
.t-min .nm{font-size:28px}
.t-min .ct{justify-content:center}
.t-min .hd{color:#111}
.t-min .hd::after{background:#111;height:1px}
.t-min .chips{display:block}
.t-min .chips i{background:none;color:inherit;padding:0;font-weight:400;font-size:13px;border-radius:0}
.t-min .chips i:not(:last-child)::after{content:" · "}
@media print{.noprint{display:none !important}body{background:#fff !important;padding:0 !important}.rs{box-shadow:none;border-radius:0}}
"""

PAGE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stApp * {font-family: Inter, sans-serif;}
span[data-testid="stIconMaterial"], .material-icons {font-family: "Material Symbols Rounded", "Material Icons" !important;}

.stApp {
    background:
        radial-gradient(circle at 8% 0%, #dbeafe 0%, transparent 35%),
        radial-gradient(circle at 95% 8%, #ede9fe 0%, transparent 34%),
        #f8fafc;
}
.block-container {max-width: 1100px; padding-top: 24px;}
header[data-testid="stHeader"] {background: transparent;}

@keyframes flow {0% {background-position: 0% 50%} 100% {background-position: 200% 50%}}
.hero {text-align: center; padding: 14px 10px 10px;}
.hero-t {
    font-size: 46px; font-weight: 800; line-height: 1.1; margin: 4px 0 10px;
    letter-spacing: -0.025em;
    background: linear-gradient(90deg, #1d4ed8, #4f46e5, #7c3aed, #1d4ed8);
    background-size: 200% auto;
    animation: flow 7s linear infinite;
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-s {color: #64748b; font-size: 16px; max-width: 640px; margin: 0 auto 18px;}
.fp {display: inline-block; margin: 4px; padding: 6px 14px; border-radius: 99px; font-size: 13px; font-weight: 700;}

.step {
    display: flex; align-items: center; gap: 10px; font-size: 18px;
    font-weight: 800; color: #172554; margin: 2px 0 8px;
}
.step b {
    width: 32px; height: 32px; border-radius: 9px; display: inline-flex;
    align-items: center; justify-content: center; font-size: 16px;
    box-shadow: 0 6px 14px rgba(37, 99, 235, .18);
}
.hint {color: #64748b; font-size: 13px; margin: -4px 0 8px 42px;}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,.96);
    border: 1px solid #e2e8f0 !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 28px rgba(15, 23, 42, .06);
    padding: 6px 8px;
}
.stApp label p {color: #334155 !important; font-weight: 600 !important; font-size: 13.5px !important;}

.stTextInput input, .stTextArea textarea {
    background: #ffffff !important; color: #0f172a !important;
    border: 1.5px solid #cbd5e1 !important; border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.12) !important;
}
div[data-baseweb="select"] > div {
    background: #ffffff !important; border-radius: 10px !important;
    border: 1.5px solid #cbd5e1 !important;
}

.stButton > button, .stDownloadButton > button {
    width: 100%; border-radius: 10px; padding: 10px 12px;
    font-size: 14px; font-weight: 700;
    border: 1px solid #cbd5e1;
    background: #ffffff; color: #1e3a8a !important;
    transition: .2s;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #2563eb, #4f46e5);
    color: #fff !important; border: none;
    box-shadow: 0 8px 20px rgba(37,99,235,.24);
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px);
    border-color: #93c5fd;
    box-shadow: 0 5px 16px rgba(15,23,42,.08);
}

.stTabs [data-baseweb="tab-list"] {gap: 7px; border: 0;}
.stTabs [data-baseweb="tab"] {
    background: #ffffff; border-radius: 10px; padding: 8px 17px;
    border: 1px solid #e2e8f0; height: auto;
}
.stTabs [data-baseweb="tab"] p {font-weight: 700; color: #475569;}
.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #2563eb, #4f46e5);
    border-color: transparent;
}
.stTabs [aria-selected="true"] p {color: #fff !important;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display: none;}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a, #172554 55%, #312e81);
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"] label div,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] small {color: #e2e8f0 !important;}

.meter {
    background: rgba(255,255,255,.12); border-radius: 99px;
    height: 9px; overflow: hidden; margin: 6px 0 4px;
}
.meter div {
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, #60a5fa, #818cf8);
}

.ring {
    width: 84px; height: 84px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 20px; color: #172554; flex-shrink: 0;
}
.ring span {
    background: #fff; width: 62px; height: 62px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
}
.score {display: flex; align-items: center; gap: 18px; margin: 6px 0 10px;}
.tag {
    display: inline-block; margin: 3px 4px 0 0; padding: 3px 11px;
    border-radius: 99px; font-size: 12.5px; font-weight: 600;
}
.ok {background: #dcfce7; color: #166534;}
.miss {background: #fee2e2; color: #991b1b;}
.card {border-radius: 14px; padding: 14px 18px; margin: 10px 0; font-size: 14px;}
.card b {display: block; margin-bottom: 4px;}
.c-g {background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534;}
.c-y {background: #fffbeb; border: 1px solid #fde68a; color: #92400e;}
.c-r {background: #fef2f2; border: 1px solid #fecaca; color: #991b1b;}
.stCaption {text-align: center;}
"""

st.markdown("<style>" + PAGE_CSS + RESUME_CSS + "</style>", unsafe_allow_html=True)


# ============================================================ HELPERS
def esc(v):
    return html.escape(str(v or ""))


def as_list(v):
    return v if isinstance(v, list) else ([v] if isinstance(v, str) and v.strip() else [])


def clean(df):
    out = []
    for r in df.fillna("").to_dict("records"):
        vals = [str(v).strip() for v in r.values()]
        if any(vals):
            out.append(vals)
    return out


def to_df(rows, k):
    rows = [r for r in rows if len(r) == len(COLS[k])]
    return pd.DataFrame(rows, columns=COLS[k])


def reset_editors():
    for k in COLS:
        st.session_state.pop(f"ed_{k}", None)


def load_sample():
    for k, v in SAMPLE_FIELDS.items():
        st.session_state[k] = v
    st.session_state.tables = {k: to_df(SAMPLE_TABLES[k], k) for k in COLS}
    reset_editors()


def jload(text):
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {}


def ask(prompt, as_json=False, stream_status=None):
    kwargs = {"format": "json"} if as_json else {}
    buf = []
    for part in ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}], stream=True,
                            options={"temperature": 0.35}, **kwargs):
        buf.append(part["message"]["content"])
        if stream_status and len(buf) % 20 == 0:
            stream_status.update(label=f"AI is writing… ({len(buf)} tokens)")
    return "".join(buf)


def ollama_error(e):
    st.error(f"Could not get an answer from Ollama: {e}\n\nMake sure Ollama is running, then run: `ollama pull {MODEL}`")


def entry(title, right="", sub="", detail="", bullets=None):
    li = "".join(f"<li>{esc(b)}</li>" for b in (bullets or []))
    return ("<div class='e'>"
            f"<div class='eh'><b>{esc(title)}</b><span>{esc(right)}</span></div>"
            + (f"<div class='co'>{esc(sub)}</div>" if sub else "")
            + (f"<div class='dt'>{esc(detail)}</div>" if detail else "")
            + (f"<ul>{li}</ul>" if li else "") + "</div>")


def sec(title, body):
    return f"<div class='hd'>{title}</div>{body}" if body else ""


def fallback_bullets(notes):
    parts = [p.strip(" .") for p in re.split(r"[.\n;]", notes) if p.strip()]
    return [p[0].upper() + p[1:] for p in parts]


# ============================================================ RESUME BUILDING
def build_blocks(R, keep):
    T = R["tables"]
    b = {}
    b["profile"] = f"<div>{esc(R['summary'])}</div>" if R["summary"] else ""
    b["exp"] = "".join(entry(x["role"], x["dates"], x["company"], bullets=x["bullets"]) for x in R["exp"])
    b["intern"] = "".join(entry(x["role"], x["dates"], x["company"], bullets=x["bullets"]) for x in R["intern"])
    b["proj"] = "".join(entry(x["name"], x["link"], x["tech"], x["desc"]) for x in R["proj"])
    b["edu"] = "".join(entry(r[0], r[2], r[1] + (f" · {r[3]}" if r[3] else "")) for r in T["edu"])
    b["award"] = "".join(entry(r[0], r[2], r[1]) for r in T["award"])
    b["cert"] = "".join(entry(r[0], r[2], r[1]) for r in T["cert"])
    b["vol"] = "".join(entry(r[0], "", r[1], r[2]) for r in T["vol"])
    b["skills"] = "<div class='chips'>" + "".join(f"<i>{esc(s)}</i>" for s in R["skills"]) + "</div>" if R["skills"] else ""
    b["lang"] = ("<div class='chips'>" + "".join(f"<i>{esc(r[0])}{' · ' + esc(r[1]) if r[1] else ''}</i>" for r in T["lang"]) + "</div>"
                 if T["lang"] else "")
    titles = dict(SECTIONS)
    return {k: (sec(titles[k], b[k]) if k in keep else "") for k in b}


def build_resume_html(R, template, theme, keep, photo):
    a, c = THEMES[theme]
    b = build_blocks(R, keep)
    info = R["info"]
    ct = "".join(f"<span>{esc(x)}</span>" for x in (info["email"], info["phone"], info["loc"], info["links"]) if x)
    head = f"<div class='nm'>{esc(info['name'])}</div><div class='role'>{esc(info['title'])}</div>"
    if template == "Sidebar":
        ini = "".join(w[0] for w in info["name"].split()[:2]).upper()
        av = f"<img src='{photo}'>" if photo else esc(ini)
        contact = sec("Contact", f"<div class='ct'>{ct}</div>")
        inner = (f"<div class='side'><div class='av'>{av}</div>{contact}{b['skills']}{b['lang']}{b['edu']}{b['cert']}</div>"
                 f"<div class='main'>{head}{b['profile']}{b['exp']}{b['intern']}{b['proj']}{b['award']}{b['vol']}</div>")
        cls = "t-side"
    elif template == "Minimal":
        inner = (f"<div class='top'>{head}<div class='ct'>{ct}</div></div>{b['profile']}{b['edu']}{b['exp']}{b['intern']}"
                 f"{b['proj']}{b['award']}{b['skills']}{b['cert']}{b['vol']}{b['lang']}")
        cls = "t-min"
    else:
        ph = f"<img class='ph' src='{photo}'>" if photo else ""
        inner = (f"<div class='top'>{ph}<div><div class='nm'>{esc(info['name'])}</div><div class='role'>{esc(info['title'])}</div>"
                 f"<div class='ct'>{ct}</div></div></div><div class='body'>{b['profile']}{b['exp']}{b['intern']}{b['proj']}"
                 f"{b['edu']}{b['award']}{b['skills']}{b['cert']}{b['vol']}{b['lang']}</div>")
        cls = "t-modern"
    return f"<div class='rs {cls}' style='--a:{a};--b:{c}'>{inner}</div>"


def build_text(R):
    i, T = R["info"], R["tables"]
    L = [i["name"].upper(), i["title"], " | ".join(x for x in (i["email"], i["phone"], i["loc"], i["links"]) if x), ""]
    if R["summary"]:
        L += ["PROFILE", R["summary"], ""]
    for key, title in (("exp", "EXPERIENCE"), ("intern", "INTERNSHIPS")):
        if R[key]:
            L.append(title)
            for x in R[key]:
                L.append(f"{x['role']} - {x['company']} ({x['dates']})")
                L += [f"  - {t}" for t in x["bullets"]]
            L.append("")
    if R["proj"]:
        L.append("PROJECTS")
        L += [f"{p['name']} ({p['tech']}): {p['desc']}" for p in R["proj"]] + [""]
    for key, title, fmt in (("edu", "EDUCATION", "{0} - {1} ({2}) {3}"), ("award", "SCHOLARSHIPS & AWARDS", "{0} - {1} ({2})"),
                            ("cert", "CERTIFICATIONS", "{0} - {1} ({2})"), ("vol", "VOLUNTEERING", "{0} - {1}: {2}")):
        if T[key]:
            L.append(title)
            L += [fmt.format(*(r + [""] * 4)) for r in T[key]] + [""]
    if R["skills"]:
        L += ["SKILLS", ", ".join(R["skills"]), ""]
    if T["lang"]:
        L += ["LANGUAGES", ", ".join(f"{r[0]} ({r[1]})" for r in T["lang"])]
    return "\n".join(L)


def generate(info, T, status):
    payload = {
        "target_title": info["title"], "summary_notes": info["summary"], "skills": info["skills"],
        "experience": [{"role": r[0], "company": r[1], "notes": r[3]} for r in T["exp"]],
        "internships": [{"role": r[0], "company": r[1], "notes": r[3]} for r in T["intern"]],
        "projects": [{"name": r[0], "tech": r[1], "notes": r[3]} for r in T["proj"]],
    }
    jd = f"\nTAILOR FOR THIS JOB:\n{info['jd']}\n" if info["jd"] else ""
    prompt = f"""You are an expert resume writer and ATS specialist. Return ONLY JSON in this shape:
{{"summary": "...", "skills": ["..."], "experience": [{{"bullets": ["..."]}}], "internships": [{{"bullets": ["..."]}}], "projects": [{{"description": "..."}}]}}
RULES: experience, internships and projects arrays must have EXACTLY the same number and order as the input.
Experience: 3-4 bullets each. Internships: 2-3 bullets each. Every bullet = strong action verb + what + impact.
Use numbers only if the user gave them. Summary: 2-3 confident sentences tailored to the target title, never use "I".
Skills: 8-14 items, most relevant first. Never invent facts. Fix grammar.{jd}
INPUT:
{json.dumps(payload)}"""
    try:
        ai = jload(ask(prompt, True, status))
        err = None
    except Exception as e:
        ai, err = {}, e

    def merge(key, rows):
        out = []
        for i, r in enumerate(rows):
            got = as_list(ai.get(key))
            g = got[i] if i < len(got) and isinstance(got[i], dict) else {}
            bl = [str(x) for x in as_list(g.get("bullets"))] or fallback_bullets(r[3])
            out.append({"role": r[0], "company": r[1], "dates": r[2], "bullets": bl})
        return out

    projs = []
    got = as_list(ai.get("projects"))
    for i, r in enumerate(T["proj"]):
        g = got[i] if i < len(got) and isinstance(got[i], dict) else {}
        projs.append({"name": r[0], "tech": r[1], "link": r[2], "desc": str(g.get("description") or r[3])})
    skills = [str(s) for s in as_list(ai.get("skills"))] or [s.strip() for s in info["skills"].split(",") if s.strip()]
    return {"info": info, "tables": T, "summary": str(ai.get("summary") or info["summary"]), "skills": skills,
            "exp": merge("experience", T["exp"]), "intern": merge("internships", T["intern"]), "proj": projs}, err


def ats_check(R):
    jd = R["info"]["jd"]
    words = [w.strip(".") for w in re.findall(r"[a-zA-Z][a-zA-Z+#.]{2,}", jd.lower())]
    stop = set("the and for with you your our are will have has from that this their they able work team role about into over more "
               "than such using use per job must can who all any not but its should also strong good experience years year ability "
               "skills looking need needs candidate".split())
    top = [w for w, _ in Counter(w for w in words if w and w not in stop).most_common(15)]
    blob = build_text(R).lower()
    return top, [k for k in top if k not in blob]


def strength(vals, T, photo):
    s = 0
    s += 10 if vals["p_name"] and vals["p_title"] else 0
    s += 10 if vals["p_email"] and vals["p_phone"] else 0
    s += 10 if vals["p_summary"] else 0
    s += 10 if len([x for x in vals["p_skills"].split(",") if x.strip()]) >= 5 else 0
    s += 20 if (T["exp"] or T["intern"]) else 0
    s += 10 if T["edu"] else 0
    s += 10 if T["proj"] else 0
    s += 10 if (T["award"] or T["cert"]) else 0
    s += 5 if vals["p_jd"] else 0
    s += 5 if photo else 0
    return s


def step(n, title, g):
    return f'<div class="step"><b style="background:{g};color:#fff">{n}</b> {title}</div>'


# ============================================================ STATE + SIDEBAR
if "tables" not in st.session_state:
    st.session_state.tables = {k: pd.DataFrame(columns=COLS[k]) for k in COLS}

with st.sidebar:
    st.markdown("## 🎨 Design")
    template = st.radio("Template", ["Modern", "Sidebar", "Minimal"], help="Minimal is the most ATS-friendly.")
    theme = st.selectbox("Colour theme", list(THEMES))
    st.markdown("".join(
        f"<span style='display:inline-block;width:26px;height:26px;border-radius:50%;margin:2px;"
        f"background:linear-gradient(135deg,{a},{b})'></span>" for a, b in THEMES.values()), unsafe_allow_html=True)
    keep_labels = st.multiselect("Sections to show", [t for _, t in SECTIONS], default=[t for _, t in SECTIONS])
    keep = [k for k, t in SECTIONS if t in keep_labels]
    st.markdown("## 🤖 AI")
    MODEL = st.text_input("Ollama model", value="llama3.2")
    st.markdown("## 💾 Save / Load")
    up = st.file_uploader("Load a saved profile (.json)", type="json")
    if up is not None and st.session_state.get("loaded") != (up.name, up.size):
        try:
            saved = json.loads(up.getvalue())
            for k in FIELDS:
                st.session_state[k] = saved["fields"].get(k, "")
            st.session_state.tables = {k: to_df(saved["tables"].get(k, []), k) for k in COLS}
            reset_editors()
            st.session_state.loaded = (up.name, up.size)
        except Exception:
            st.error("That file is not a valid profile.")
    meter = st.empty()

# ============================================================ HERO
st.markdown(
    """<div class="hero"><div class="hero-t">ResumeAI Studio</div>
<div class="hero-s">Build a professional, ATS-ready resume with AI-powered writing, projects, internships and more.</div></div>""",
    unsafe_allow_html=True,
)

# ============================================================ TOP QUICK-ACTION BUTTONS
# These are real Streamlit buttons, not decorative HTML labels.
if "quick_action" not in st.session_state:
    st.session_state.quick_action = ""

q1, q2, q3, q4, q5, q6 = st.columns(6)

if q1.button("💼 Internships", use_container_width=True):
    st.session_state.quick_action = "internships"

if q2.button("🎓 Scholarships", use_container_width=True):
    st.session_state.quick_action = "scholarships"

if q3.button("🚀 Projects", use_container_width=True):
    st.session_state.quick_action = "projects"

if q4.button("🎯 ATS Score", use_container_width=True):
    st.session_state.quick_action = "ats"

if q5.button("✉️ Cover Letter", use_container_width=True):
    st.session_state.quick_action = "cover"

if q6.button("🎤 Interview Prep", use_container_width=True):
    st.session_state.quick_action = "interview"

# Quick-access panel
action = st.session_state.quick_action

if action:
    with st.container(border=True):
        if action == "internships":
            st.markdown("### 💼 Internships")
            st.info("Add your internships in the **Build → Internships** section below.")
            st.markdown("Your internship details will automatically appear in the generated resume.")

        elif action == "scholarships":
            st.markdown("### 🎓 Scholarships & Awards")
            st.info("Add scholarships, prizes, hackathon wins and awards in the **Build → Scholarships & awards** section.")
            st.markdown("These achievements will automatically appear in your resume.")

        elif action == "projects":
            st.markdown("### 🚀 Projects")
            st.info("Add your academic, personal or open-source projects in the **Build → Projects** section.")
            st.markdown("The AI can improve your project descriptions when you generate the resume.")

        elif action == "ats":
            st.markdown("### 🎯 ATS Score")
            if "R" not in st.session_state:
                st.warning("Generate your resume first. Then your ATS keyword score will appear in the **Resume** tab.")
            else:
                quick_R = st.session_state.R
                if quick_R["info"]["jd"]:
                    quick_top, quick_missing = ats_check(quick_R)
                    quick_score = int(100 * (len(quick_top) - len(quick_missing)) / len(quick_top)) if quick_top else 0
                    st.metric("ATS Keyword Match", f"{quick_score}%")
                    if quick_missing:
                        st.write("Missing keywords:")
                        st.write(", ".join(quick_missing))
                    else:
                        st.success("No missing keywords were detected from the job description.")
                else:
                    st.warning("Add a job description in the Build tab to calculate the ATS score.")

        elif action == "cover":
            st.markdown("### ✉️ Cover Letter")
            if "R" not in st.session_state:
                st.warning("Generate your resume first. Then open **🚀 AI Tools → Cover letter**.")
            else:
                st.success("Your resume is ready for a personalized cover letter.")
                st.info("Open **🚀 AI Tools → Cover letter** to enter the company and generate it with AI.")

        elif action == "interview":
            st.markdown("### 🎤 Interview Preparation")
            if "R" not in st.session_state:
                st.warning("Generate your resume first. Then open **🚀 AI Tools → Interview prep**.")
            else:
                st.success("Your resume is ready for interview preparation.")
                st.info("Open **🚀 AI Tools → Interview prep** to generate technical, behavioural and HR questions.")

tab_build, tab_resume, tab_tools = st.tabs(["✍️ Build", "📄 Resume", "🚀 AI Tools"])

# ============================================================ TAB 1: BUILD
with tab_build:
    st.button("⚡ Fill with sample data", on_click=load_sample)

    with st.container(border=True):
        st.markdown(step(1, "About you", "linear-gradient(135deg,#6366f1,#a855f7)"), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.text_input("Full name", key="p_name", placeholder="Priya Sharma")
        c2.text_input("Target job title", key="p_title", placeholder="Frontend Developer")
        c3, c4, c5 = st.columns(3)
        c3.text_input("Email", key="p_email")
        c4.text_input("Phone", key="p_phone")
        c5.text_input("Location", key="p_loc")
        st.text_input("Links (LinkedIn, GitHub, portfolio)", key="p_links")
        photo_file = st.file_uploader("Profile photo (optional, used in Modern and Sidebar)", type=["png", "jpg", "jpeg"])
        st.text_area("Summary notes", key="p_summary", height=70, placeholder="Rough notes about you. The AI will polish them.")
        st.text_input("Skills (comma separated)", key="p_skills", placeholder="Python, SQL, Git")

    T_RAW = {}

    def editor(k, label, hint, g, n):
        with st.container(border=True):
            st.markdown(step(n, label, g), unsafe_allow_html=True)
            st.markdown(f'<div class="hint">{hint}</div>', unsafe_allow_html=True)
            cfg = {COLS[k][-1]: st.column_config.TextColumn(width="large")} if k in ("exp", "intern", "proj", "vol") else {}
            T_RAW[k] = st.data_editor(st.session_state.tables[k], key=f"ed_{k}", num_rows="dynamic",
                                      column_config=cfg, hide_index=True)

    editor("exp", "💼 Work experience", "Click the empty row at the bottom to add. Rough notes are fine.", "linear-gradient(135deg,#0ea5e9,#6366f1)", 2)
    editor("intern", "🧑‍💻 Internships", "Add every internship, even short ones.", "linear-gradient(135deg,#f97316,#ec4899)", 3)
    editor("edu", "🎓 Education", "Degree, school, year and CGPA / percentage.", "linear-gradient(135deg,#059669,#0ea5e9)", 4)
    editor("proj", "🚀 Projects", "Academic, personal or open-source projects.", "linear-gradient(135deg,#a855f7,#ec4899)", 5)
    editor("award", "🏆 Scholarships & awards", "Scholarships, prizes, hackathon wins, rankings.", "linear-gradient(135deg,#d97706,#dc2626)", 6)
    editor("cert", "📜 Certifications", "Courses and certificates.", "linear-gradient(135deg,#4338ca,#9333ea)", 7)
    editor("vol", "🤝 Volunteering & activities", "Clubs, NSS/NCC, events, leadership.", "linear-gradient(135deg,#be185d,#7c3aed)", 8)
    editor("lang", "🌍 Languages", "Language and level (Native, Fluent, Basic).", "linear-gradient(135deg,#14b8a6,#3b82f6)", 9)

    with st.container(border=True):
        st.markdown(step(10, "🎯 Target job (recommended)", "linear-gradient(135deg,#ef4444,#f97316)"), unsafe_allow_html=True)
        st.text_area("Paste the job description", key="p_jd", height=110,
                     placeholder="The AI tailors your resume and shows an ATS keyword score.")

    go = st.button("✨ Generate my resume", type="primary")

# collect current values (runs every rerun)
VALS = {k: st.session_state.get(k, "").strip() for k in FIELDS}
TABLES = {k: clean(T_RAW[k]) for k in COLS}
photo = ""
if photo_file is not None:
    photo = f"data:{photo_file.type};base64," + base64.b64encode(photo_file.getvalue()).decode()

pct = strength(VALS, TABLES, photo)
meter.markdown(f"<div style='color:#e0e7ff;font-weight:700;margin-top:10px'>Profile strength: {pct}%</div>"
               f"<div class='meter'><div style='width:{pct}%'></div></div>", unsafe_allow_html=True)

if go:
    if not VALS["p_name"] or not VALS["p_title"]:
        tab_build.warning("Please enter at least your name and target job title.")
    else:
        info = {k[2:]: VALS[k] for k in FIELDS}
        with tab_build.status("AI is writing…", expanded=False) as status:
            R, err = generate(info, TABLES, status)
            st.session_state.R = R
            if err:
                status.update(label="AI unavailable, built from your notes instead", state="error")
                ollama_error(err)
            else:
                status.update(label="Resume ready ✅  Open the 📄 Resume tab", state="complete")

# ============================================================ TAB 2: RESUME
with tab_resume:
    if "R" not in st.session_state:
        st.info("Fill in the Build tab and click Generate. Try the sample data button first.")
    else:
        R = st.session_state.R
        resume = build_resume_html(R, template, theme, keep, photo)
        st.markdown(resume, unsafe_allow_html=True)

        a, _ = THEMES[theme]
        page = ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>" + esc(R["info"]["name"]) + " - Resume</title>"
                "<style>body{background:#eef0f6;padding:24px;max-width:900px;margin:auto}.noprint{margin-bottom:14px;padding:10px 20px;"
                "border:0;border-radius:10px;background:" + a + ";color:#fff;font-weight:700;cursor:pointer}" + RESUME_CSS +
                "</style></head><body><button class='noprint' onclick='window.print()'>Print / Save as PDF</button>" + resume + "</body></html>")
        st.write("")
        d1, d2, d3 = st.columns(3)
        d1.download_button("⬇ Resume (HTML → PDF)", page, file_name="resume.html", mime="text/html")
        d2.download_button("⬇ Plain text (ATS)", build_text(R), file_name="resume.txt")
        d3.download_button("💾 Save my profile", json.dumps({"fields": VALS, "tables": TABLES}), file_name="profile.json")

        if R["info"]["jd"]:
            top, missing = ats_check(R)
            score = int(100 * (len(top) - len(missing)) / len(top)) if top else 0
            st.markdown("### 🎯 ATS keyword match")
            st.markdown(
                f"<div class='score'><div class='ring' style='background:conic-gradient({a} {score}%, #e5e7eb 0)'><span>{score}%</span></div><div>"
                + "".join(f"<span class='tag ok'>{esc(k)}</span>" for k in top if k not in missing)
                + "".join(f"<span class='tag miss'>{esc(k)}</span>" for k in missing) + "</div></div>", unsafe_allow_html=True)
            if missing:
                st.caption("Red keywords appear in the job description but not in your resume. Add them only if they are true for you.")

# ============================================================ TAB 3: AI TOOLS
with tab_tools:
    if "R" not in st.session_state:
        st.info("Generate your resume first. These tools use it.")
    else:
        R = st.session_state.R
        resume_text = build_text(R)
        jd = R["info"]["jd"] or "Not provided"
        t1, t2, t3, t4 = st.tabs(["✉️ Cover letter", "🔍 Resume review", "🎤 Interview prep", "💼 LinkedIn"])

        with t1:
            c1, c2, c3 = st.columns(3)
            company = c1.text_input("Company", key="cl_company")
            manager = c2.text_input("Hiring manager (optional)", key="cl_mgr")
            tone = c3.selectbox("Tone", ["Professional", "Friendly", "Confident", "Enthusiastic"])
            if st.button("✉️ Write cover letter"):
                with st.spinner("Writing…"):
                    try:
                        st.session_state.cl_text = ask(
                            f"Write a one-page cover letter (about 250 words) for the role of {R['info']['title']} at "
                            f"{company or 'the company'}. Address it to {manager or 'the Hiring Manager'}. Tone: {tone}. "
                            f"Use only facts from this resume, never invent achievements.\n\nRESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd}\n\n"
                            "Return only the letter text.")
                    except Exception as e:
                        ollama_error(e)
            if "cl_text" in st.session_state:
                st.text_area("Your cover letter (editable)", value=st.session_state.cl_text, height=360)
                st.download_button("⬇ Download cover letter", st.session_state.cl_text, file_name="cover_letter.txt")

        with t2:
            if st.button("🔍 Review my resume"):
                with st.spinner("Reviewing…"):
                    try:
                        st.session_state.review = jload(ask(
                            "You are a strict senior recruiter. Review this resume for the target role. Return ONLY JSON: "
                            '{"score": 0-100 integer, "strengths": ["..."], "improvements": ["..."], "missing": ["..."]} '
                            "with 3-5 short items per list. 'missing' = sections or keywords a recruiter would expect.\n\n"
                            f"TARGET: {R['info']['title']}\nJOB DESCRIPTION: {jd}\n\nRESUME:\n{resume_text}", True))
                    except Exception as e:
                        ollama_error(e)
            rv = st.session_state.get("review")
            if rv:
                sc = int(rv.get("score", 0) or 0)
                a, _ = THEMES[theme]
                st.markdown(f"<div class='score'><div class='ring' style='background:conic-gradient({a} {sc}%, #e5e7eb 0)'><span>{sc}</span></div>"
                            "<div><b>Recruiter score</b><br><small>out of 100</small></div></div>", unsafe_allow_html=True)
                for key, cls, title in (("strengths", "c-g", "✅ Strengths"), ("improvements", "c-y", "💡 Improve"), ("missing", "c-r", "⚠️ Missing")):
                    items = "".join(f"• {esc(x)}<br>" for x in as_list(rv.get(key)))
                    if items:
                        st.markdown(f"<div class='card {cls}'><b>{title}</b>{items}</div>", unsafe_allow_html=True)

        with t3:
            if st.button("🎤 Generate interview questions"):
                with st.spinner("Thinking…"):
                    try:
                        st.session_state.iq = jload(ask(
                            "Create 10 likely interview questions (mix of technical, behavioural and HR) for this candidate and role. "
                            'Return ONLY JSON: {"questions": [{"q": "...", "tip": "how to answer using the candidate\'s real experience"}]}\n\n'
                            f"ROLE: {R['info']['title']}\nJOB DESCRIPTION: {jd}\n\nRESUME:\n{resume_text}", True))
                    except Exception as e:
                        ollama_error(e)
            for i, q in enumerate(as_list((st.session_state.get("iq") or {}).get("questions")), 1):
                if isinstance(q, dict):
                    with st.expander(f"{i}. {q.get('q', '')}"):
                        st.write(q.get("tip", ""))

        with t4:
            if st.button("💼 Write LinkedIn headline and About"):
                with st.spinner("Writing…"):
                    try:
                        st.session_state.li = jload(ask(
                            'Write a LinkedIn headline (max 120 characters) and an About section (120-180 words, first person, friendly, '
                            'no invented facts) from this resume. Return ONLY JSON: {"headline": "...", "about": "..."}\n\n'
                            f"RESUME:\n{resume_text}", True))
                    except Exception as e:
                        ollama_error(e)
            li = st.session_state.get("li")
            if li:
                st.markdown("**Headline**")
                st.code(str(li.get("headline", "")), language=None)
                st.markdown("**About**")
                st.code(str(li.get("about", "")), language=None)

st.caption("ResumeAI Studio · Streamlit · Ollama")