# DSP Bootcamp – notes (date-wise, running)

Source: YouTube auto-captions (Hindi script) in `out/`. Coverage per video is marked. Items under **BUILD** are things we could build.

## Core formula (repeated every class)
**Agent = Claude (brain) + Job Description + Tools (hands) + Loop.**
- Job description = Role, Goal, Audience, Tone, Rules (system prompt / "instructions").
- Memory + Context added on day 3. Specific beats clever: one task, one job.
- Testing / securing / deploying on day 5 (Friday).
- Hallucination trap: an agent that is "too helpful" with no facts will invent (e.g. a wrong price). Fix: put facts (prices etc.) in ONE place, and tell it not to guess.

## 07 Jul – class 1 (read fully)
AI vs chatbot vs agent, formula, 4 traits of a good agent (repeatable, rule-based, valuable, explainable), 3 mistakes (too broad, vague instruction, no specific goal).
- **BUILD:** "DSP Admission Manager" Claude Project (role/goal/audience/tone/rules; must refuse to quote fees).

## 08 Jul – class 2 (sampled)
Why build agents; agent = employee with job title; tools = "hands"; agent must have a job description of 7 parts; the teacher's own WhatsApp agent that answers seat-reservation questions for beginners/students/teachers/marketers.
- **BUILD:** WhatsApp seat-reservation agent for a course/business.

## 09 Jul – class 3 (sampled)
Memory types: built-in vs injected (permanent) vs short-term. Context vs instructions. Model choice (strongest vs Sonnet). Never put conflicting prices in two places. Example from a student: boutique suit price 1.5 lakh – agent quoted a wrong price and lost a client.
- **BUILD:** agent with a facts/prices file + memory.

## 10 Jul – class 4 (sampled)
"Type plain English, software appears." Claude Code builds a single-page chat widget in plain HTML (greets visitor, explains bootcamp, validates email/name). Teacher's own "Get AI Sales / close deals while you sleep" system that posts daily on LinkedIn and gives weekly analysis. A `.md` project file holds what/who/audience for the whole project.
- **BUILD:** single-page chat website + lead capture form; project `.md` (CLAUDE.md) file; auto LinkedIn poster.

## 13 Jul – class 5 (sampled)
AI basics for new students; NotebookLM (free) to turn material into study aids; chatter vs worker AI; Claude Cowork and Claude Code; website built in ~2 minutes; Projects give memory; connectors/skills come later.
- **BUILD:** website in minutes; NotebookLM study pack.

## 14 Jul – Claude certification training (sampled)
What is Claude, 3 modes (Chat / Cowork / Code), prompts with role+task, artifacts, skills, connectors (Gmail, Drive), deep research. Free Anthropic-style course, students take certificates. Teacher: people who entered crypto in 2013 became millionaires – this is the same moment.
- **BUILD:** market-analysis report prompt (role + tasks + format); research reports with deep research.

## 16 Jul – Cowork (sampled)
Claude Cowork: drafts emails from Gmail (rule: DRAFT only, never send), reads a rules folder, scheduled tasks, Drive connector. Certificates come directly from Anthropic (DSP is not a partner).
- **BUILD:** daily email-drafting assistant with "never send" rules; scheduled daily tasks.

## 27 Aug – 10 Ways to Find Clients Worldwide (read intro ~ 25%)
Do NOT sell "AI agents/chatbots" – sell OUTCOMES (leads never lost, cost saved, revenue). Company budgets are ~70% marketing/sales. 5 bn people online, 3.5 bn on Meta apps. Don't wait for clients – find them. Claude does prospect research → personalised outreach → follow-up; the human adds personal touch and relationship. Teacher: SEO/marketing 24 yrs; London workshop £500/day. Has a client system showing 283 active clients.
- **BUILD:** global client pipeline (prospect research prompt by country + industry), outreach drafts, tracker.

(Notes for the remaining videos are appended below as they are read.)

## 16 Jul – Build a website in 30 min, free (sampled)
Google AI Studio (free, Gemini "high thinking") builds an app/website from an idea prompt; asks for a plan first; agent rule: "if you don't know, say I don't know – no invented prices" (wrong claims in the US carry consequences).
- **BUILD:** interactive "service finder" website for a digital-services program; voice agent idea.

