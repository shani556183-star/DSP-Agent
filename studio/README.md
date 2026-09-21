# DSP Agent Studio

Everything from the bootcamp in one local app: client demos (website + chatbot + agent + backend), an owner dashboard, and the tools to sell it.

## Run
```
python studio/server.py
```
Open http://127.0.0.1:8000 (no packages needed, Python 3.9+).

## What is inside
| Area | Where |
|---|---|
| 5 client demos: Mario's Pizza (orders), DSP admission (leads), Skyline Estates (leads), Speedy Rentals (bookings), CarePlus Clinic (bookings) | Studio > Demo Gallery, `/site/<id>` |
| Website with chat + voice (mic, spoken replies) | `/site/<id>` |
| WhatsApp-style view + real webhook code | `/whatsapp/<id>`, `/webhook/whatsapp` |
| Any new business in minutes | Studio > Agent Builder |
| Test before delivery (FAQ, prices, discount trap, off-topic, prompt injection, full flow) | Studio > Agent Tester |
| Orders, leads, bookings, call-backs, CSV export | Studio > Orders & Leads, Chats & Call-backs |
| Qualifier -> follow-up drafts -> manager digest (drafts only, never sent) | Studio > AI Sales Team |
| RAG: answers only from your documents | Studio > Knowledge Bot |
| Client Finder, Cold Email, ROI, Website Audit, Proposal, Pricing | Studio > Sales Kit |
| Client pipeline | Studio > Client CRM |
| Key/secret scan of the project | Studio > Security |
| What the teacher taught vs what exists (honest status) | Studio > Class Coverage |
| 10-minute client meeting script + objection answers | Studio > Demo Script |
| 5-day course portal with progress and certificate | `/academy` |

## Agent formula (used by every agent)
Brain (Claude or the offline engine) + Job description (Role, Goal, Audience, Tone, Rules in `studio/agents/<id>.json`) + Tools (`save_record`) + Loop (`engine.claude_agent`).

## Keys (optional) - `studio/.env`, never committed
```
ANTHROPIC_API_KEY=...        # switches the brain to Claude
CLAUDE_MODEL=claude-sonnet-5
WHATSAPP_TOKEN=...           # Meta WhatsApp Cloud API
WHATSAPP_PHONE_ID=...
WHATSAPP_VERIFY_TOKEN=...    # you choose it, paste the same in Meta
WHATSAPP_BIZ=pizza           # which business answers on WhatsApp
```

## Honest limits
- Claude mode and real WhatsApp are written to the API specs but were **not tested with real credentials**.
- Voice uses the browser (Chrome/Edge); ElevenLabs is not connected.
- The dashboard has no login. Add one (or host access control) before putting it on the internet.
- Business data, prices and contact numbers in the demos are fictional.
- Data is stored in `studio/data/*.json` (git-ignored). Use Overview > Load / Remove sample data for demos.
