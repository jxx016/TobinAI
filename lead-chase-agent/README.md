# Lead chase agent

Autonomous follow-up for property operators evaluating Tobin. A maintenance lead enters, the graph enriches a profile, classifies the reply, drafts one short note, grades it with a fixed rubric, and either sends it or stops for a human. Opt-outs halt immediately. Discounts are never invented.

The default process is local. `MOCK_EXTERNAL_SERVICES=true` and no model key means no network calls.

## Run locally

```bash
cd lead-chase-agent
uv sync
uv run uvicorn src.api.main:app --host 127.0.0.1 --port 8080
```

If `uv` is not installed, create a virtualenv, `pip install -e ".[dev]"` from this directory (pytest is in the `dev` dependency group), and run `python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8080`.

Health check: `GET /health`.

Create a lead:

```bash
curl -s -X POST http://127.0.0.1:8080/webhooks/lead \
  -H 'content-type: application/json' \
  -d '{"lead_id":"demo-1","name":"Alex Rivera","email":"alex@northwind.example","company":"Northwind","role":"Ops Lead","industry":"property-management","source":"demo-form"}'
```

Other routes:

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/webhooks/lead` | Start a thread. `thread_id` is the lead id. |
| POST | `/webhooks/reply` | Inbound email or SMS body. |
| POST | `/hitl/approve` | `{"lead_id","action":"approve"\|"edit"\|"reject","edited_draft"}` |
| POST | `/reflection/run` | Scan ghosting and unsubscribes, write a playbook diff. |
| GET | `/health` | Process flags. |

While the API is up, APScheduler polls due follow-ups and runs nightly reflection. Set `SCHEDULER_ENABLED=false` to turn that off.

## Tests and the eval harness

```bash
cd lead-chase-agent
uv sync
uv run pytest
uv run python -m src.reflection.eval_harness
```

Pytest and the harness use the in-memory checkpointer, SQLite (`sqlite:///:memory:` in tests), and the deterministic mock model. They do not call OpenAI, Anthropic, Tavily, Resend, Twilio, or Cal.com.

The harness covers five scenarios: busy-founder ghosting, a price objection, an angry opt-out, a ready-to-book reply, and a prompt-injection attempt.

## Swap mocks for live services

Copy `.env.example` to `.env`.

| Goal | Change |
| --- | --- |
| Draft with a real model | Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. The rubric, opt-out rule, and injection rule stay in code. |
| Enrich from the web | `MOCK_EXTERNAL_SERVICES=false` and `TAVILY_API_KEY` or `FIRECRAWL_API_KEY`. |
| Send mail | `MOCK_EXTERNAL_SERVICES=false` and `RESEND_API_KEY` plus `RESEND_FROM_EMAIL`. |
| Send SMS or WhatsApp | `MOCK_EXTERNAL_SERVICES=false` and the Twilio variables. |
| Real booking slots | `MOCK_EXTERNAL_SERVICES=false`, `CALCOM_API_KEY`, and `CALCOM_EVENT_TYPE_ID` or `CALCOM_USERNAME`. |
| Durable threads and shared tactics | `CHECKPOINT_DATABASE_URL=postgresql://...` (or a Postgres `DATABASE_URL`). Install with `uv sync --extra postgres`. The app falls back to memory if Postgres cannot be reached. |
| Traces | `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY`. Tracing is optional. |
| App database on Postgres | `DATABASE_URL=postgresql+psycopg://...` and `uv sync --extra postgres`. |

Live chat models need `uv sync --extra llm`.

## How a thread moves

1. `ingest_and_enrich` updates the CRM. A `NEW` lead gets a web-enrichment note and any saved tactics for that industry or persona (`("tactics", industry_or_persona)`).
2. `classify_intent` maps the latest inbound message, or a scheduled no-reply, onto a stage. Unsubscribe stops the thread. Anger, a pricing exception, or an enterprise/VIP note sets `requires_human_approval`.
3. Routing: terminal stages log and end; `READY_TO_BOOK` writes a booking link; `OBJECTION` pulls battlecards; everything else drafts the next angle (`direct_value` → `social_proof` → `micro_question` → `breakup_note`).
4. `rubric_critic` requires under 80 words, no filler, one concrete detail, exactly one CTA, and no invented price or discount. A failure goes back to the drafter while `critic_retries < 2`. After that the draft waits for a human.
5. `hitl_gate` calls `interrupt()` when approval is required. Resume with `POST /hitl/approve`.
6. `dispatch_and_schedule` sends through the email or SMS adapter, logs the touch, and sets the next follow-up at +24h, +72h, then +120h. The fourth unanswered touch is marked `GHOSTING` and is not rescheduled.

A booked handoff, or an objection that gets a real reply out, stores a short heuristic for the next similar lead.

## Layout

`src/agent` holds state, prompts, the rubric, the model adapter, and the graph. `src/tools` holds enrichment, the playbook search, CRM, messaging, and calendar. `src/reflection` holds tactic memory, the nightly diff, and the eval harness. `data/playbook.md` is the tone guide, the rate card, and the battlecards.

## Mock limitations

- Enrichment text is synthetic. It does not read the public web.
- Email and SMS are written to the CRM and stdout. Nothing is delivered.
- Booking links look like `https://cal.example.com/book/<lead_id>`. No meeting is created.
- The default checkpointer and tactic store are in-process. A restart forgets threads unless Postgres is configured. Due jobs can still rebuild a chase from the CRM row, without the prior message list.
- The critic is a deterministic rubric, not a second LLM. A live model writes drafts only when a key is set, and the rubric can still reject them.
- The eval harness always uses the mock model so it stays a safety check.
- Postgres checkpointer, pgvector-style store search, Resend, Twilio, Cal.com, Tavily, and Firecrawl are implemented as adapters and are not exercised by the test suite.
