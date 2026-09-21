"""Agent engine: one generic agent that is configured by a JSON file (studio/agents/<id>.json).
Formula from the bootcamp:  Agent = Brain + Job description + Tools + Loop.
  Brain            -> Claude (when ANTHROPIC_API_KEY is set) or the offline rule engine below
  Job description  -> system_prompt(): Role, Goal, Audience, Tone, Rules + business facts
  Tools            -> save_record (order / booking / lead)
  Loop             -> claude_agent(): keeps calling Claude while it wants to use a tool
"""
import json, re, urllib.request

NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "aik": 1, "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5}
RU = {"kya", "hai", "chahiye", "kitni", "kitna", "kitne", "kab", "kahan", "mujhe", "aap", "hain", "nahi", "karo", "dein", "bhai",
      "shukriya", "lena", "chahta", "chahti", "kaise", "kaun", "kis", "aaj", "kal", "batao", "bataen", "kar", "sakte", "milega"}

M = {  # (English, Roman Urdu)
    "hi": ("Hi! Welcome to {n}. {g}", "Assalam o Alaikum! {n} mein khush amdeed. {g}"),
    "empty": ("Your list is empty. Tell me what you need, for example: {ex}.", "List khali hai. Bata dein kya chahiye, jaise: {ex}."),
    "added": ("Added. {c}\nAnything else? Say 'confirm' to place the order.", "Add ho gaya. {c}\nAur kuch? Order ke liye 'confirm' likhein."),
    "bad_phone": ("That phone number doesn't look right. Please send 10 to 15 digits.", "Phone number theek nahi lag raha. 10 se 15 digits likhein."),
    "bad_item": ("Please choose one of these:\n{o}", "In mein se chun lein:\n{o}"),
    "done_order": ("Order {id} placed! Total {cur} {t} (delivery {cur} {d}). We'll call {p} to confirm. Thank you!",
                   "Order {id} lag gaya! Total {cur} {t} (delivery {cur} {d}). Hum {p} par call karke confirm karenge. Shukriya!"),
    "done_rec": ("Done! Your {lab} {id} is recorded. Our team will contact you on {p}. Thank you!",
                 "Ho gaya! Aap ka {lab} {id} darj ho gaya. Hamari team {p} par rabta karegi. Shukriya!"),
    "cleared": ("Cancelled. Anything else I can help with?", "Cancel kar diya. Aur kuch madad chahiye?"),
    "nooffer": ("I only know the offers listed here, so I can't promise other discounts.", "Mere paas sirf listed offers hain, is liye main koi aur discount promise nahi kar sakta."),
    "offer": ("Current offer: {v}", "Maujooda offer: {v}"),
    "unknown": ("I'm sorry, I don't have that information and I don't want to guess. I've noted your question so our team can call you back, or call us on {p}.",
                "Maazrat, mere paas ye maloomat nahi aur main andaza nahi lagana chahta. Aap ka sawal note kar liya hai, team aap ko call karegi, ya humein {p} par call karein."),
    "hours": ("Our timings: {v}.", "Hamara waqt: {v}."),
    "address": ("You can find us at: {v}. Phone: {p}.", "Hamara pata: {v}. Phone: {p}."),
}
GREETING = re.compile(r"\b(hi|hello|hey|salam|assalam|aoa|good morning|good evening)\b")
DISCOUNT = re.compile(r"\b(discount|offer|offers|deal|deals|sasta|raiyat|concession)\b")
CONFIRM = re.compile(r"\b(confirm|checkout|place order|that's all|thats all|bas|done|order karo)\b")
CANCEL = re.compile(r"\b(cancel|clear|reset|khali|start over)\b")
CARTV = re.compile(r"\b(cart|my order|bill|total)\b")
PRICEQ = re.compile(r"\b(price|prices|kitne|kitni|kitna|how much|cost|rate|rates|charges?)\b")
LISTQ = re.compile(r"\b(menu|list|options|available|kya hai|what do you have|show|dikhao|services|cars|properties|courses|catalog)\b")
HOURS = re.compile(r"\b(hour|hours|timing|timings|open|close|closing|kab|waqt)\b")
ADDR = re.compile(r"\b(address|location|where|kahan|pata|map)\b")


def toks(s):
    return re.findall(r"[a-z0-9']+", s.lower())


def is_ru(text):
    return any(w in RU for w in toks(text))


def word(k, low):
    return re.search(r"\b" + re.escape(k.lower()) + r"\b", low) is not None


def money(biz, v):
    return "%s %s" % (biz.get("currency", "Rs"), format(int(v), ","))


def item_line(biz, m):
    price = "" if m.get("price") in (None, "") else " - %s%s" % (money(biz, m["price"]), m.get("price_note", ""))
    return "%s%s (%s)" % (m["name"], price, m.get("desc", "")) if m.get("desc") else "%s%s" % (m["name"], price)


