"""DSP Agent Studio - one local server: client demo sites, chat agents, dashboard, sales tools.
Run:  python studio/server.py   -> http://127.0.0.1:8000
No packages needed. Optional keys go in studio/.env (never committed): ANTHROPIC_API_KEY, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_VERIFY_TOKEN
"""
import glob, json, os, re, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import engine, tools

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, STATIC, AGENTS = (os.path.join(BASE, d) for d in ("data", "static", "agents"))
os.makedirs(DATA, exist_ok=True)
LOCK = threading.Lock()


def load_env():
    env = {}
    p = os.path.join(BASE, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k.strip()] = v.strip().strip('"')
    return env


ENV = load_env()
ENVG = lambda k, d="": ENV.get(k) or os.environ.get(k, d)
API_KEY, MODEL = ENVG("ANTHROPIC_API_KEY"), ENVG("CLAUDE_MODEL", "claude-sonnet-5")
WA_TOKEN, WA_PHONE, WA_VERIFY = ENVG("WHATSAPP_TOKEN"), ENVG("WHATSAPP_PHONE_ID"), ENVG("WHATSAPP_VERIFY_TOKEN", "dsp-verify")


# ---------------- storage ----------------
def rd(name, default=None):
    p = os.path.join(DATA, name)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            pass
    return [] if default is None else default


