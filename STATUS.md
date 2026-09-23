# TobinAI — shared status board

**Rule for every agent (Cursor, Claude, Codex, Grok Bot, cloud agents):**
1. **Read this file first** before starting TobinAI work.
2. **Claim** a task under Active before you edit code (add your name + timestamp).
3. **Update** when you finish, block, or hand off — same session, don’t leave stale claims.
4. Keep entries short. Details go in PRs/commits; this file is the shared brain.

Stable product context lives in `AGENTS.md`. This file is the **live** coordination surface.

---

## Now (one paragraph)
Supervised single-landlord pilot. LangGraph on `feat/vendor-research`. **API live:** https://tobinai.onrender.com (`/health` 200). Built Netlify JS already posts to Render (not localhost). **Sell form still blocked:** `/submit-request` and `/check-status` 404 until John redeploys Netlify with `_redirects` (source merged in PR #1). Places gate code is deployed; JOH-7 smoke took the **DB vendor path**, not Places. JOH-8 offer one-pager is in `docs/pilot-offer.md` (2 weeks free → $99/mo).

## Active
| Agent | Task | Started (local) | Notes |
|-------|------|-----------------|-------|
| — | — | — | — |

## Blocked
| Item | Waiting on | Since |
|------|------------|-------|
| JOH-5 live SPA routes | John: **PR #1 already merged** — redeploy Netlify `dist/public` with `_redirects` (live still 404) | 2026-09-12 |
| JOH-6 `sent_at` default | John: run `ai-agent/migrations/002_outreach_sent_at.sql` in Supabase (not verified) | 2026-09-12 |
| Places-path smoke | Sample vendors cover all specialties, so live tickets match DB vendors and skip Places / landlord-approve email | 2026-09-12 |

## Done (newest first)
| When | Agent | What |
|------|-------|------|
| 2026-09-21 | Cursor cloud | Week Rock notify honesty: graph `notifications[]`, honest `ai_reasoning`, webhook JSON, form warning on failed SMS/email, `/health` env-presence flags. PR https://github.com/jxx016/TobinAI/pull/5 → `feat/vendor-research`. pytest 26/26 (mocked; no real SMS). Live Render SMS retest still John’s. |
| 2026-09-12 | Cursor cloud | JOH-7 readiness: pytest 15/15; live smoke `TM-20260912-0006` (DB vendor "City Plumbing Co"); Netlify deep links still 404; no PR for product code — findings in Linear JOH-7 |
| 2026-09-12 | Cursor cloud | JOH-8: `docs/pilot-offer.md` — 2-week free then $99/mo supervised 1-landlord offer |
| 2026-09-12 | Cursor cloud | JOH-5: Netlify SPA `_redirects` source checked in; PR https://github.com/jxx016/TobinAI/pull/1 → `feat/vendor-research` (redeploy still needed for live) |
| 2026-09-09 | Cursor (Grok) | Vendor approve gate: `AUTO_OUTREACH=false` default, landlord email, `POST /webhook/approve-outreach` + `X-Tobin-Approve-Key`; DB vendors still notify; Places SMS only after approve |
| 2026-09-09 | Grok Bot | Pushed private repo https://github.com/jxx016/TobinAI (`main` + `feat/vendor-research`) |
| 2026-09-09 | Grok Bot | Created this `STATUS.md` shared board |
| 2026-09-08 | Grok Bot | Launch-readiness review; created `AGENTS.md` |

## Next up (priority order)
1. **Redeploy Netlify** with `_redirects` (JOH-5 live) — sell form still 404
2. **Send `docs/pilot-offer.md`** — first landlord ask (2 weeks free → $99/mo)
3. **Confirm JOH-6** applied in Supabase (`sent_at` DROP DEFAULT)
4. **Supervised live ticket** — real tenant phone; confirm JSON `notifications` + actual SMS (HTTP 200 is not delivery). DB vendor only; John watching Twilio
5. **Places-path proof** — only after sample/preferred vendors would *not* match (or temporarily deactivate them); do not approve-outreach without John + `APPROVE_SECRET`
6. Later: archive Express/`n8n` leftovers; refresh README

## Handoff notes (freeform, newest at top)
- 2026-09-21 Cursor cloud (Week Rock): **UI success ≠ delivery is fixed in API + form.** Failures record `{channel,to,ok:false,error}` and `❌` reasoning; success still claims sent. Twilio/AgentMail now lazy-init so missing Render env is a notify error, not a boot crash. John: verify Render env (`TWILIO_*`, `AGENTMAIL_*`, `LANDLORD_EMAIL`), hit `/health` after 30–60s cold start, submit with a **real** tenant phone, check `notifications` + actual SMS. Approve-gate / AUTO_OUTREACH unchanged.
- 2026-09-12 Cursor cloud (JOH-7): **No-Go for sell demo** until Netlify SPA routes are live. **Conditional Go for API-only supervised pilot** (Render + DB vendors). Smoke POST `TM-20260912-0006` succeeded; check-status found it (`status=pending`). Reasoning claimed tenant+vendor SMS; phones were `+15555550100` (tenant) and schema sample `+15552345678` (City Plumbing Co) — Twilio almost certainly rejected both. Places / landlord-approve email **not** exercised because Gemini matched a DB vendor. Approve webhook without key → 401 (did not call with secret). Repo landing app source is now only `_redirects` files after PR #1 (submodule removed) — rebuild from this tree will not recreate the live SPA. Full write-up in Linear JOH-7.
- 2026-09-12 Cursor cloud: JOH-8 offer one-pager in `docs/pilot-offer.md`. Default: free 2 weeks then $99/mo, one landlord / 5 properties. Places still gated. John can send the last section (“How to say it”) as-is.
- 2026-09-12 Cursor cloud: JOH-5 PR #1 open. Landing was a broken gitlink; now tracked `_redirects` under `landing_page/TobinPropertyAssistant/{public,client/public}/`. Live still 404 until John redeploys Netlify. Do not start JOH-6 until this PR is open (it is).
- 2026-09-09 Grok Bot: Switched agent hosting plan to **Render** (Railway needs paid). Added `render.yaml` + `ai-agent/RENDER.md`. Deploy via dashboard; free tier cold-starts.
- 2026-09-09 Grok Bot: Chose Railway for hosting. Dockerfile PORT-aware + railway.toml added under ai-agent/. Awaiting `railway login` on Mac.
- 2026-09-09 Cursor: Places path saves `vendor_outreach` with `sent_at=NULL`, status `awaiting_vendor_approval`, emails `LANDLORD_EMAIL`. Approve: `POST /webhook/approve-outreach` JSON `{"request_id":"TM-..."}` header `X-Tobin-Approve-Key`. Repeat calls do not re-SMS. Set `APPROVE_SECRET` before using the webhook (empty secret → 401).
- 2026-09-09 Grok Bot: GitHub remote live. Cloud agent launch failed — Cursor’s connected GitHub can’t access `jxx016/TobinAI`. Use local Cursor/Claude/Codex with paste prompt, or connect `jxx016` to Cursor.
- 2026-09-09 Grok Bot: John switches Cursor ↔ Claude ↔ Codex for code; Grok Bot owns product/pilot.