def find_items(biz, text):
    t = " " + text.lower() + " "
    found = {}
    for m in biz.get("catalog", []):
        aliases = m.get("aliases") or [m["name"].lower()]
        for a in sorted(aliases, key=len, reverse=True):
            i = t.find(a.lower())
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


def cart_total(biz, cart):
    by = {m["id"]: m for m in biz.get("catalog", [])}
    sub = sum((by[i].get("price") or 0) * q for i, q in cart.items() if i in by)
    fee, free_above = biz.get("delivery_fee", 0), biz.get("free_delivery_above", 0)
    delivery = 0 if (not sub or (free_above and sub >= free_above)) else fee
    return sub, delivery


def cart_text(biz, cart):
    by = {m["id"]: m for m in biz.get("catalog", [])}
    lines = ["%d x %s = %s" % (q, by[i]["name"], money(biz, (by[i].get("price") or 0) * q)) for i, q in cart.items() if i in by]
    s, d = cart_total(biz, cart)
    return "; ".join(lines) + " | Subtotal %s, delivery %s, total %s." % (money(biz, s), money(biz, d), money(biz, s + d))


def next_field(biz, st):
    for f in biz["flow"]["fields"]:
        if f["key"] not in st["fields"]:
            return f
    return None


def ask(biz, st, f):
    q = f.get("ask_ur") if st.get("ru") and f.get("ask_ur") else f.get("ask_en", "Please share your " + f["key"] + "?")
    if f.get("type") == "catalog":
        q += "\n" + "\n".join("- " + item_line(biz, m) for m in biz.get("catalog", []))
    return q


def finish(biz, st, save_record):
    fl = biz["flow"]
    rec = {"type": fl["type"], "label": fl.get("record_label", "Request"), "fields": dict(st["fields"])}
    if fl["type"] == "order":
        by = {m["id"]: m for m in biz["catalog"]}
        rec["items"] = {by[i]["name"]: q for i, q in st["cart"].items() if i in by}
        sub, dl = cart_total(biz, st["cart"])
        rec.update(subtotal=sub, delivery=dl, total=sub + dl)
    r = save_record(rec)
    ru = st.get("ru")
    st.update(cart={}, fields={}, collecting=False)
    phone = r["fields"].get("phone", biz.get("phone", ""))
    if fl["type"] == "order":
        return M["done_order"][1 if ru else 0].format(id=r["id"], cur=biz.get("currency", "Rs"), t=format(r["total"], ","), d=format(r["delivery"], ","), p=phone)
    return M["done_rec"][1 if ru else 0].format(lab=rec["label"].lower(), id=r["id"], p=phone)


def start_flow(biz, st, text, save_record):
    st.update(collecting=True, fields={})
    pre = find_items(biz, text)
    for f in biz["flow"]["fields"]:
        if f.get("type") == "catalog" and pre:
            st["fields"][f["key"]] = next((m["name"] for m in biz["catalog"] if m["id"] in pre), "")
    f = next_field(biz, st)
    return finish(biz, st, save_record) if f is None else ask(biz, st, f)


def offline_reply(biz, st, text, save_record, log_question):
    st.setdefault("cart", {}), st.setdefault("fields", {})
    st["ru"] = bool(st.get("ru")) or is_ru(text)
    ru = 1 if st["ru"] else 0
    low = text.lower().strip()
    fl = biz["flow"]
    ph = biz.get("phone", "")
    t = lambda k, **kw: M[k][ru].format(**{"n": biz["name"], "p": ph, "g": biz.get("greeting", ""), **kw})

    if st.get("collecting"):                      # slot filling
        if CANCEL.search(low):
            st.update(collecting=False, fields={}, cart={})
            return t("cleared")
        f = next_field(biz, st)
        if f is None:
            return finish(biz, st, save_record)
        v = text.strip()[:200]
        if f.get("type") == "phone":
            digits = re.sub(r"\D", "", v)
            if not 10 <= len(digits) <= 15:
                return t("bad_phone")
            v = digits
        elif f.get("type") == "catalog":
            got = find_items(biz, v)
            if not got:
                return t("bad_item", o="\n".join("- " + item_line(biz, m) for m in biz["catalog"]))
            v = next(m["name"] for m in biz["catalog"] if m["id"] in got)
        st["fields"][f["key"]] = v
        nf = next_field(biz, st)
        return finish(biz, st, save_record) if nf is None else ask(biz, st, nf)

    if CANCEL.search(low):
        st.update(cart={}, fields={})
        return t("cleared")
    if fl["type"] == "order" and CONFIRM.search(low):
        if not st["cart"]:
            return t("empty", ex=fl.get("example", "2 items"))
        return start_flow(biz, st, "", save_record)
    if fl["type"] == "order" and CARTV.search(low):
        return cart_text(biz, st["cart"]) if st["cart"] else t("empty", ex=fl.get("example", "2 items"))
    if DISCOUNT.search(low):
        offers = biz.get("offers", [])
        return t("offer", v=" ".join(offers)) if offers else t("nooffer")

    for e in biz.get("faq", []):                  # facts from the business file (single source of truth)
        if any(word(k, low) for k in e["keys"]):
            return e.get("a_ur") if ru and e.get("a_ur") else e["a"]

    items = find_items(biz, text)
    if items and fl["type"] == "order" and not PRICEQ.search(low):
        for i, q in items.items():
            st["cart"][i] = st["cart"].get(i, 0) + q
        return t("added", c=cart_text(biz, st["cart"]))
    if items and PRICEQ.search(low):
        return "\n".join(item_line(biz, m) for m in biz["catalog"] if m["id"] in items)
    if fl["type"] in ("booking", "lead") and any(word(k, low) for k in fl.get("triggers", [])):
        return start_flow(biz, st, text, save_record)
    if PRICEQ.search(low) or LISTQ.search(low) or items:
        return "\n".join(item_line(biz, m) for m in biz.get("catalog", [])) or t("unknown")
    if HOURS.search(low) and biz.get("hours"):
        return t("hours", v=biz["hours"])
    if ADDR.search(low) and biz.get("address"):
        return t("address", v=biz["address"])
    if GREETING.search(low) and len(toks(low)) <= 5:
        return t("hi")
    log_question(text)
    return t("unknown")