## 21 Jul – AI, Agents, Agentic AI, Prompt (sampled)
Agent = "helper tool"; Agentic AI = mindset of letting AI think/run/test/finish multi-step projects alone. Hire an agent like an employee (job depends on the role). A Karachi-born founder's agent (Cursor) reached a ~$60bn deal. Bad prompt ("I want food") vs specific prompt. Safety: prefer Claude (a chatbot from another vendor gave harmful advice to teens).
- **BUILD:** role-specific agents (programmer, web dev, marketer …).

## 22 Jul – Claude / Cowork / Code (sampled)
Three surfaces: Chat, Cowork (works on your computer), Code. ChatGPT "invents answers confidently" -> always ask "is this data verified?". Agents must be steerable (guide/manage/control). Project "interview me" trick to write instructions.
- **BUILD:** Project with interview-style instruction builder; verification step in every research prompt.

## 22 & 23 Jul – Build website with Claude in 15 min (same recording appears twice; sampled)
Project + agent that answers ONLY from the knowledge base. Claude Code builds and hosts (Netlify-style, free); a domain costs ~$12/yr; "plan before build" step. Price-change rule: update the knowledge base, stop quoting the old number. Example client: Canadian artificial-jewellery seller who wants to go international after watching a video while driving.
- **BUILD:** business website + small chat agent + editable knowledge base (price list).

## 23 Jul – Context engineering (sampled)
Prompt engineering was last year's hype; context engineering = what goes into the model's limited window (tokens). 4 failures: context **poisoning** (a wrong output stays and repeats), **distraction**, and two more (confusion/clash – see 21 Aug); fixes: keep the highest-signal items, summarise, correct errors immediately. Short-term vs long-term memory; agent that checks your mailbox and meetings. Next course: "FDE – Forward Deployed Engineer".
- **BUILD:** agent with a curated memory file; email/meeting checker agent.

## 31 Jul – Discussion on practical project / Practical work (sampled)
Last week's project: the teacher built the marketing + sales team of the Digital Services Program with agents; ~90% of students built their own. Key point: 8-10 agents are useless unless each has a job description and they work together with shared context. Runtime facts (fee, time, course length, tools) must be available to the agent. Order-taking agent for a restaurant; long-term memory (customer likes sweets -> "last time you also had this drink"). RAG idea: fetch only the most relevant slice, not whole documents. Git vs GitHub explained (tracks every code change). A 9th-class student built his own AI "professors". Teacher's team built a phone ordering agent for an American client with **500 restaurants**.
- **BUILD:** multi-agent team (sales, marketing, admission) with shared context; restaurant order-taking + memory agent; GitHub repo for each project.

## 02 Aug – Build and publish websites live (sampled) and "No coding, no technical work"
Let Claude decide how many sub-agents + a main agent are needed; travel-agent spec generated by Claude; deploy on Vercel (or GitHub Pages/Netlify) and share an artifact link; a student built a full **LMS portal** with no prior knowledge (every module working); Google AI Studio is free; record your screen and turn it into a reusable **skill**; question about offline/secure deployment for security organisations; existing WordPress sites can stay.
- **BUILD:** LMS/student portal; travel-agent website; skill recorded from repeated work.

## 04 Aug – Claude Masterclass Part 2 (sampled)
Chat forgets when closed; Projects build a "relationship" (memory). Demo: "Mario Pizza" order-taker agent + second agent; Claude Code builds a 10-50 page website (front + back end); Cowork installs things after asking permission.
- **BUILD:** pizza/food order-taker agent pair; multi-page business website.

## 11 Aug – Next level of AI (sampled) and Masterclass Part 1 (sampled)
Worker analogy (ask-only vs plan vs autonomous); ML basics; LLM knowledge cut-off -> hallucination; **agent anatomy** needs planning (many students say "I built an agent" without knowing its job). Teacher warns: don't start building after class 1 – learn fundamentals or you waste money. Role example: "You are my SEO/digital-marketing expert for a net cafe". Before building a website ask: what is it for, what problem does it solve, who is the user; colours can be changed by one sentence.
- **BUILD:** SEO/digital-marketing expert agent for a local business (net cafe).

