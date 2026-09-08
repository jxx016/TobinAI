# TobinAI — shared status board

**Rule for every agent (Cursor, Claude, Codex, Grok Bot, cloud agents):**
1. **Read this file first** before starting TobinAI work.
2. **Claim** a task under Active before you edit code (add your name + timestamp).
3. **Update** when you finish, block, or hand off — same session, don’t leave stale claims.
4. Keep entries short. Details go in PRs/commits; this file is the shared brain.

Stable product context lives in `AGENTS.md`. This file is the **live** coordination surface.

---

## Now (one paragraph)
Supervised single-landlord pilot. LangGraph on `feat/vendor-research`. **GitHub:** https://github.com/jxx016/TobinAI (private). **P0:** human approve gate before cold Places vendor SMS. Hosting + `VITE_API_URL` still needed for a real pilot.

## Active
| Agent | Task | Started (local) | Notes |
|-------|------|-----------------|-------|
| — | Vendor approve gate (unclaimed) | — | Cloud agent blocked: Cursor GitHub account can’t see `jxx016/TobinAI` yet |

## Blocked
| Item | Waiting on | Since |
|------|------------|-------|
| Cursor cloud agent | Connect GitHub account `jxx016` to Cursor (or grant Cursor access to TobinAI) | 2026-09-09 |
| Public pilot URL | Host FastAPI `ai-agent` + set `VITE_API_URL` | 2026-09-08 |

## Done (newest first)
| When | Agent | What |
|------|-------|------|
| 2026-09-09 | Grok Bot | Pushed private repo https://github.com/jxx016/TobinAI (`main` + `feat/vendor-research`) |
| 2026-09-09 | Grok Bot | Created this `STATUS.md` shared board |
| 2026-09-08 | Grok Bot | Launch-readiness review; created `AGENTS.md` |

## Next up (priority order)
1. **Vendor approve gate** — pause before `outreach_vendors` / cold SMS; `AUTO_OUTREACH=false` + approve webhook
2. **Host `ai-agent`** — Dockerfile → public HTTPS
3. **Point frontend** — production `VITE_API_URL`
4. **Supervised live ticket** — DB vendor only, John watching Twilio
5. Later: archive Express/`n8n` leftovers; refresh README

## Handoff notes (freeform, newest at top)
- 2026-09-09 Grok Bot: GitHub remote live. Cloud agent launch failed — Cursor’s connected GitHub can’t access `jxx016/TobinAI`. Use local Cursor/Claude/Codex with paste prompt, or connect `jxx016` to Cursor.
- 2026-09-09 Grok Bot: John switches Cursor ↔ Claude ↔ Codex for code; Grok Bot owns product/pilot.
