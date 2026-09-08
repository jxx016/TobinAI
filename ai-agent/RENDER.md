# Deploy Tobin AI agent on Render

1. https://dashboard.render.com → **New** → **Web Service**
2. Connect GitHub repo `jxx016/TobinAI` (grant access if prompted)
3. Settings:
   - Branch: `feat/vendor-research`
   - Root Directory: `ai-agent`
   - Runtime: **Docker**
   - Instance type: **Free**
4. Environment → add every key from local `ai-agent/.env`, plus:
   - `AUTO_OUTREACH=false`
   - `APPROVE_SECRET` = a long random string
5. Create Web Service → wait for deploy
6. Open `https://<your-service>.onrender.com/health` — expect `{"status":"ok","service":"tobin-ai"}`
7. Tell Grok Bot the URL so we can point `VITE_API_URL` at it

Notes:
- Free tier **spins down** when idle (~cold start). Fine for pilot; Twilio reply webhooks may be slow after idle.
- Run Supabase SQL `migrations/002_outreach_sent_at.sql` if you have not yet.