## 12 Aug – Claude fundamentals (sampled)
Project custom instructions (e.g. "science tutor for grade 7"), artifacts, **skills** = saved instructions, Dispatch (use Claude from the phone), interactive artifacts such as a periodic table.
- **BUILD:** science-tutor project + interactive study artifact.

## 14 Aug – Day 4 tools + Claude Code (sampled) and Day 5 "test, secure, deploy"
"From talking to doing." Claude Code can create the `.env` (API keys/passwords stay private, never public). Advice: build ONE small feature first, e.g. a **WhatsApp booking agent for a rent-a-car business**, put it live, test it well. Day 5: evaluation methods and 10 automated testing tools (DeepEval, Promptfoo …); test an agent with 100+ questions to see if it stays on purpose and tone; secure and deploy on Friday; weekend = final project.
- **BUILD:** rent-a-car WhatsApp booking agent; a test-question suite for every agent.

## 15 Aug – Zero to live deployment (sampled)
Baby-step practical: one main project folder; open Claude Code inside it; copy a ready prompt; no database at first (add later only if needed); make sure keys/placeholder names sit in the `.env` and are NOT published; then deploy.
- **BUILD:** first live agent site from the ready prompt (folder -> Claude Code -> GitHub -> Vercel).

## 17 Aug – Building real AI applications, Day 1 (sampled)
Teacher's own site made with Claude is static (cannot update without redeploy) vs a system with backend. Hiring an AI "employee" checks a week of email and replies; hidden tasks with sub-agents. Set up a clean project folder; build the cheapest **minimum viable product** and deploy it at the weekend.
- **BUILD:** MVP with a backend (not a static page).

## 19 Aug – AI myths vs reality: ChatGPT vs Claude vs Gemini (sampled)
Side-by-side tests (reasoning, "explain to a 10-year-old", science-scientist prompt, prioritisation, AI utilisation). Claude Code is best for coding; vibe coding = no coding skill needed. "Difference between using AI and being AI-skilled = turning output into real results."
- **BUILD:** a comparison test sheet that shows clients which model fits which job.

## 19 Aug – Frontend with Claude Code + GitHub (sampled)
`index.html` basics; **Git** = version history/safety net (if Claude crashes or breaks the code you can go back; keeps cost low, every change tracked); commit messages; GitHub as the online copy (Claude asks permission to check remotes).
- **BUILD:** the repo/commit workflow for every project (also needed to push this project).

## 21 Aug – Context engineering: 4 failures + fixes (sampled)
Mistakes multiply through the system (poisoning); garbage in = garbage out; what the model sees at run time matters; **4 pillars** to manage context layers; SEO agent team example (one agent on research, keywords, backlinks, on-page, off-page).
- **BUILD:** SEO multi-agent team (research / keywords / backlinks / on-page / off-page) as a sellable service.

## 21 Aug – API keys and .env (sampled)
Get an API key from the provider dashboard ("Get API key", name it e.g. *cafe bot*); keep it only in `.env`, never on GitHub; "the model only answers from its training data unless you give it tools"; future: personal AI assistants for everyone, autonomous one-person companies worth $1bn.
- **BUILD:** cafe-bot with a proper `.env` + `.gitignore` (we already did the .gitignore step for this repo).

## 21 Aug – Claude Projects: memory, instructions, context (sampled)
Rule: never write the same fact (e.g. consultancy fee) in two places (project instructions vs memory) – they will clash. Build order for a customer chatbot: web chat UI -> backend API -> system prompt -> order state; `/context` shows how many tokens system tools, system prompt, skills, messages use; Plan mode vs build mode.
- **BUILD:** customer web-chat + backend + order tracking agent.

## 21 Aug – Inside DSP (short Q&A, 17 min, sampled)
Student support call: front end unaffected if backend crashes; when to restart vs fix (to save tokens): first PLAN in Claude Chat, then give the plan to Cowork/Code to fix; install desktop software from Google download.