# ---------------- Claude brain ----------------
def system_prompt(biz):
    cat = "\n".join("- " + item_line(biz, m) for m in biz.get("catalog", [])) or "(none)"
    faq = "\n".join("- %s: %s" % (", ".join(e["keys"][:3]), e["a"]) for e in biz.get("faq", []))
    fields = ", ".join(f["key"] for f in biz["flow"]["fields"])
    return (
        "ROLE: %s\nGOAL: %s\nAUDIENCE: %s\nTONE: %s\nRULES:\n%s\n\n"
        "BUSINESS: %s (%s). Phone %s. Address %s. Hours %s. Offers: %s\n\nCATALOG (%s)\n%s\n\nFACTS\n%s\n\n"
        "TASK: When the customer confirmed what they want and you have these details (%s), call the save_record tool. "
        "Never guess missing facts; if unknown, say so and offer a call back."
        % (biz.get("role", "Assistant of " + biz["name"]), biz.get("goal", ""), biz.get("audience", ""), biz.get("tone", "Friendly, short, clear."),
           "\n".join("- " + r for r in biz.get("rules", [])), biz["name"], biz.get("city", ""), biz.get("phone", ""), biz.get("address", ""),
           biz.get("hours", ""), "; ".join(biz.get("offers", [])) or "none", biz.get("catalog_label", "Catalog"), cat, faq, fields))


def tools_for(biz):
    props = {f["key"]: {"type": "string"} for f in biz["flow"]["fields"]}
    schema = {"type": "object", "properties": {"fields": {"type": "object", "properties": props, "required": list(props)}}, "required": ["fields"]}
    if biz["flow"]["type"] == "order":
        schema["properties"]["items"] = {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string", "enum": [m["id"] for m in biz["catalog"]]}, "qty": {"type": "integer", "minimum": 1}}, "required": ["id", "qty"]}}
        schema["required"].append("items")
    return [{"name": "save_record", "description": "Save the confirmed %s." % biz["flow"].get("record_label", "request").lower(), "input_schema": schema}]


def claude_call(biz, messages, key, model):
    body = json.dumps({"model": model, "max_tokens": 700, "system": system_prompt(biz), "tools": tools_for(biz), "messages": messages}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def claude_agent(biz, st, text, save_record, key, model):
    msgs = st.setdefault("history", [])
    msgs.append({"role": "user", "content": text})
    for _ in range(5):                            # the LOOP
        r = claude_call(biz, msgs[-20:], key, model)
        msgs.append({"role": "assistant", "content": r["content"]})
        if r.get("stop_reason") != "tool_use":
            return "".join(b.get("text", "") for b in r["content"]).strip() or "..."
        out = []
        for b in r["content"]:
            if b["type"] == "tool_use":
                a = b["input"]
                rec = {"type": biz["flow"]["type"], "label": biz["flow"].get("record_label", "Request"), "fields": a.get("fields", {})}
                if biz["flow"]["type"] == "order":
                    by = {m["id"]: m for m in biz["catalog"]}
                    cart = {i["id"]: int(i["qty"]) for i in a.get("items", []) if i.get("id") in by}
                    rec["items"] = {by[i]["name"]: q for i, q in cart.items()}
                    sub, dl = cart_total(biz, cart)
                    rec.update(subtotal=sub, delivery=dl, total=sub + dl)
                r2 = save_record(rec)
                out.append({"type": "tool_result", "tool_use_id": b["id"], "content": "Saved as %s." % r2["id"]})
        msgs.append({"role": "user", "content": out})
    return "Sorry, something went wrong."
