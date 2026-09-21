# Mario's Pizza - demo website + chatbot + ordering agent

A complete small system built from the bootcamp formula: **Agent = Brain + Job description + Tools + Loop**.

| Part | File | What it is |
|---|---|---|
| Frontend | `static/index.html` | Business website with menu and a chat widget |
| Backend | `server.py` | Python (no packages needed): serves the site, `/api/chat`, stores orders |
| Job description | `system_prompt()` in `server.py` + `knowledge.json` | Role, goal, audience, tone, rules, business facts (single source of truth) |
| Tool | `place_order` | Saves a confirmed order (name, phone, address, items) |
| Loop | `claude_agent()` | Keeps calling Claude while it asks for a tool |
| Dashboard | `static/admin.html` (`/admin`) | Orders, revenue, questions the agent could not answer, recent chats |

## Run
```
python demo/server.py
```
Open http://127.0.0.1:8000 (website) and http://127.0.0.1:8000/admin (owner dashboard).

## Two brains
- **Offline mode (default):** a rule-based agent that answers only from `knowledge.json`, takes orders step by step (English + Roman Urdu) and logs questions it cannot answer. No key, no cost.
- **Claude mode:** copy `demo/.env.example` to `demo/.env` and add `ANTHROPIC_API_KEY`. `.env` is git-ignored, so the key is never uploaded. The agent then uses Claude with the `place_order` tool. (Claude mode was written to the API spec but not tested with a real key.)

## Selling it
Change `knowledge.json` (name, menu, hours, delivery, offers, rules) to fit another business: clinic, salon, real estate, car rental. Pitch the outcome: no lead is lost, orders are taken 24/7, staff only get real orders and a call-back list.

## Known limits (demo)
No login on `/admin` (it listens on 127.0.0.1 only), data is stored in `demo/data/*.json`, no WhatsApp/voice yet (next step: WhatsApp Cloud API through Meta, ElevenLabs for voice).
