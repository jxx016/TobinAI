# Put `demo-request` on cool-cannoli without replacing the SPA

The live form at `https://cool-cannoli-68cac9.netlify.app/waitlist` posts JSON to `/.netlify/functions/demo-request`. That function is not in the current Netlify deploy (the path returns Netlify’s HTML 404). This repo now has the function, but it does **not** have the SPA bundle. The landing submodule was removed; only `_redirects` is tracked.

`netlify.toml` in this folder sets `publish = "dist/public"` and `functions = "netlify/functions"`. `dist/public` is not in git. A Git-triggered production deploy of this repository publishes an empty site and takes cool-cannoli down.

Do not use “Clear cache and deploy site” on a Netlify site linked to `jxx016/TobinAI`. Do not change the production publish directory to this folder until it contains the current `index.html` and `assets/`.

## 1. Render first

Merge the demo-request PR into `feat/vendor-research`. Render’s service tracks that branch (`ai-agent/RENDER.md`).

```bash
curl -sS https://tobinai.onrender.com/health
```

Wait until the JSON includes `"demo_request": true` (free tier rebuild often takes several minutes; `/health` also wakes a sleeping instance).

```bash
curl -sS -D - -X POST https://tobinai.onrender.com/webhook/demo-request \
  -H 'content-type: application/json' \
  -H 'origin: https://cool-cannoli-68cac9.netlify.app' \
  -d '{"email":"smoke-demo-request@example.com","name":"Tobin smoke test","phone":"","property_count":"1","message":"Automated smoke test. Safe to ignore.","source":"demo-request","timestamp":"2026-10-24T00:00:00.000Z"}'
```

Expect `200` and `{"success":true,"message":"Demo request received. We'll be in touch within 24 hours!"}`. That send uses AgentMail to `LANDLORD_EMAIL`. Check the inbox once. Do not re-run it in a loop.

## 2. Deploy the function beside the current SPA

On a machine logged into the Netlify account that owns `cool-cannoli-68cac9` (`npx netlify-cli status`).

From this directory (`landing_page/TobinPropertyAssistant`) on the merged commit:

```bash
bash scripts/snapshot-live-spa.sh /tmp/cool-cannoli-publish
```

Confirm `/tmp/cool-cannoli-publish` contains `index.html`, `assets/index-*.js`, `assets/index-*.css`, and `_redirects` (`/* /index.html 200`). The script refuses to save the SPA HTML fallback as if it were a real favicon or robot file.

If you still have the original Replit output or `dist/public` that produced the live site, use that directory as `--dir` instead of the snapshot. It must contain the same `_redirects` line or `/waitlist` will 404 after the new deploy.

Draft deploy, then production:

```bash
npx netlify-cli deploy \
  --site=cool-cannoli-68cac9 \
  --dir=/tmp/cool-cannoli-publish \
  --functions="$(pwd)/netlify/functions"

# On the draft URL, POST /.netlify/functions/demo-request
# and open /waitlist. Both must work before --prod.

npx netlify-cli deploy --prod \
  --site=cool-cannoli-68cac9 \
  --dir=/tmp/cool-cannoli-publish \
  --functions="$(pwd)/netlify/functions"
```

Leave Netlify env `DEMO_REQUEST_UPSTREAM` unset. The function defaults to `https://tobinai.onrender.com/webhook/demo-request`. The file is `demo-request.mjs` so Netlify treats it as ESM; the URL is still `/.netlify/functions/demo-request`.

If the live site is built from a different repo (the Replit project), copy `netlify/functions/demo-request.mjs` into that project and redeploy **there**. Do not retarget cool-cannoli at `jxx016/TobinAI`.

## 3. Confirm the form path

```bash
curl -sS -D - -X POST \
  https://cool-cannoli-68cac9.netlify.app/.netlify/functions/demo-request \
  -H 'content-type: application/json' \
  -H 'origin: https://cool-cannoli-68cac9.netlify.app' \
  -d '{"email":"you@example.com","name":"John","phone":"","property_count":"1","message":"manual check","source":"demo-request","timestamp":"2026-10-24T00:00:00.000Z"}'
```

Expect HTTP 200 and `"success": true`. Then submit `/waitlist` once in a browser. The page shows the thank-you state and calls `fbq('track','Lead')` only when the response is OK. Do not publish Meta ads.

## If the function times out

Render’s free instance sleeps. Hit `/health` and wait for 200 before another submit. Netlify’s current synchronous function limit is 60 seconds on the docs; some sites still stop at 10 seconds until Netlify support raises it. A platform HTML 504 means the proxy was killed, not that this repo’s function is missing. The agent returns 502 when AgentMail fails, so the form stays on the error state and does not count a Lead.
