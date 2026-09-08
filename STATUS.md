# TobinAI — shared status board

**Rule for every agent (Cursor, Claude, Codex, Grok Bot, cloud agents):**
1. **Read this file first** before starting TobinAI work.
2. **Claim** a task under Active before you edit code (add your name + timestamp).
3. **Update** when you finish, block, or hand off — same session, don’t leave stale claims.
4. Keep entries short. Details go in PRs/commits; this file is the shared brain.

Stable product context lives in `AGENTS.md`. This file is the **live** coordination surface.

---

## Now (one paragraph)
Supervised single-landlord pilot path. LangGraph agent on `feat/vendor-research` is the product. **P0:** human approve gate before cold Places vendor SMS. Repo still **local-only** (no git remote). Hosting + `VITE_API_URL` still needed for a real pilot.

## Active
| Agent | Task | Started (local) | Notes |
|-------|------|-----------------|-------|
| — | — | — | nothing claimed |

## Blocked
| Item | Waiting on | Since |
|------|------------|-------|
| Cursor cloud agent on this repo | GitHub remote | 2026-09-08 |
| Public pilot URL | Host FastAPI `ai-agent` + set `VITE_API_URL` | 2026-09-08 |

## Done (newest first)
| When | Agent | What |
|------|-------|------|
| 2026-09-08 | Grok Bot | Launch-readiness review; created `AGENTS.md` |
| 2026-09-09 | Grok Bot | Created this `STATUS.md` shared board |

## Next up (priority order)
1. **Vendor approve gate** — pause before `outreach_vendors` / cold SMS; approve endpoint or landlord email link (`AUTO_OUTREACH=false` default)
2. **Push to GitHub** — add remote, push `feat/vendor-research`
3. **Host `ai-agent`** — Dockerfile → public HTTPS
4. **Point frontend** — production `VITE_API_URL`
5. **Supervised live ticket** — DB vendor only, John watching Twilio
6. Later: archive Express/`n8n` leftovers; refresh README

## Handoff notes (freeform, newest at top)
- 2026-09-09 Grok Bot: John switches Cursor ↔ Claude ↔ Codex for code; Grok Bot owns product/pilot and keeps these files current. Coding agents should append here when they stop mid-task.
