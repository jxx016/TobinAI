# Pretotype Meta video — Concept D

One short captioned ad for the Austin landlord pilot. Docs and mp4 only. No Meta spend from this repo.

**Vertical (use this):** `concept-d-video-1080x1920.mp4` — 1080×1920, ~24.5s  
**Square (optional):** `concept-d-video-1080.mp4` — 1080×1080, same story  
**Copy + UTM:** `COPY.md` (`utm_content=concept_d_video`)

**Gate:** do not spend until notify PR #5 is merged and Render is retested. See `COPY.md`.

Captions are burned in. There is no voiceover. A silent audio track is included so Ads Manager accepts the file.

---

## Download the mp4

1. Open this pull request on GitHub.
2. Open `docs/pretotype-ads/concept-d-video-1080x1920.mp4` (and the square file if you want feed).
3. Click **Download** (GitHub’s file view). Save the `.mp4` as-is. Do not re-export or crop it.
4. Or from a clone:

```bash
git fetch origin
git checkout cursor/concept-d-video-ad-f1d7
# files:
# docs/pretotype-ads/concept-d-video-1080x1920.mp4
# docs/pretotype-ads/concept-d-video-1080.mp4
```

---

## Upload in Meta Ads Manager

Do this as a **draft**. Leave the ad off until the spend gate in `COPY.md` is clear.

1. Campaign name: `Austin Pilot Sep26`. Objective: Traffic, or Leads if the Pixel Lead event is already live.
2. Ad set: Austin (metro or ~25 miles). Keep it one ad set for this video.
3. Create one ad. Name: `Concept D / Video`.
4. **Media:** upload `concept-d-video-1080x1920.mp4` and assign it to Stories and Reels (vertical).
5. **Optional feed:** upload `concept-d-video-1080.mp4` for the square Feed placement so Meta does not crop the vertical file. If you skip the square, run Stories/Reels only.
6. **Primary text, headline, description:** paste from `COPY.md`.
7. **CTA button:** Learn more.
8. **Destination URL** (must include the video UTM):

   `https://cool-cannoli-68cac9.netlify.app/submit-request?utm_source=meta&utm_medium=paid&utm_campaign=austin_pilot_sep26&utm_content=concept_d_video`

9. Captions are already on the picture. You do not need a separate SRT.
10. Preview Stories and Reels. Confirm the hook, the two vendor cards, and **Start free pilot** are readable, then save as draft.

Do not add a budget you are willing to spend, and do not hit Publish, until PR #5 is merged and the Render retest passes.