## 22 Aug – How RAG works (17 min, sampled) and 23 Aug – Perfect memory: RAG explained (sampled)
"AI doesn't know everything – it searches." RAG = retrieve only the exact relevant pages from your private data (turned into numbers/embeddings), give them to the model, so it doesn't need to memorise the whole database and doesn't hallucinate. Example: airline bot without RAG says "I don't have access to your booking"; with RAG it answers from the real record. Google NotebookLM shown as a no-code RAG (upload sources -> ask, or generate a slide deck).
- **BUILD:** RAG agent on a client's own documents (menu/policies/price list/FAQ); NotebookLM-based knowledge assistant; company knowledge bot.

## 24 Aug – Vibe coding: website, chatbot, agents (sampled)
Static website vs a site that reacts; social-media recommendation = AI everywhere; vibe coding = "describe the outcome in plain English – you are the director, Claude is the builder"; live WhatsApp demo: an agent handles a hiring conversation ("we have to hire Zara").
- **BUILD:** website + chatbot + WhatsApp agent bundle.

## 25 Aug – Claude Masterclass 2026: chatbot -> agent (sampled)
Four top LLMs; Claude leads. Projects hold files/connectors; Cowork sets up folders and suggests roles/plugins/connectors/skills itself; Claude Design for design work; **MCP** replaces per-software API integrations (old way broke when the model upgraded).
- **BUILD:** MCP/connector-based agent (Gmail, Drive, calendar) instead of hand-coded API glue.

## 27 Aug – 10 Ways to find clients (second half, keyword-sampled)
Channels named: Google prospect research (by country + industry), competitor & market research (Claude compares your price/value with the market; "same price, more value" or lower price), **personalised cold emails** (Claude writes as a "B2B cold-email copywriter" – rare in Pakistan but the norm worldwide), LinkedIn, website audits (free audit as a hook), social media, freelancer hubs, partnerships. Digital employee demo: replies to email, sends welcome, follows up, takes payment, updates the database; savings are calculated and shown to the client. Warning: many people have "wow" ideas but stay in a job – start earning.
- **BUILD:** prospect-research prompt pack; cold-email copywriter agent; website-audit report generator; savings calculator for pitches.

## 28 Aug – Brand + website in one afternoon (sampled)
Give Claude the folder/pictures, ask for a brand + page structure + component/design system; **an `.md` project file** keeps context for new sessions; check the result with a role prompt.
- **BUILD:** complete brand kit + website for a small business in one sitting.

## 29 Aug – Deployment from zero to live (sampled)
Website flow: Claude writes prompt -> Claude Code builds -> push to GitHub -> import in Vercel/Render (Render if a backend must run all the time) -> live in ~30 minutes; also "how to find the client" in the same flow.
- **BUILD:** live client demo site deployed within the class.

## 03 Sep – WhatsApp AI agent for your business (sampled)
Front end + backend already built; now the agent: business description, address, office hours (e.g. "closes 9pm Wednesday"), products/FAQ files, then connect to WhatsApp through **Meta** (next two days).
- **BUILD:** WhatsApp Business agent connected through Meta Cloud API.

## 03 Sep – Voice agent in 15 min (sampled)
**ElevenLabs** agent (choose an industry: finance/banking, real estate, food, manufacturing, tech); job-interview question: "what is the grounding effect when building an AI agent?" = boundaries so it refuses risky answers (very important in US/UK/Canada/Australia because of laws); qualification + booking + 24/7 support.
- **BUILD:** voice receptionist/booking agent per industry.

---
# WHAT COULD NOT BE READ
- **No captions on YouTube (need Whisper, slow):** 15 Jul, 27 Jul, 3 Aug, 5 Aug, 13 Aug, 19 Aug (Day 2 frontend), 21 Aug (Claude Code live), 22 Aug (test agents), 26 Aug (Golden Rule), 6 Sep, 7 Sep (Vercel).
- **Removed by YouTube:** 4 Sep (jVJwoOBkGms).
- Every other video was only sampled (about 6-14 excerpts each), not read minute by minute.
