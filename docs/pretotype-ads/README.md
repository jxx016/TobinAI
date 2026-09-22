# TobinAI pretotype Meta ads

Static creatives + copy for an Austin landlord pilot Meta test. **Docs/assets only** — no Meta API spend from this repo.

**Offer:** 2 weeks free → $99/mo  
**Form:** https://cool-cannoli-68cac9.netlify.app/submit-request  
**Spend gate:** do **not** run ads until notify PR #5 is merged and Render is retested. See `COPY.md`.

---

## Files

| File | Size | Use |
|------|------|-----|
| `concept-a-night-dispatcher-1080.png` | 1080×1080 | Feed / square |
| `concept-a-night-dispatcher-1080x1920.png` | 1080×1920 | Stories / Reels |
| `concept-b-three-steps-1080.png` | 1080×1080 | Feed / square |
| `concept-b-three-steps-1080x1920.png` | 1080×1920 | Stories / Reels |
| `concept-c-price-1080.png` | 1080×1080 | Feed / square |
| `concept-c-price-1080x1920.png` | 1080×1920 | Stories / Reels |
| `COPY.md` | — | Primary text, headlines, UTMs, kill criteria |
| `README.md` | — | This file |

---

## How John downloads from the PR

1. Open the pull request that adds `docs/pretotype-ads/`.
2. Go to the **Files changed** tab (or browse the branch on GitHub).
3. Open each `.png` → click **Download** / **View raw** → Save As.
4. Or clone/checkout the PR branch and copy the folder:
   ```bash
   git fetch origin
   git checkout <pr-branch>
   open docs/pretotype-ads   # or Finder / Explorer
   ```
5. Keep filenames as-is so UTMs in `COPY.md` stay matched (`concept_a` / `concept_b` / `concept_c`).

---

## What to upload in Meta Ads Manager

1. **Campaign:** Traffic or Leads (prefer Leads if Pixel Lead is live). Name: `Austin Pilot Sep26`.
2. **Budget:** campaign spend limit **$100**. Do not start until spend gate clears.
3. **Ad set:** Austin metro (or 25-mi radius). Age 25–64. Interests optional (real estate investing / landlord) — keep broad if volume dies.
4. **Ads:** one ad per concept (A/B/C). For each:
   - Upload **1080×1080** for Feed placements.
   - Upload matching **1080×1920** for Stories / Reels (or let Meta crop only if you skip Stories).
   - Paste primary text + headline + description from `COPY.md`.
   - CTA button: Learn more (A) or Sign up (B/C).
   - Destination URL: the concept’s UTM URL from `COPY.md` (must include `utm_content=concept_x`).
5. **Pixel:** PageView + Lead before go-live (checklist in `COPY.md`).
6. **Kill rules:** pause if ~0 submits after ~$80 or dead CTR; PASS at ≥3 qualified submits or ≥1 booked call.

---

## Design notes

- Brand wordmark: **TobinAI**
- CTAs on creative: “Start free pilot” / “Send your first ticket”
- No third-party logos; no spend automation in-repo
