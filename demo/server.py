"""Mario's Pizza demo: website + chatbot + ordering agent + admin dashboard.
Run:  python demo/server.py      then open http://127.0.0.1:8000
Brain: Claude (if ANTHROPIC_API_KEY is in demo/.env) else an offline rule-based agent.
Formula: Brain + Job description (system prompt) + Tools (place_order) + Loop (tool loop).
"""
import json, os, re, time, threading, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
STATIC = os.path.join(BASE, "static")
os.makedirs(DATA, exist_ok=True)
KB = json.load(open(os.path.join(BASE, "knowledge.json"), encoding="utf-8"))
MENU = {m["id"]: m for m in KB["menu"]}
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
API_KEY = ENV.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = ENV.get("CLAUDE_MODEL", "claude-sonnet-5")


# ---------- storage ----------
def read(name):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def append(name, item):
    with LOCK:
        rows = read(name)
        rows.append(item)
        json.dump(rows, open(os.path.join(DATA, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def total_of(cart):
    sub = sum(MENU[i]["price"] * q for i, q in cart.items())
    delivery = 0 if sub >= 2000 or sub == 0 else 200
    return sub, delivery


def place_order(name, phone, address, cart, channel):
    sub, delivery = total_of(cart)
    order = {"id": "M%04d" % (len(read("orders.json")) + 1), "time": now(), "name": name, "phone": phone,
             "address": address, "items": {MENU[i]["name"]: q for i, q in cart.items()},
             "subtotal": sub, "delivery": delivery, "total": sub + delivery, "channel": channel}
    append("orders.json", order)
    return order


# ---------- offline agent (no API key needed) ----------
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "aik": 1, "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5}
RU = ["kya", "hai", "chahiye", "kitni", "kitna", "kab", "kahan", "mujhe", "aap", "hain", "nahi", "karo", "dein", "bhai", "shukriya", "lena"]
T = {
    "hi": ("Hi! Welcome to {n}. I can show the menu, take your order, or answer questions about delivery and timings. What would you like?",
           "Assalam o Alaikum! {n} mein khush amdeed. Main menu bata sakta hoon, order le sakta hoon, ya delivery/timing ke sawal ka jawab de sakta hoon. Kya chahiye?"),
    "hours": ("We are open: {v}.", "Hamara waqt: {v}."),
    "delivery": ("{v}", "{v}"),
    "address": ("You can find us at {v}. Phone: {p}.", "Hamara pata: {v}. Phone: {p}."),
    "payment": ("Payment: {v}", "Payment: {v}"),
    "offer": ("Current offer: {v}", "Maujooda offer: {v}"),
    "nooffer": ("I only know the offers listed here, so I can't promise other discounts.", "Mere paas sirf listed offers hain, is liye main koi aur discount promise nahi kar sakta."),
    "empty": ("Your cart is empty. Tell me what you'd like, e.g. '2 margherita and a cola'.", "Cart khali hai. Bata dein kya chahiye, jaise '2 margherita aur aik cola'."),
    "added": ("Added. {c}\nAnything else? Say 'confirm' to place the order.", "Add ho gaya. {c}\nAur kuch? Order ke liye 'confirm' likhein."),
    "ask_name": ("Great! What's your name?", "Zabardast! Aap ka naam?"),
    "ask_phone": ("Thanks {v}. Your phone number?", "Shukriya {v}. Aap ka phone number?"),
    "bad_phone": ("That phone number doesn't look right. Please send digits only.", "Phone number theek nahi lag raha. Sirf digits likhein."),
    "ask_addr": ("Delivery address?", "Delivery ka pata?"),
    "done": ("Order {id} placed! Total Rs {t} (delivery Rs {d}). We'll call {p} to confirm. Thank you!",
             "Order {id} lag gaya! Total Rs {t} (delivery Rs {d}). Hum {p} par call karke confirm karenge. Shukriya!"),
    "cleared": ("Cart cleared.", "Cart khali kar diya."),
    "unknown": ("I'm sorry, I don't have that information, and I don't want to guess. I've noted your question so our staff can call you back - or call us on {p}.",
                "Maazrat, mere paas ye maloomat nahi aur main andaza nahi lagana chahta. Aap ka sawal note kar liya hai, staff aap ko call karega - ya humein {p} par call karein."),
}


def is_ru(text):
    w = re.findall(r"[a-z]+", text.lower())
    return sum(1 for x in w if x in RU) >= 1


def find_items(text):
    t = " " + text.lower() + " "
    found = {}
    for m in KB["menu"]:
        for a in sorted(m["aliases"], key=len, reverse=True):
            i = t.find(a)
            if i >= 0:
                before = re.findall(r"[a-z0-9]+", t[max(0, i - 12):i])
                q = 1
                if before:
                    b = before[-1]
                    q = int(b) if b.isdigit() else NUM.get(b, 1)
                found[m["id"]] = max(1, min(q, 20))
                t = t[:i] + " " * len(a) + t[i + len(a):]
                break
    return found


def cart_text(cart):
    lines = ["%d x %s = Rs %d" % (q, MENU[i]["name"], MENU[i]["price"] * q) for i, q in cart.items()]
    s, d = total_of(cart)
    return "; ".join(lines) + " | Subtotal Rs %d, delivery Rs %d, total Rs %d." % (s, d, s + d)


def offline_agent(st, text):
    ru = is_ru(text)
    L = lambda k, **kw: T[k][1 if ru else 0].format(**{"n": KB["business"]["name"], "p": KB["business"]["phone"], **kw})
    low = text.lower().strip()
    b = KB["business"]
    stage = st.get("stage")
    if stage == "name":
        st["name"], st["stage"] = text.strip()[:60], "phone"
        return L("ask_phone", v=st["name"])
    if stage == "phone":
        digits = re.sub(r"\D", "", text)
        if not 10 <= len(digits) <= 15:
            return L("bad_phone")
        st["phone"], st["stage"] = digits, "address"
        return L("ask_addr")
    if stage == "address":
        st["stage"] = None
        o = place_order(st["name"], st["phone"], text.strip()[:200], st["cart"], "offline-agent")
        st["cart"] = {}
        return L("done", id=o["id"], t=o["total"], d=o["delivery"], p=o["phone"])
    if re.search(r"\b(cancel|clear|reset|khali)\b", low):
        st["cart"] = {}
        return L("cleared")
    if re.search(r"\b(confirm|checkout|place order|that's all|thats all|bas|done)\b", low):
        if not st["cart"]:
            return L("empty")
        st["stage"] = "name"
        return L("ask_name")
    if re.search(r"\b(cart|my order|bill)\b", low):
        return cart_text(st["cart"]) if st["cart"] else L("empty")
    if re.search(r"\b(discount|offer|deal|sasta|raiyat)\b", low):
        return L("offer", v=" ".join(b["offers"])) if b["offers"] else L("nooffer")
    if re.search(r"\b(hour|hours|time|timing|open|close|kab|waqt)\b", low) and "deliver" not in low:
        return L("hours", v=b["hours"])
    if re.search(r"\b(deliver|delivery|charges|fee|free)\b", low):
        return L("delivery", v=b["delivery"])
    if re.search(r"\b(address|location|where|kahan|pata)\b", low):
        return L("address", v=b["address"])
    if re.search(r"\b(pay|payment|cash|card|bank)\b", low):
        return L("payment", v=b["payment"])
    items = find_items(text)
    if items and not re.search(r"\b(price|kitne|kitni|kitna|how much|cost)\b", low):
        for i, q in items.items():
            st["cart"][i] = st["cart"].get(i, 0) + q
        return L("added", c=cart_text(st["cart"]))
    if re.search(r"\b(menu|price|prices|kitne|kitni|kitna|how much|cost|list|kya hai|pizzas?)\b", low) or items:
        pick = [MENU[i] for i in items] if items else KB["menu"]
        return "\n".join("%s - Rs %d (%s)" % (m["name"], m["price"], m["desc"]) for m in pick)
    if re.search(r"\b(hi|hello|hey|salam|assalam|aoa)\b", low):
        return L("hi")
    append("questions.json", {"time": now(), "question": text[:300], "session": st.get("sid")})
    return L("unknown")


# ---------- Claude agent (brain + job description + tool + loop) ----------
def system_prompt():
    b = KB["business"]
    menu = "\n".join("- %s: Rs %d (%s)" % (m["name"], m["price"], m["desc"]) for m in KB["menu"])
    return ("ROLE: You are the ordering assistant of %s in %s.\n"
            "GOAL: Help visitors choose food, answer questions and take delivery orders. When the customer has confirmed items, "
            "collect name, phone and address, then call the place_order tool.\n"
            "AUDIENCE: Hungry customers, some write in Roman Urdu.\nTONE: Friendly, short, clear. Reply in the customer's language.\n"
            "RULES:\n%s\n\nBUSINESS INFO\nHours: %s\nDelivery: %s\nPayment: %s\nAddress: %s\nOffers: %s\n\nMENU\n%s\n"
            % (b["name"], b["city"], "\n".join("- " + r for r in KB["rules"]), b["hours"], b["delivery"], b["payment"],
               b["address"], "; ".join(b["offers"]) or "none", menu))


TOOLS = [{
    "name": "place_order",
    "description": "Place a confirmed delivery order. Call only after the customer confirmed items and gave name, phone and address.",
    "input_schema": {"type": "object", "properties": {
        "name": {"type": "string"}, "phone": {"type": "string"}, "address": {"type": "string"},
        "items": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string", "enum": list(MENU)}, "qty": {"type": "integer", "minimum": 1}},
            "required": ["id", "qty"]}}},
        "required": ["name", "phone", "address", "items"]}}]


def claude_call(messages):
    body = json.dumps({"model": MODEL, "max_tokens": 700, "system": system_prompt(), "tools": TOOLS, "messages": messages}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def claude_agent(st, text):
    msgs = st.setdefault("history", [])
    msgs.append({"role": "user", "content": text})
    for _ in range(5):  # the LOOP: keep going while the model wants to use a tool
        r = claude_call(msgs[-20:])
        msgs.append({"role": "assistant", "content": r["content"]})
        if r.get("stop_reason") != "tool_use":
            return "".join(b.get("text", "") for b in r["content"]).strip() or "..."
        results = []
        for b in r["content"]:
            if b["type"] == "tool_use":
                a = b["input"]
                cart = {i["id"]: int(i["qty"]) for i in a.get("items", []) if i.get("id") in MENU}
                o = place_order(a.get("name", ""), a.get("phone", ""), a.get("address", ""), cart, "claude-agent")
                results.append({"type": "tool_result", "tool_use_id": b["id"],
                                "content": "Order %s saved. Total Rs %d." % (o["id"], o["total"])})
        msgs.append({"role": "user", "content": results})
    return "Sorry, something went wrong."


SESSIONS = {}


def chat(sid, text):
    st = SESSIONS.setdefault(sid, {"cart": {}, "stage": None, "sid": sid})
    if API_KEY:
        try:
            reply, mode = claude_agent(st, text), "claude"
        except Exception as e:
            print("Claude error, using offline agent:", e)
            reply, mode = offline_agent(st, text), "offline"
    else:
        reply, mode = offline_agent(st, text), "offline"
    append("chats.json", {"time": now(), "session": sid, "user": text[:500], "bot": reply[:800], "mode": mode})
    return reply, mode


# ---------- http ----------
class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            return self._send(200, open(os.path.join(STATIC, "index.html"), "rb").read(), "text/html")
        if p == "/admin":
            return self._send(200, open(os.path.join(STATIC, "admin.html"), "rb").read(), "text/html")
        if p == "/api/knowledge":
            return self._send(200, {"business": KB["business"], "menu": KB["menu"], "mode": "claude" if API_KEY else "offline"})
        if p == "/api/admin":
            return self._send(200, {"orders": read("orders.json")[::-1], "questions": read("questions.json")[::-1],
                                    "chats": read("chats.json")[::-1][:60], "mode": "claude" if API_KEY else "offline"})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/chat":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0))
        try:
            d = json.loads(self.rfile.read(n) or b"{}")
            sid, text = str(d.get("session", "anon"))[:40], str(d.get("message", "")).strip()[:500]
        except Exception:
            return self._send(400, {"error": "bad json"})
        if not text:
            return self._send(400, {"error": "empty"})
        reply, mode = chat(sid, text)
        self._send(200, {"reply": reply, "mode": mode})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("Mario's Pizza demo on http://127.0.0.1:8000  (agent brain: %s)" % ("Claude " + MODEL if API_KEY else "offline rules"))
    ThreadingHTTPServer(("127.0.0.1", 8000), H).serve_forever()
