# TobinAI — agent handoff (Cursor / Claude / Codex / Grok Bot)

## Roles
- **Grok Bot (New Bot):** product, pilot plan, launch readiness, prioritizing work, keeping this file current after decisions.
- **Cursor / Claude / Codex:** implementation in this repo. Prefer the LangGraph path under `ai-agent/`; do not revive n8n or the Express `backend/` unless John asks.

## Product (one line)
Autonomous property repair coordinator: tenant maintenance request → AI triage → vendor match or Places research → SMS/email outreach → vendor YES/NO → landlord notify.

## Current state (2026-09-08)
- Path: `~/Personal_projet/TobinAI` (folder spelling `Personal_projet`)
- Branch: `feat/vendor-research` (ahead of `main`; n8n → FastAPI + LangGraph already done)
- **No git remote** — local-only until John pushes to GitHub
- Stack that matters: `ai-agent/` (FastAPI + LangGraph + Gemini), `frontend/` (Vite form + status), `landing_page/TobinPropertyAssistant/` (Netlify), Supabase Postgres, Twilio, AgentMail, Google Places
- Env keys live in `ai-agent/.env` (gitignored). See `ai-agent/.env.example`
- Verdict: **demo-strong / supervised single-landlord pilot almost**; not multi-tenant SaaS

## Do / don’t
- **Do** add a human approval gate before any cold vendor SMS (Places outreach)
- **Do** keep DB-listed preferred vendors workable for known landlords
- **Don’t** blast Google Places vendors in production without consent/approve
- **Don’t** expand multi-tenant auth until one paid pilot works
- **Don’t** rewrite README to n8n — that path is legacy

## Ranked next tasks
1. **Vendor approve gate (P0)** — after `research_vendors`, pause before `outreach_vendors` / `notify_vendor` until John (or landlord) approves the candidate list. Options: env `AUTO_OUTREACH=false` + `POST /webhook/approve-outreach`, or email John a link with approve tokens.
2. **Host the agent** — deploy `ai-agent` Dockerfile somewhere public; set frontend `VITE_API_URL`
3. **Git remote** — create GitHub repo, push `feat/vendor-research`, open PR to `main`
4. **One supervised live ticket** — known vendor in DB only; John watching Twilio
5. **Cleanup later** — archive/ignore Express `backend/`, n8n docs; refresh root README

## Key files
- `ai-agent/graph.py` — LangGraph wiring + route after analysis
- `ai-agent/nodes.py` — save, analyze, notify, research, outreach, update
- `ai-agent/vendor_research.py` — Places search + outreach table helpers
- `ai-agent/main.py` — webhooks: maintenance-request, vendor-reply, health
- `frontend/src/MaintenanceRequestForm.jsx` — posts to `{VITE_API_URL}/webhook/maintenance-request`

## Shared coordination
- **`STATUS.md`** — living board. **Read first, write when you claim/finish/block.** All agents update it.
- **`AGENTS.md`** — this file: roles, product, do/don’t, ranked backlog (slower-changing).

## How to collaborate
When you finish a chunk, update `STATUS.md` (Done + Next + Handoff notes). Grok Bot reads it and adjusts the pilot plan. If you only use chat, paste a 3-line status and Grok Bot will write it into `STATUS.md` for everyone else.