def wr(name, rows):
    with LOCK:
        json.dump(rows, open(os.path.join(DATA, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def add(name, item):
    with LOCK:
        rows = rd(name)
        rows.append(item)
        json.dump(rows, open(os.path.join(DATA, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def agents():
    out = {}
    for f in sorted(glob.glob(os.path.join(AGENTS, "*.json"))):
        try:
            a = json.load(open(f, encoding="utf-8"))
            out[a["id"]] = a
        except Exception as e:
            print("bad agent file", f, e)
    return out


def summary(a):
    return {k: a.get(k) for k in ("id", "name", "industry", "emoji", "color", "tagline", "city", "phone", "custom")} | {
        "flow": a["flow"]["type"], "catalog_n": len(a.get("catalog", [])), "faq_n": len(a.get("faq", []))}


# ---------------- agent runtime ----------------
SESSIONS = {}


def new_state(sid="x"):
    return {"cart": {}, "fields": {}, "collecting": False, "sid": sid}


def save_record(biz, rec, channel="web", sample=False):
    with LOCK:
        rows = rd("records.json")
        n = sum(1 for r in rows if r.get("biz") == biz["id"]) + 1
        r = {"id": "%s-%04d" % (biz.get("code", biz["id"][:2].upper()), n), "biz": biz["id"], "biz_name": biz["name"], "time": now(),
             "status": "new", "channel": channel, "sample": sample, **rec}
        rows.append(r)
        json.dump(rows, open(os.path.join(DATA, "records.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return r


def chat(biz_id, sid, text, channel="web"):
    biz = agents().get(biz_id)
    if not biz:
        return "Unknown business.", "error"
    st = SESSIONS.setdefault((biz_id, sid), new_state(sid))
    sr = lambda rec: save_record(biz, rec, channel)
    lq = lambda q: add("questions.json", {"id": "Q%d" % (len(rd("questions.json")) + 1), "time": now(), "biz": biz_id, "biz_name": biz["name"], "question": q[:300], "session": sid, "resolved": False, "sample": False})
    mode = "offline"
    if API_KEY:
        try:
            reply, mode = engine.claude_agent(biz, st, text, sr, API_KEY, MODEL), "claude"
        except Exception as e:
            print("Claude error -> offline:", str(e)[:120])
            reply = engine.offline_reply(biz, st, text, sr, lq)
    else:
        reply = engine.offline_reply(biz, st, text, sr, lq)
    add("chats.json", {"time": now(), "biz": biz_id, "session": sid, "user": text[:500], "bot": reply[:900], "mode": mode, "channel": channel, "sample": False})
    return reply, mode


def claude_text(system, user):
    body = json.dumps({"model": MODEL, "max_tokens": 600, "system": system, "messages": [{"role": "user", "content": user}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    return "".join(b.get("text", "") for b in json.load(urllib.request.urlopen(req, timeout=60))["content"])


# ---------------- agent builder ----------------
def slug(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())[:20] or "agent"


def build_config(d):
    name = (d.get("name") or "My Business").strip()
    aid = slug(d.get("id") or name)
    ftype = d.get("flow") if d.get("flow") in ("order", "booking", "lead") else "lead"
    cat = []
    for i, line in enumerate([l for l in (d.get("catalog") or "").splitlines() if l.strip()]):
        p = [x.strip() for x in line.split("|")]
        price = None
        if len(p) > 1 and re.sub(r"[^\d]", "", p[1]):
            price = int(re.sub(r"[^\d]", "", p[1]))
        nm = p[0]
        cat.append({"id": "i%d" % i, "name": nm, "price": price, "desc": p[2] if len(p) > 2 else "", "aliases": list({nm.lower(), nm.lower().split()[0]})})
    faq = []
    for line in [l for l in (d.get("faq") or "").splitlines() if ":" in l]:
        k, a = line.split(":", 1)
        faq.append({"keys": [x.strip().lower() for x in k.split(",") if x.strip()], "a": a.strip()})
    F = lambda key, t, en, ur: {"key": key, "type": t, "ask_en": en, "ask_ur": ur}
    base = [F("name", "text", "Your name?", "Aap ka naam?"), F("phone", "phone", "Your phone number?", "Aap ka phone number?")]
    if ftype == "order":
        fields = base + [F("address", "text", "Delivery address?", "Delivery ka pata?")]
    elif ftype == "booking":
        fields = base + ([F("item", "catalog", "Which one would you like?", "Kaunsi cheez chahiye?")] if cat else []) + [F("when", "text", "Preferred day and time?", "Kaunsa din aur waqt?")]
    else:
        fields = base + ([F("item", "catalog", "Which one are you interested in?", "Kis mein dilchaspi hai?")] if cat else []) + [F("note", "text", "Anything else we should know?", "Aur kuch batana chahain?")]
    triggers = {"order": [], "booking": ["book", "appointment", "reserve", "schedule"], "lead": ["interested", "join", "apply", "register", "quote", "enquiry", "inquiry", "contact"]}[ftype]
    code = (aid[:2] or "XX").upper()
    if any(a.get("code") == code and a["id"] != aid for a in agents().values()):
        code = (aid[:1] + str(len(agents()))).upper()
    rules = [l.strip() for l in (d.get("rules") or "").splitlines() if l.strip()] or ["Answer only from the business information.", "Never invent prices or facts; say you do not know and offer a call back."]
    return {"id": aid, "code": code, "custom": True, "name": name, "industry": d.get("industry") or "Business", "emoji": d.get("emoji") or "🏪", "color": d.get("color") or "#2563eb",
            "tagline": d.get("tagline") or "", "city": d.get("city") or "", "phone": d.get("phone") or "", "address": d.get("address") or "", "hours": d.get("hours") or "",
            "currency": d.get("currency") or "Rs", "greeting": d.get("greeting") or "How can I help you today?",
            "offers": [l.strip() for l in (d.get("offers") or "").splitlines() if l.strip()], "catalog_label": d.get("catalog_label") or "Menu / Services", "catalog": cat, "faq": faq,
            "flow": {"type": ftype, "record_label": {"order": "Order", "booking": "Booking", "lead": "Enquiry"}[ftype], "triggers": triggers, "example": "2 " + (cat[0]["name"].lower() if cat else "items"), "fields": fields},
            "role": "You are the assistant of %s." % name, "goal": d.get("goal") or "Answer questions and take %s requests." % ftype,
            "audience": d.get("audience") or "Customers of %s." % name, "tone": d.get("tone") or "Friendly, short, clear.", "rules": rules,
            "roi": {"monthly_leads": 200, "close_rate": 20, "avg_value": 2000, "missed_pct": 30, "staff_cost": 40000}}


# ---------------- sample data for demos ----------------
def seed():
    ag = agents()
    if any(r.get("sample") for r in rd("records.json")):
        return "Sample data already loaded."
    samples = [
        ("pizza", {"type": "order", "label": "Order", "fields": {"name": "Ahmed Raza", "phone": "03001234567", "address": "House 21, Gulberg III"}, "items": {"Pepperoni Pizza": 2, "Cola (500 ml)": 2}, "subtotal": 3300, "delivery": 0, "total": 3300}),
        ("pizza", {"type": "order", "label": "Order", "fields": {"name": "Sana Malik", "phone": "03211234567", "address": "Flat 4, Model Town"}, "items": {"Margherita Pizza": 1, "Fries": 1}, "subtotal": 1650, "delivery": 200, "total": 1850}),
        ("admission", {"type": "lead", "label": "Seat reservation", "fields": {"name": "Hina Tariq", "phone": "03331234567", "item": "AI Agent Bootcamp (5 days)", "background": "Teacher, urgent - want to start tomorrow"}}),
        ("admission", {"type": "lead", "label": "Seat reservation", "fields": {"name": "Bilal Khan", "phone": "03451234567", "item": "Website with Claude", "background": "Student"}}),
        ("realestate", {"type": "lead", "label": "Viewing request", "fields": {"name": "Usman Ali", "phone": "03121234567", "item": "5 Marla House, DHA", "budget": "25000000", "when": "tomorrow 5 pm"}}),
        ("rentacar", {"type": "booking", "label": "Booking", "fields": {"name": "Fatima Noor", "phone": "03011234567", "item": "Toyota Corolla", "dates": "this week, 3 days", "pickup": "Islamabad airport"}}),
        ("clinic", {"type": "booking", "label": "Appointment", "fields": {"name": "Zain Abbas", "phone": "03151234567", "item": "Dental Check-up", "when": "today evening"}}),
    ]
    for bid, rec in samples:
        if bid in ag:
            save_record(ag[bid], rec, "web", True)
    for bid, q in (("pizza", "Do you have gluten-free crust?"), ("clinic", "Is the doctor available on Sunday?"), ("realestate", "Any 3 marla houses in Johar Town?")):
        if bid in ag:
            add("questions.json", {"id": "Q%d" % (len(rd("questions.json")) + 1), "time": now(), "biz": bid, "biz_name": ag[bid]["name"], "question": q, "session": "sample", "resolved": False, "sample": True})
    crm = [("Al-Noor Restaurant", "Restaurant", "Contacted", 1500, "Cold email, asked for demo"), ("Prime Dental Care", "Clinic", "Demo shown", 2500, "Liked appointment booking"),
           ("City Motors Rentals", "Car rental", "Proposal sent", 3000, "Waiting for reply"), ("Green Valley Homes", "Real estate", "New", 2000, "Found on Google, no website chat"),
           ("Bake House", "Restaurant", "Won", 800, "Starter package, paid"), ("Glow Salon", "Salon", "Lost", 600, "Chose a cheaper option")]
    for n, ind, st, val, note in crm:
        add("crm.json", {"id": "C%d" % (len(rd("crm.json")) + 1), "name": n, "industry": ind, "contact": "", "source": "sample", "stage": st, "value": val, "notes": note, "created": now(), "sample": True})
    for bid, u, b in (("pizza", "2 margherita please", "Added. 2 x Margherita Pizza = Rs 2,400"), ("admission", "kya beginners join kar sakte hain", "No coding is needed. The course is for complete beginners."), ("clinic", "book appointment", "Let's book your appointment. Your name?")):
        add("chats.json", {"time": now(), "biz": bid, "session": "sample", "user": u, "bot": b, "mode": "offline", "channel": "web", "sample": True})
    return "Sample data loaded (marked as sample)."


def reset_samples():
    for f in ("records.json", "questions.json", "chats.json", "crm.json", "drafts.json"):
        wr(f, [r for r in rd(f) if not r.get("sample")])
    return "Sample data removed."


# ---------------- coverage: what the teacher taught vs what exists here ----------------
COVERAGE = [
    ("Agent formula: Claude + job description + tools + loop", "Class 1-3", "Every agent uses Role/Goal/Audience/Tone/Rules; tool = save_record; loop = tool loop", "engine.py, Agent Builder", "built"),
    ("Admission-manager agent that refuses to quote fees", "7 Jul", "Admission demo agent + Tester checks the rules", "Demo Gallery: DSP Digital Services", "built"),
    ("Order-taking agent (Mario Pizza / restaurant)", "4 Aug, 31 Jul", "Pizza agent with cart, delivery rule, order record", "Demo Gallery: Mario's Pizza", "built"),
    ("Booking agent (rent-a-car, clinic)", "14 Aug", "Speedy Rentals and CarePlus Clinic agents", "Demo Gallery", "built"),
    ("Lead agent (real estate, sales)", "27 Aug", "Skyline Estates viewing-request agent", "Demo Gallery", "built"),
    ("Business website with chat widget", "10 Jul, 16 Jul, 22 Jul", "Every business gets a live site + chat + menu", "/site/<id>", "built"),
    ("Backend / MVP (not a static page)", "17 Aug", "Python API, saved orders/leads, dashboard", "server.py", "built"),
    ("Facts in ONE place (no conflicting prices)", "9 Jul, 21 Aug", "Each business file is the single source of truth", "studio/agents/*.json", "built"),
    ("Hallucination guard: say 'I don't know'", "7 Jul, 3 Sep", "Unknown questions are logged for call-back; never guesses", "Chats & Call-backs", "built"),
    ("Memory: short-term + long-term", "9 Jul, 31 Jul", "Session memory (cart, fields). Long-term customer memory is NOT built yet", "engine.py", "partial"),
    ("RAG: fetch only the relevant slice", "22-23 Aug", "Knowledge Bot: paste documents, ask questions, answers only from them", "Knowledge Bot", "built"),
    ("Testing with many questions before launch", "14 Aug (Day 5)", "Agent Tester runs 11-13 checks per agent", "Agent Tester", "built"),
    ("Security: .env, keys never public", "14 Aug, 21 Aug", "Security scan + .gitignore + keys only in .env", "Security", "built"),
    ("Git + GitHub for every project", "19 Aug", "Project is committed and pushed to GitHub", "repo", "built"),
    ("Deploy live (Vercel/Render)", "15 Aug, 29 Aug", "Runs locally. Going live needs a host + login on dashboard (see Security)", "-", "partial"),
    ("Multi-agent team (sales/marketing agents with shared context)", "31 Jul, 21 Aug", "AI Sales Team: qualifier -> follow-up drafter -> manager digest", "AI Sales Team", "built"),
    ("Email drafts (never sends automatically)", "16 Jul", "Follow-up drafts are marked DRAFT, nothing is sent", "AI Sales Team", "built"),
    ("Agent Builder: any business in minutes", "27 Aug", "Form -> agent + website + chat instantly", "Agent Builder", "built"),
    ("LMS / student portal", "2 Aug", "Academy portal with 5-day course and progress tracker", "/academy", "built"),
    ("WhatsApp agent", "3 Sep", "WhatsApp-style simulator + webhook code. Real WhatsApp needs Meta credentials; NOT tested live", "/whatsapp/<id>", "partial"),
    ("Voice agent (ElevenLabs)", "3 Sep", "Browser voice (mic + spoken replies) on every site. ElevenLabs NOT connected", "Site chat mic button", "partial"),
    ("Claude as the real brain", "All", "Works when ANTHROPIC_API_KEY is in studio/.env. Not tested with a real key", "engine.py", "needs key"),
    ("Sell outcomes, not 'AI agents'", "27 Aug", "Cold Email, Proposal and ROI all lead with results", "Sales Kit", "built"),
    ("Find clients worldwide (10 ways)", "27 Aug", "Client Finder: research prompt, search queries, 10 channels", "Sales Kit", "built"),
    ("Personalised cold email", "27 Aug", "Cold Email tool (English + Roman Urdu, DM, WhatsApp, follow-up)", "Sales Kit", "built"),
    ("Show client the cost saved + money earned", "27 Aug", "ROI calculator + one-line pitch", "Sales Kit", "built"),
    ("Free website audit as a hook", "27 Aug", "Audit tool fetches a real site and scores it", "Sales Kit", "built"),
    ("Client pipeline (teacher tracks 283 clients)", "27 Aug", "CRM board: New -> Contacted -> Demo -> Proposal -> Won/Lost", "CRM", "built"),
    ("Pricing (class range about $500 - $5,000)", "7 Jul", "3 packages you can edit in the proposal", "Sales Kit", "built"),
    ("Brand + website in one afternoon", "28 Aug", "Agent Builder creates site; full branding/logo work is NOT automated", "Agent Builder", "partial"),
    ("Notes from 11 videos without captions", "various", "Need Whisper transcription (slow). Their topics may add more", "-", "todo"),
]


# ---------------- http ----------------
def page(name):
    return open(os.path.join(STATIC, name), "rb").read()


class H(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def do_GET(self):
        u = urlparse(self.path)
        p, q = u.path, {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if p in ("/", "/studio"):
                return self.send(200, page("studio.html"), "text/html")
            if p.startswith("/site/"):
                return self.send(200, page("site.html"), "text/html")
            if p.startswith("/whatsapp/"):
                return self.send(200, page("whatsapp.html"), "text/html")
            if p == "/academy":
                return self.send(200, page("academy.html"), "text/html")
            if p == "/webhook/whatsapp":
                ok = q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == WA_VERIFY
                return self.send(200 if ok else 403, (q.get("hub.challenge", "") if ok else "forbidden").encode(), "text/plain")
            if p == "/api/status":
                return self.send(200, {"claude": bool(API_KEY), "model": MODEL, "whatsapp": bool(WA_TOKEN and WA_PHONE), "time": now()})
            if p == "/api/agents":
                return self.send(200, [summary(a) for a in agents().values()])
            if p.startswith("/api/agents/"):
                a = agents().get(p.split("/")[-1])
                return self.send(200 if a else 404, a or {"error": "not found"})
            if p == "/api/records":
                rows = [r for r in rd("records.json") if not q.get("biz") or r.get("biz") == q["biz"]]
                return self.send(200, rows[::-1])
            if p == "/api/chats":
                rows = [r for r in rd("chats.json") if not q.get("biz") or r.get("biz") == q["biz"]]
                return self.send(200, rows[::-1][:200])
            if p == "/api/questions":
                return self.send(200, rd("questions.json")[::-1])
            if p == "/api/drafts":
                return self.send(200, rd("drafts.json")[::-1])
            if p == "/api/crm":
                return self.send(200, rd("crm.json"))
            if p == "/api/kb":
                return self.send(200, rd("kb.json"))
            if p == "/api/security":
                return self.send(200, tools.security_scan())
            if p == "/api/coverage":
                return self.send(200, [dict(zip(("item", "when", "what", "where", "status"), c)) for c in COVERAGE])
            if p == "/api/overview":
                return self.send(200, self.overview())
            self.send(404, {"error": "not found"})
        except Exception as e:
            self.send(500, {"error": str(e)[:200]})

    def do_POST(self):
        p, d = urlparse(self.path).path, self.body()
        try:
            if p == "/api/chat":
                text = str(d.get("message", "")).strip()[:500]
                if not text:
                    return self.send(400, {"error": "empty"})
                reply, mode = chat(str(d.get("biz", "")), str(d.get("session", "anon"))[:40], text, d.get("channel", "web"))
                return self.send(200, {"reply": reply, "mode": mode})
            if p == "/webhook/whatsapp":
                return self.send(200, self.whatsapp_in(d))
            if p == "/api/agents":
                cfg = build_config(d)
                if cfg["id"] in agents() and not agents()[cfg["id"]].get("custom"):
                    return self.send(400, {"error": "That id belongs to a built-in demo. Use another name."})
                json.dump(cfg, open(os.path.join(AGENTS, cfg["id"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                return self.send(200, {"ok": True, "id": cfg["id"], "config": cfg})
            if p == "/api/agents/delete":
                a = agents().get(d.get("id", ""))
                if a and a.get("custom"):
                    os.remove(os.path.join(AGENTS, a["id"] + ".json"))
                    return self.send(200, {"ok": True})
                return self.send(400, {"error": "Only custom agents can be deleted."})
            if p == "/api/records/status":
                rows = rd("records.json")
                for r in rows:
                    if r["id"] == d.get("id"):
                        r["status"] = d.get("status", r["status"])
                wr("records.json", rows)
                return self.send(200, {"ok": True})
            if p == "/api/questions/resolve":
                rows = rd("questions.json")
                for r in rows:
                    if r["id"] == d.get("id"):
                        r["resolved"] = True
                wr("questions.json", rows)
                return self.send(200, {"ok": True})
            if p == "/api/test":
                ag = agents()
                ids = [d["biz"]] if d.get("biz") in ag else list(ag)
                out = []
                for i in ids:
                    fake = lambda rec, i=i: {"id": "TEST-0001", **rec, "fields": rec.get("fields", {}), "total": rec.get("total", 0), "delivery": rec.get("delivery", 0)}
                    out.append(tools.run_tests(ag[i], lambda: new_state("test"), fake, lambda q: None))
                return self.send(200, out)
            if p == "/api/team/run":
                return self.send(200, self.team_run())
            if p == "/api/roi":
                return self.send(200, tools.roi(d))
            if p == "/api/coldemail":
                return self.send(200, tools.cold_email(d))
            if p == "/api/finder":
                return self.send(200, tools.finder(d))
            if p == "/api/audit":
                return self.send(200, tools.audit(d.get("url", "")))
            if p == "/api/kb/add":
                title, text = (d.get("title") or "Document").strip()[:80], (d.get("text") or "").strip()
                if len(text) < 20:
                    return self.send(400, {"error": "Paste some text first (at least a sentence)."})
                add("kb.json", {"id": "D%d" % (len(rd("kb.json")) + 1), "title": title, "text": text[:60000], "time": now()})
                return self.send(200, {"ok": True})
            if p == "/api/kb/delete":
                wr("kb.json", [r for r in rd("kb.json") if r["id"] != d.get("id")])
                return self.send(200, {"ok": True})
            if p == "/api/kb/ask":
                res = tools.rag_ask(rd("kb.json"), d.get("question", ""))
                res["mode"] = "offline"
                if API_KEY and res["grounded"]:
                    try:
                        ctx = "\n---\n".join(s["text"] for s in res["sources"])
                        res["answer"] = claude_text("Answer ONLY from the context. If it is not there, say you don't know.", "Context:\n%s\n\nQuestion: %s" % (ctx, d.get("question", "")))
                        res["mode"] = "claude"
                    except Exception as e:
                        print("Claude RAG error:", str(e)[:100])
                if not res["grounded"]:
                    add("questions.json", {"id": "Q%d" % (len(rd("questions.json")) + 1), "time": now(), "biz": "kb", "biz_name": "Knowledge Bot", "question": d.get("question", "")[:300], "session": "kb", "resolved": False, "sample": False})
                return self.send(200, res)
            if p == "/api/crm/add":
                add("crm.json", {"id": "C%d" % (len(rd("crm.json")) + 1), "name": d.get("name", "Client")[:80], "industry": d.get("industry", ""), "contact": d.get("contact", ""), "source": d.get("source", ""),
                                 "stage": d.get("stage", "New"), "value": int(float(d.get("value") or 0)), "notes": d.get("notes", ""), "created": now(), "sample": False})
                return self.send(200, {"ok": True})
            if p == "/api/crm/update":
                rows = rd("crm.json")
                for r in rows:
                    if r["id"] == d.get("id"):
                        for k in ("stage", "notes", "value"):
                            if k in d:
                                r[k] = d[k]
                wr("crm.json", rows)
                return self.send(200, {"ok": True})
            if p == "/api/crm/delete":
                wr("crm.json", [r for r in rd("crm.json") if r["id"] != d.get("id")])
                return self.send(200, {"ok": True})
            if p == "/api/seed":
                return self.send(200, {"message": seed()})
            if p == "/api/reset_samples":
                return self.send(200, {"message": reset_samples()})
            self.send(404, {"error": "not found"})
        except Exception as e:
            self.send(500, {"error": str(e)[:200]})

    # ---- helpers ----
    def overview(self):
        ag, rec, qs, ch, crm = agents(), rd("records.json"), rd("questions.json"), rd("chats.json"), rd("crm.json")
        per = []
        for a in ag.values():
            rs = [r for r in rec if r["biz"] == a["id"]]
            per.append({**summary(a), "records": len(rs), "revenue": sum(r.get("total", 0) for r in rs), "chats": sum(1 for c in ch if c["biz"] == a["id"]),
                        "open_q": sum(1 for q in qs if q["biz"] == a["id"] and not q["resolved"])})
        stages = {}
        for c in crm:
            stages[c["stage"]] = stages.get(c["stage"], 0) + 1
        return {"agents": per, "records": len(rec), "revenue": sum(r.get("total", 0) for r in rec), "chats": len(ch), "open_questions": sum(1 for q in qs if not q["resolved"]),
                "crm_total": len(crm), "crm_value": sum(int(c.get("value") or 0) for c in crm if c["stage"] not in ("Lost",)), "crm_won": sum(int(c.get("value") or 0) for c in crm if c["stage"] == "Won"),
                "stages": stages, "latest": rec[::-1][:8], "hot": [r for r in rec if r.get("label_score") == "hot"][::-1][:5],
                "claude": bool(API_KEY), "whatsapp": bool(WA_TOKEN and WA_PHONE)}

    def team_run(self):
        ag, rec, drafts = agents(), rd("records.json"), rd("drafts.json")
        new = []
        for r in rec:
            if "label_score" not in r:
                s, lab, why = tools.qualify(r)
                r.update(score=s, label_score=lab, why=why)
                dr = {"id": "DR%d" % (len(drafts) + len(new) + 1), "time": now(), "biz": r["biz"], "record": r["id"], "to": r["fields"].get("name", ""), "phone": r["fields"].get("phone", ""),
                      "text": tools.draft(r, r["biz_name"]), "status": "DRAFT - waiting for human approval", "sample": r.get("sample", False)}
                new.append(dr)
        wr("records.json", rec)
        wr("drafts.json", drafts + new)
        alld = drafts + new
        return {"processed": len(new), "records": [{"id": r["id"], "biz": r["biz_name"], "name": r["fields"].get("name", ""), "score": r["score"], "label": r["label_score"], "why": r["why"]} for r in rec if "score" in r][::-1][:40],
                "drafts": alld[::-1][:20], "digest": tools.digest(rec, rd("questions.json"), alld)}

    def whatsapp_in(self, d):
        try:
            biz = ENVG("WHATSAPP_BIZ") or next(iter(agents()))
            for e in d.get("entry", []):
                for c in e.get("changes", []):
                    for m in c.get("value", {}).get("messages", []):
                        if m.get("type") == "text":
                            reply, _ = chat(biz, "wa:" + m["from"], m["text"]["body"], "whatsapp")
                            if WA_TOKEN and WA_PHONE:
                                body = json.dumps({"messaging_product": "whatsapp", "to": m["from"], "type": "text", "text": {"body": reply}}).encode()
                                req = urllib.request.Request("https://graph.facebook.com/v20.0/%s/messages" % WA_PHONE, data=body,
                                                             headers={"Authorization": "Bearer " + WA_TOKEN, "Content-Type": "application/json"})
                                urllib.request.urlopen(req, timeout=20)
        except Exception as ex:
            print("whatsapp error:", str(ex)[:150])
        return {"status": "ok"}

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("DSP Agent Studio on http://127.0.0.1:8000   (Claude brain: %s, WhatsApp: %s)" % (MODEL if API_KEY else "off - offline engine", "on" if WA_TOKEN else "off"))
    ThreadingHTTPServer(("127.0.0.1", 8000), H).serve_forever()
