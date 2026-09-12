# TobinAI — shared status board

**Rule for every agent (Cursor, Claude, Codex, Grok Bot, cloud agents):**
1. **Read this file first** before starting TobinAI work.
2. **Claim** a task under Active before you edit code (add your name + timestamp).
3. **Update** when you finish, block, or hand off — same session, don’t leave stale claims.
4. Keep entries short. Details go in PRs/commits; this file is the shared brain.

Stable product context lives in `AGENTS.md`. This file is the **live** coordination surface.

---

## Now (one paragraph)
Supervised single-landlord pilot. LangGraph on `feat/vendor-research`. **GitHub:** https://github.com/jxx016/TobinAI (private). Places cold SMS is gated (`AUTO_OUTREACH=false` + approve webhook). **Host on Render** (see `ai-agent/RENDER.md`) + set `VITE_API_URL`.

## Active
| Agent | Task | Started (local) | Notes |
|-------|------|-----------------|-------|
| — | — | — | — |

## Blocked
| Item | Waiting on | Since |
|------|------------|-------|
| JOH-5 live SPA routes | John: merge PR #1 + redeploy Netlify `dist/public` with `_redirects` | 2026-09-12 |
| Cursor cloud agent | Connect GitHub account `jxx016` to Cursor (or grant Cursor access to TobinAI) | 2026-09-09 |
| Public pilot URL | Deploy `ai-agent` on Render + set `VITE_API_URL` | 2026-09-09 |

## Done (newest first)
| When | Agent | What |
|------|-------|------|
| 2026-09-12 | Cursor cloud | JOH-5: Netlify SPA `_redirects` source checked in; PR https://github.com/jxx016/TobinAI/pull/1 → `feat/vendor-research` (redeploy still needed for live) |
| 2026-09-09 | Cursor (Grok) | Vendor approve gate: `AUTO_OUTREACH=false` default, landlord email, `POST /webhook/approve-outreach` + `X-Tobin-Approve-Key`; DB vendors still notify; Places SMS only after approve |
| 2026-09-09 | Grok Bot | Pushed private repo https://github.com/jxx016/TobinAI (`main` + `feat/vendor-research`) |
| 2026-09-09 | Grok Bot | Created this `STATUS.md` shared board |
| 2026-09-08 | Grok Bot | Launch-readiness review; created `AGENTS.md` |

## Next up (priority order)
1. **Host `ai-agent`** — Dockerfile → public HTTPS
2. **Point frontend** — production `VITE_API_URL`
3. **Set `APPROVE_SECRET`** in `ai-agent/.env` (and run `migrations/002_outreach_sent_at.sql` in Supabase if needed)
4. **Supervised live ticket** — DB vendor only, John watching Twilio
5. Later: archive Express/`n8n` leftovers; refresh README

## Handoff notes (freeform, newest at top)
- 2026-09-12 Cursor cloud: JOH-5 PR #1 open. Landing was a broken gitlink; now tracked `_redirects` under `landing_page/TobinPropertyAssistant/{public,client/public}/`. Live still 404 until John redeploys Netlify. Do not start JOH-6 until this PR is open (it is).
- 2026-09-09 Grok Bot: Switched agent hosting plan to **Render** (Railway needs paid). Added `render.yaml` + `ai-agent/RENDER.md`. Deploy via dashboard; free tier cold-starts.
- 2026-09-09 Grok Bot: Chose Railway for hosting. Dockerfile PORT-aware + railway.toml added under ai-agent/. Awaiting `railway login` on Mac.
- 2026-09-09 Cursor: Places path saves `vendor_outreach` with `sent_at=NULL`, status `awaiting_vendor_approval`, emails `LANDLORD_EMAIL`. Approve: `POST /webhook/approve-outreach` JSON `{"request_id":"TM-..."}` header `X-Tobin-Approve-Key`. Repeat calls do not re-SMS. Set `APPROVE_SECRET` before using the webhook (empty secret → 401).
- 2026-09-09 Grok Bot: GitHub remote live. Cloud agent launch failed — Cursor’s connected GitHub can’t access `jxx016/TobinAI`. Use local Cursor/Claude/Codex with paste prompt, or connect `jxx016` to Cursor.
- 2026-09-09 Grok Bot: John switches Cursor ↔ Claude ↔ Codex for code; Grok Bot owns product/pilot.
