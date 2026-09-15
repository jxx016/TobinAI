# Tobin Acquire — brainstorm / design (docs only)

**Working name:** Tobin Acquire (also “Tobin side app”)  
**Status:** exploration. **Do not build** until John makes the decisions in §J.  
**Date:** 2026-09-15  
**Repo context:** adjacent to [TobinAI](https://github.com/jxx016/TobinAI) on `feat/vendor-research`. Core product is a **supervised property maintenance coordinator**, live at [cool-cannoli-68cac9.netlify.app](https://cool-cannoli-68cac9.netlify.app/) and [tobinai.onrender.com](https://tobinai.onrender.com). Pilot offer: 2 weeks free → $99/mo (`docs/pilot-offer.md`).  
**This document is not a license to scrape MLS, auto-dial, or ship undisclosed AI voice.**

---

## Verdict (read this first)

| Path | Verdict | Why |
|------|---------|-----|
| **United interview showcase** (inbound + consented volunteer; mocked or licensed data; disclosed AI; human handoff) | **Go** | High signal, low legal surface, reuses Tobin’s existing “policy-gated agent” story. |
| **Supervised acquire desk** (licensed data, John/landlord approve before every outbound, TCPA/DNC/litigator gates, disclosed AI, SMS-first, one metro, tiny volume) | **Conditional Go** | Legal *enough to try* only if §J decisions are made and counsel signs off. Not a growth product. |
| **Automated find → skip-trace → cold AI voice/SMS at scale** (Zillow/MLS scrape, undisclosed “human-like” voice, no approve gate) | **No-Go** | TCPA class-action math ($500–$1,500/call, no cap), ToS/copyright on listing sites, brand risk to core Tobin, interview liability. |

**Recommended stance:** treat Acquire as a **supervised desk** that *prepares* a file (property, motivation score, comps, draft offer, skip-trace, compliance flags) and waits for a human to press send. Conversation quality is the product. Volume is not.

Core Tobin already has the right muscle: `AUTO_OUTREACH=false`, landlord email, `POST /webhook/approve-outreach`. Acquire should copy that discipline, not the maintenance graph.

---

## A. Problem / ICP / positioning vs core Tobin (landlord ops)

### The idea being explored (not built)

An agent that:

1. Finds potential motivated sellers.
2. Calculates an offer from value + comps.
3. Obtains a phone number and texts/calls.
4. Converses fluently / human-like on questions.

Steps 1–3 are **data + compliance + human judgment**. Step 4 is **conversational + voice agent design**. Mixing them without a gate is how this idea becomes a lawsuit instead of a product (or an interview).

### Problem (honest version)

Off-market residential deal flow is expensive because humans do four slow jobs: (a) find owners who might sell, (b) price a defensible offer, (c) get a reachable number, (d) have a first conversation that does not kill the relationship. Wholesalers and small landlords already buy lists, skip-trace, and blast SMS. Most of that volume is noisy, often non-compliant, and produces “we called your grandma about her house” stories. The *useful* product is a **thin, supervised first-touch** that a buyer can audit, not a robodialer.

### ICP (narrow for any Conditional Go)

| Rank | Who | Why they might pay | Why they are dangerous as v1 |
|------|-----|--------------------|------------------------------|
| **1 (preferred)** | **John + 1–2 known landlords** already in the Tobin ops orbit, acquiring 0–5 extra doors/year in a metro they know | Adjacent to core: same brand, same “I don’t want to be on the phone at 11pm,” same approve-gate habit | Still TCPA if you cold-call owners. Keep volume tiny. |
| 2 | Licensed investor / broker who already has **inbound** leads (FSBO form, “we buy houses” PPC with PEWC) | Consent exists; voice agent is a qualifier, not a hunter | Need written consent language that names the entity **and** AI voice. |
| 3 | High-volume wholesaler who wants “set it and forget it” | They will pay for volume | **Do not build for them.** Their default is illegal-adjacent ops. |

**Non-ICP for v1:** national “we buy houses” shop; anyone asking to scrape Zillow; anyone who wants the agent to *sound human so people don’t hang up*. That last one is an interview anti-pattern as well as a legal one.

### Dual purpose (product exploration + United interview)

| Purpose | What “good” looks like | What to show / not show |
|---------|------------------------|-------------------------|
| **Tobin product** | Landlords who already use the repair coordinator can later ask Tobin to **watch a ZIP for off-market inventory** (probate, tax delinquent, long-held SFR) and **prepare** an offer packet. Outbound only after the landlord (or John) approves the list. | Share brand, Twilio *discipline*, and “human veto.” Do **not** share the production Twilio number, Render service, or landlord tenant PII. |
| **United interview** | United cares about **policy-gated conversational agents**: disclosure, tool use (fares / comps), interruption handling, escalation to a human, audit logs, and not hallucinating a price. Acquire is a *story* for that, not a consumer-harassment demo. | Demo inbound or **consented volunteer**. Lead with “we refuse to ship the illegal version.” That is the adult answer in 2026 after FCC 24-17 (AI voice = artificial/prerecorded). |

Airline parallel (use this in the interview, not in seller SMS):

| Airline ops | Acquire desk |
|-------------|--------------|
| Agent may quote a fare only from the pricing tool | Agent may quote an offer only from the comps/AVM tool + approved band |
| Policy: identify the airline, offer a human | Policy: identify Tobin/entity, disclose AI, offer John |
| DNC / quiet hours analog: do not call overnight | TCPA hours + DNC + state mini-TCPAs |
| Transfer to a specialist when the request is out of policy | Warm transfer on “talk to a person,” legal questions, hostility |

### Positioning vs core Tobin (do not merge the products)

| | **Core Tobin (landlord ops)** | **Tobin Acquire (side app)** |
|--|-------------------------------|------------------------------|
| User | Tenant + landlord + vendor | Buyer (John / landlord) + owner of record |
| Trigger | Tenant maintenance form | Lead file (public record / inbound / licensed list) |
| Relationship | Existing tenant or preferred vendor | Often **no prior relationship** |
| Consent | Tenant gave the number on the form; DB vendors were listed by the landlord | **Usually none** until inbound or written consent |
| Failure mode | Missed repair, angry tenant | TCPA class action, ToS C&D, brand poison |
| Money | $99/mo ops (pilot) | Unclear; do not price until desk works on 10 supervised files |
| Runtime | `ai-agent/` on Render | **Separate service + schema.** Do not put acquire nodes on the maintenance graph. |

**Brand rule:** Acquire may be “from the people who built Tobin,” but it is not a feature flag on the repair coordinator. Mixing seller-outreach SMS onto the same 10DLC number that texts tenants and vendors is a **No-Go**.

**Positioning line (product):**  
*Tobin Acquire is a supervised buying desk: it researches a property, drafts a conservative offer, and waits for you to approve contact. It does not hunt owners in the dark.*

**Positioning line (interview):**  
*Same architecture as a customer-care voice agent: tools, policy, disclosure, human handoff. The domain is housing instead of itineraries.*

---

## B. End-to-end flow + system architecture

### Happy path (supervised desk)

```
[1] Lead ingest (licensed API / county CSV / inbound form)
        ↓
[2] Normalize address (USPS / Google Address Validation) + owner of record
        ↓
[3] Motivation score (rules, not LLM vibes): tenure, tax delq, probate, vacancy, absentee
        ↓
[4] Value + comps (AVM + sold comps + repair heuristic) → draft offer band
        ↓
[5] Skip-trace → phones/emails  [still no contact]
        ↓
[6] Compliance scrub: Federal DNC, state DNC, litigator, deceased, line-type,
    quiet hours TZ, reassigned-number, internal suppression
        ↓
[7] Desk card: "ready to contact?"  ← HUMAN APPROVE (hard gate)
        ↓
[8] Channel policy: SMS first (disclosed) → if owner replies and consents to a call → voice
        ↓
[9] Conversation (SMS or voice): disclose, qualify, answer from tools, never invent price
        ↓
[10] Outcomes: not interested / later / send letter / warm transfer to John / STOP
        ↓
[11] Write-back: transcript, offer quoted, next action, suppression list
```

**Nothing in steps 1–6 sends a message.** That is the whole product.

### Explicit non-flow (rejected)

```
scrape Zillow → guess phone from FastPeopleSearch → auto-dial 200 numbers
with an undisclosed ElevenLabs clone that "sounds like a local investor"
```

Illegal-adjacent, ToS-violating, and useless as a United story.

### System architecture (proposed, not implemented)

Keep Acquire **out of** `ai-agent/graph.py`. Mirror the pattern, new package.

```
┌─────────────────────────────────────────────────────────────────┐
│  Acquire Desk UI (internal, auth = John)                        │
│  Queue | Lead card | Approve/reject | Listen/join | Transcripts │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    POST /acquire/approve-outreach
                    (header X-Tobin-Approve-Key, same idea as Places)
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  Acquire orchestrator (LangGraph or equivalent)                 │
│  nodes: ingest → score → value → skip → scrub → wait_approve    │
│         → sms_send → voice_session → handoff → persist          │
│  AUTO_ACQUIRE_OUTREACH=false  (default, never flip in prod)     │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
   ┌───▼───┐    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
   │ Data  │    │  Skip +   │  │ Twilio    │  │ Voice     │
   │ RentCast/  │  DNC      │  │ SMS +     │  │ Vapi or   │
   │ ATTOM/     │  BatchData│  │ 10DLC     │  │ Retell or │
   │ county     │  + Twilio │  │ (new SID  │  │ ConvRelay │
   │            │  Lookup   │  │  / number)│  │ + Gemini  │
   └───────┘    └───────────┘  └───────────┘  └───────────┘
       │
   Supabase schema `acquire_*` (not maintenance_requests)
```

**Reuse from core Tobin (ideas, not tables):**

| Core Tobin | Acquire analog |
|------------|----------------|
| `AUTO_OUTREACH=false` | `AUTO_ACQUIRE_OUTREACH=false` |
| `POST /webhook/approve-outreach` + `X-Tobin-Approve-Key` | Same shape, different payload (`lead_id`, channel, script version) |
| Email landlord the Places list | Email John the lead card (comps + flags + draft SMS) |
| Gemini for triage | Gemini (or GPT) for **conversation + tool calling**, not for “is this a motivated seller” as the only score |
| Twilio SMS | **New** Twilio subaccount + 10DLC campaign (“real estate purchase inquiry”) |
| AgentMail | Optional: send a physical-letter PDF / email *after* SMS opt-in, not as the first cold channel |

**Do not reuse:** `TWILIO_PHONE_NUMBER=+12064893667`, `LANDLORD_EMAIL` as the acquire From, tenant PII, vendor_outreach rows, Render process that serves `/webhook/maintenance-request`.

### State machine (desk)

| Status | Meaning | Outbound allowed? |
|--------|---------|-------------------|
| `ingested` | Address + owner raw | No |
| `researched` | Score + AVM + comps | No |
| `enriched` | Skip-trace done | No |
| `scrubbed` | DNC/TCPA flags attached | No |
| `blocked` | Any hard fail (DNC, litigator, deceased, no PEWC for voice, scrape-sourced) | Never |
| `awaiting_approve` | Human must click | No |
| `approved_sms` | John approved **this** lead for SMS only | SMS once |
| `sms_sent` | Waiting | Only replies |
| `consented_call` | Owner replied YES to a call **or** inbound | Voice |
| `talking` | Live session | — |
| `handed_off` | John on the line / scheduled | Human |
| `closed_*` | `not_now` / `dead` / `offer_out` / `stop` | Suppression |

Approve is **per lead, per channel, per 24h**. Re-approving does not re-SMS (same idempotency as Places).

### Tool-calling contract for the conversational agent

The model may call only:

1. `get_lead_file(lead_id)` — locked facts (address, beds, year, owner name, draft offer **band**, comps IDs).
2. `get_comp(comp_id)` — one sold comp at a time.
3. `schedule_callback(window)` — writes a task; does not dial.
4. `transfer_to_human()` — Twilio/Vapi warm transfer to John’s cell.
5. `log_opt_out(reason)` — STOP / DNC immediate.

The model **may not** call skip-trace, dial, or mutate offer price. If the owner asks “what’s my house worth?”, the agent reads the **precomputed band** and says it is an estimate, not an appraisal.

### Interview vs production topology

| | Interview spike | Conditional-Go desk |
|--|-----------------|---------------------|
| Leads | 3 fixture JSON files | 10–20 licensed/public-record files in one ZIP |
| Skip-trace | Hardcoded volunteer number | BatchData (or equivalent) + scrub |
| Voice | Inbound to a demo number **or** outbound to John/friend who consented in writing | SMS-first; voice only after reply |
| Desk UI | One HTML page or Retell/Vapi dashboard | Minimal queue in a new Vite app |
| Hosting | Local / Vapi cloud | Separate Render service |

---

## C. Data sources ranked (allowed vs risky) — MLS scrape risks explicit

### Why “scrape MLS / Zillow” is the wrong primary path

The naive stack is: scrape Zillow or an IDX page → parse beds/baths/price → skip-trace the owner → dial. That is attractive because it is free and looks like “deal flow.” It is a **bad primary path** for legal, product, and interview reasons.

**1. Contract / ToS (civil, immediate)**  
Zillow, Realtor.com (Move), and Redfin Terms of Use prohibit robots, crawlers, and bypassing technical measures. Commercial use of scraped listings to build a competing or adjacent product is explicitly in the strike zone. You do not need a CFAA felony for this to be expensive: C&D, account bans, and breach-of-contract litigation are enough to kill a side app and stain a United loop.

**2. CFAA is not a free pass**  
*Van Buren* and *hiQ v. LinkedIn* narrowed “unauthorized access” for *public* pages. They do **not** bless: (a) bypassing CAPTCHA / IP blocks / login walls, (b) scraping behind an MLS or Bridge login, (c) copyright in listing photos and broker remarks, (d) violating a clickwrap you accepted. Circumventing Zillow’s 2026 anti-bot stack is the fact pattern plaintiffs *want*.

**3. The data is not “Zillow’s to give you” and not “yours to take”**  
Active listing content is licensed from MLSs and listing brokers. NAR/MLS rules (IDX, VOW, BBO) exist because that content is a paid membership product. Recirculating it into an offer engine without a data license is both a ToS problem and an MLS-participation problem. If John later wants to be a licensed agent, a scrape history is a career own-goal.

**4. Product quality is worse than people think**  
Portals lag, hide owner names, mix FSBO and agent listings, and show *asking* prices not *sold* comps. Motivated-seller signal is weak on an active MLS listing (they already have an agent). The owners you actually want—probate, tired landlord, tax delinquent, vacant—are often **not on Zillow**. Scraping the wrong population then blasting them is how you get “why is an AI calling me, my house isn’t for sale?” complaints.

**5. Interview optics**  
“I built a scraper + robodialer” is the opposite of a United-ready story in 2026. “I refused the scrape, used licensed/public records, and put a human gate in front of the model” *is* the story.

**6. Operational fragility**  
Portal HTML changes weekly. Residential proxies + CAPTCHA farms are a second product you do not want to maintain, and they look like “access after being told no.”

**Ranked alternatives (better):** public-record distress, inbound with PEWC, licensed APIs, a broker partner with RESO/Bridge, and John’s own off-market network.

### Ranked sources

| Rank | Source | Allowed? | What you get | Motivated-seller signal | Cost / access | Use in MVP? |
|------|--------|----------|--------------|-------------------------|---------------|-------------|
| **1** | **Inbound form** (“thinking of selling?”, landlord-referred, PPC with PEWC) | Yes, if consent text is correct | Phone + stated motivation | Highest | Form + ads | **Yes — best legal path** |
| **2** | **County public records** (assessor, recorder, tax delinquent lists, probate docket, code violations, sheriff sales) where the county publishes them for reuse | Yes, with county ToS + no login bypass | Owner name, mailing vs situs, tenure, distress flags | High | Sweat + occasional bulk fees | **Yes — primary research path** |
| **3** | **Licensed property APIs** (RentCast, ATTOM, BatchData, Regrid, HouseCanary) | Yes, under contract | Parcel, AVM, liens/foreclosure flags, owner | Medium–high | $0–$95 (RentCast) to $1k+/mo (BatchData/ATTOM) | **Yes — start RentCast; graduate ATTOM/BatchData** |
| **4** | **John’s / landlord’s off-market network** (expired conversations, “I know that owner”) | Yes | Warm intro | High | $0 | **Yes — first 5 files** |
| **5** | **USPS / vacancy / absentee** (mailing ≠ situs via assessor) | Yes via licensed or public data | Absentee landlord flag | Medium | Included in #3 | Yes as a *feature*, not a list |
| **6** | **Licensed MLS via partner agent** (RESO Web API / Bridge Interactive, IDX/VOW/BBO as granted) | Yes **if** a broker/MLS approves the use case | Active/sold listings, photos, agent of record | Low for *off-market*; high for **comps** | MLS dues + license | **Comps: yes. Prospecting off IDX: usually no** |
| **7** | **FSBO ads** (Craigslist, Facebook Marketplace) collected **manually** or via official APIs if any | Conditional — site ToS; no scraping at scale | Seller who already advertised | High | Time | Manual copy-paste into desk for v1 |
| **8** | **Purchased “motivated seller” CSV** from random Facebook ads | Risky | Stale phones, recycled DNC, litigator bait | Fake | Cheap for a reason | **No** |
| **9** | **People-search scrape** (TruePeopleSearch, FastPeopleSearch, Spokeo HTML) | No for production | Phones of uneven legality/quality | n/a | “Free” | **No** |
| **10** | **Zillow / Redfin / Realtor.com HTML scrape** | **No-Go as primary (or any automated) path** | Listings you are not licensed to reuse | Weak | Legal + proxy cost | **No** |
| **11** | **MLS member portal scrape / shared agent login** | **No-Go** | Full listings | — | Career + lawsuit | **No** |

### MLS / portal path — if John ever wants listings legally

1. Partner with a **licensed broker** in the target MLS.  
2. Apply for the correct feed (IDX vs VOW vs BBO) on **Bridge** or the MLS’s RESO Web API.  
3. Sign the data license; display required attribution; do not store/redisplay beyond the license.  
4. Use **sold** data for comps if the license allows; do **not** use IDX as a cold-call list of “people who listed with someone else.” Calling a listed seller to cut out their agent is both a reputation problem and, in many MLS rules, a participation problem.

Zillow Group data on Bridge is **not** a public Zestimate API. Access is provider-approved and ToS-bound. Unofficial “Zillow wrapper” APIs are a third-party scrape in a trench coat — treat as **No-Go** for anything with John’s name on it.

### Motivated-seller feature list (rules engine)

Score 0–100 from **licensed/public fields only**. Suggested weights for a landlord-buyer (not a wholesaler):

| Signal | Points | Notes |
|--------|--------|-------|
| Tax delinquent (county) | +25 | Strong; verify status date |
| Probate / deceased owner on title | +20 | Sensitive; different script; some states restrict |
| Absentee (mailing ≠ situs) + SFR | +15 | Tired landlord hypothesis |
| Ownership tenure ≥ 15 years | +10 | Equity, life event |
| Vacant / utility off (if licensed) | +10 | |
| Pre-foreclosure / NOD (ATTOM) | +20 | Time-sensitive; counsel on FDCPA-adjacent messaging |
| Code violations / open permits | +8 | |
| Active MLS listing | **−30** | Already represented; do not cold-call |
| Recently sold | block | |

LLM can *summarize* the file. LLM must not *invent* a signal.

---

## D. Pricing/comps approach + tool options

### What the number on the card actually is

v1 is **not** an appraisal, a Zestimate clone, or a binding offer. It is a **desk estimate**:

```
ARV  = median(sold comps) blended with AVM, haircut for condition
Repairs = heuristic (age, visible flags)  OR  John-entered
Offer_low  = f(strategy)   # see strategies
Offer_high = Offer_low + band (e.g. 5–8%)
Agent may quote only [Offer_low, Offer_high] and must say "estimate"
```

**Two strategies (John must pick one per lead):**

| Strategy | Formula (starting point, not gospel) | When |
|----------|--------------------------------------|------|
| **Hold (landlord)** | `min(AVM, comps) * 0.85` to start, **or** price off rent: `RentCast_rent * 12 / target_cap` minus rehab | Core Tobin adjacency. This is the product. |
| **Wholesale / flip** | Classic `70% * ARV − repairs` | Higher complaint rate; easier to sound like a spam buyer. **Out of scope for supervised MVP** unless John is already doing it with a license and counsel. |

Never let the model interpolate a new price mid-call because the owner “sounds motivated.” If they counter, the agent logs it and **transfers**.

### Comp rules (v1)

- Subject: same county, ±20% GLA, same beds ±1, same property type, sold last 6–12 months, radius 0.5–1.0 mi (rural: 5 mi or same tract).  
- Drop: active listings as sold comps; bank-owned as comps unless labeled; renovated vs wreck without adjustment.  
- Show John **3–5 comps** on the approve card with photos if the license allows.  
- If <3 good comps: status `needs_human_price` — no outbound with a number.

### Tool options

| Tool | Role | Pros | Cons | v1 fit |
|------|------|------|------|--------|
| **RentCast** | AVM + rent + comps, self-serve API | Cheap (free tier ~50 calls/mo; paid tens–low hundreds $/mo), JSON, good enough for a desk | Not a lender AVM; thinner liens/foreclosure | **Default for spike + interview** |
| **HouseCanary** | AVM + forecast | Stronger valuation story | Auth/pricing less indie-friendly | If John wants “serious” numbers |
| **ATTOM** | Parcel + AVM + recorder + foreclosure | One vendor for distress + value | Sales-led; responses heavy; $95–$1k+/mo class | **Graduate here** if desk continues |
| **CoreLogic / Cotality** | Institutional AVM, MLS ties | Deepest | Enterprise sales, overkill | No for side app |
| **Regrid** | Parcel geometry, zoning, owner | Maps / absentee | Not an AVM | Optional layer |
| **BatchData** | Property + skip + DNC flags | One pipe for enrich + contact | ~$1k/mo class; sales | If skip+data combined |
| **County assessor / sales** | Ground truth assessed value + some sales | Free, citable | Inconsistent APIs, lag | Always as a check |
| **MLS solds via partner** | Best comps | Licensed | Needs broker | v2 |
| **Zillow Zestimate via scrape/wrapper** | Familiar number | Owners know it | ToS; not yours to productize | **No** |
| **Gemini / GPT as “the appraiser”** | None | Fast | Hallucinated prices | **Forbidden as source of truth** |

### Offer card (what John sees before approve)

- Address, owner, mailing, score + why (bullet signals).  
- AVM point + range; RentCast (or ATTOM) comps table.  
- Suggested band + strategy tag (`hold`).  
- Repair guess with a slider John can override **before** approve.  
- Draft SMS (immutable after approve unless he edits).  
- Compliance strip: DNC Y/N, litigator, line type, TZ, last-contact.

### Cost to quote in conversation (required language)

> “I’m not an appraiser. Based on recent nearby sales we’d look at something in the **X to Y** range, assuming typical condition. If you want a firm number, I can have John walk the property.”

If the owner cites Zillow: acknowledge, do not argue, do not scrape live Zestimate. “Zillow is one estimate; we use sold comps. Happy to have John compare notes.”

---

## E. Skip-trace + SMS/voice stack options (Twilio / Vapi / Retell / etc.)

### Skip-trace (phones)

Skip-trace is **not** “Google the name.” It is a licensed append of consumer contact data, then a **scrub**. Accuracy claims (e.g. BatchData’s ~76% right-party-contact marketing number) are vendor-reported; assume 40–70% useful mobiles and budget for wrong-party contact scripts.

| Vendor | What it is | Pros | Cons | Fit |
|--------|------------|------|------|-----|
| **BatchData** Skip Trace API | Address/name → phones/emails + inline DNC/TCPA/litigator/deceased | Built for investors; API; reverse skip exists | ~$1k/mo class; you still own TCPA | **Best combined enrich+scrub if budget** |
| **Melissa Personator Search** | Name/address/phone/email search | Legit data vendor; flexible match modes | Not RE-specific; you add DNC elsewhere | Good alternative |
| **IDI Core / TruVision / TLO-class** | Enterprise skip | High coverage | Contracts, DPPA-ish use-case scrutiny | Overkill |
| **Twilio Lookup** (line type, SIM swap, reassigned) | Validates a number you already have | Cheap; catches VoIP/landline; reassigned numbers | **Not a skip-trace** | **Mandatory after** skip |
| **People-search HTML** | Scrape | — | ToS, quality, wrong-party, interview poison | **No** |
| **Manual** (John already has the number) | — | Perfect consent story if they gave it | Doesn’t scale | **Interview + first files** |

**Wrong-party rule:** first SMS must not assume “you own 123 Main.” Use “trying to reach the owner of 123 Main — if that’s not you, reply WRONG.” Wrong → suppress + do not dial.

### SMS

| Piece | Recommendation |
|-------|----------------|
| **CPaaS** | **Twilio** (already in Tobin). New subaccount, new number, **10DLC** brand + campaign. A2P 10DLC review will ask for use case; “real estate solicitation” is high scrutiny — expect a dedicated campaign, opt-out language, and sample messages. Toll-free is an alternative with its own verification. |
| **Do not** | Share core Tobin’s `+12064893667`. Do not use unregistered long codes at any volume. |
| **STM / STOP** | Twilio Advanced Opt-Out + your own `acquire_suppression` table. Honor STOP on all channels. |
| **First message** | Identity + property + how you got the address (public record / they inquired) + how to opt out. No “hey it’s Mike, saw your house 👀”. |
| **MMS / iMessage** | Skip in v1. |
| **Email** | Optional second channel; CAN-SPAM; worse for this ICP. |

### Voice platforms

All-in cost in 2026 is typically **~$0.10–$0.30/min**, not the headline $0.05. **You** are the caller of record, not Vapi/Retell/Bland (see *Lamb v. Mortgage One* style vendor-chain theories). Platforms do not eat TCPA.

| Platform | Model | Latency (ballpark) | $ (realistic) | Twilio reuse | Pros | Cons | Fit |
|----------|-------|--------------------|---------------|--------------|------|------|-----|
| **Twilio ConversationRelay** | You stream audio ↔ your LLM | Depends on your STT/TTS | ~$0.07/min relay **plus** Voice + model | Native | One vendor with SMS; policy stays in your repo | More engineering; you assemble STT/TTS | Best **long-term** if John stays on Twilio |
| **Vapi** | Orchestrator; BYO LLM/STT/TTS/Twilio | ~500–700ms median | $0.05/min host + providers ≈ $0.13–$0.36 | Yes (bring Twilio) | Fastest **demo**; tool calling; dashboard | Compliance add-ons; easy to over-automate outbound | **Best interview spike** |
| **Retell AI** | Managed voice + transparent component $ | ~600–800ms | Voice engine ~$0.055 + TTS + LLM + tel; often ~$0.10–$0.31 | Yes | Clear pricing; outbound kit; SOC2/HIPAA story | Still your TCPA; less “bring every knob” than Vapi | Strong alternative to Vapi |
| **Bland** | Bundled minute | Claims low; independent tests mixed | Start ~$0.14/min all-in class | Owns tel or BYO | Simple invoice | Less control; pricing has moved | Only if you want zero assembly |
| **ElevenLabs + DIY SIP** | TTS only | Great TTS, not a contact center | TTS cheap; tel extra | Via Twilio | Pretty voice | Cloning a “local investor” without disclosure is a **No-Go** | TTS vendor, not the product |
| **Bland/Vapi “make it sound human so they don’t know”** | — | — | — | — | — | **No-Go.** FCC 24-17: lifelike ≠ exempt. CA AB 2905: disclose artificial voice. | Forbidden |

**STT/TTS for a Vapi/ConvRelay spike:** Deepgram (STT) + Gemini realtime or GPT-4.1-mini + a **non-cloned** stock voice (ElevenLabs Flash or Cartesia). Do not clone John’s voice for outbound.

### Channel policy (Conditional Go)

1. **Never** first-touch with AI voice on a skipped number. That is the TCPA nuclear scenario (artificial voice + marketing + wireless + no PEWC).  
2. First-touch = **one SMS** after human approve, or a **letter**.  
3. Voice = (a) inbound to the Acquire number, or (b) outbound only after the owner texts/calls back and agrees to a call, logged.  
4. Concurrent lines: **1**. This is a desk, not a predictive dialer.  
5. If John wants to *hear* the agent: he calls the demo number (inbound). That is the United-safe path.

### Rough unit economics (order of magnitude)

| Item | Spike (interview) | 20 supervised files/mo |
|------|-------------------|-------------------------|
| RentCast | $0–$50 | $50–$200 |
| Skip-trace | $0 (fixtures) | $20–$150 (or BatchData min if subscribed) |
| Twilio SMS | pennies | < $20 |
| Voice minutes | 30–60 min rehearsal | 0–3 hrs if SMS-first |
| 10DLC / numbers | $0–$50 | $20–$100 |
| **John’s time** | 1–2 days prompt + demo | The real cost: approve + handoff |
| Counsel letter | — | **Do this before any live owner SMS** |

Voice API cost will not be the bill that hurts. **A single TCPA claim** will.

---

## F. Conversation design (disclosure, handoff, objection handling)

### Design goals

- Sound **competent and calm**, not “human so they don’t notice.”  
- Disclose in the first turn.  
- Never argue price.  
- Get to a disposition in < 3 minutes.  
- Make handoff the *win*, not a failure.

### Identity

**Working persona:** “Alex at Tobin Acquire, calling/texting for John [Last], a local buyer.”  
Not a fake neighbor. Not “your property manager.” Not core Tobin’s tenant bot.

If John is not a licensed agent, the script **must not** imply brokerage (“I can list your home,” “buyer’s agent”). Investor-buyer language only.

### SMS v1 (after approve)

```
Hi, this is Alex with Tobin Acquire (an AI assistant for John [Last]).
We're a local cash/conventional buyer looking at [123 Main St] from public records —
not an MLS listing. If you're the owner and open to a conversation about selling,
reply YES. If not, reply STOP and we won't text again. If we have the wrong person, reply WRONG.
```

Edit for truth: if the lead was **inbound**, say so (“you asked for a number on our form”). Never claim public records if the source was a purchased list.

### Voice — inbound or consented outbound (first 15 seconds)

Follow a **defensive disclosure** that covers FCC identity rules, likely future federal AI disclosure, Texas-style 30-second rules, and California AB 2905 spirit (artificial voice + nature of call + who is calling):

> “Hi, this is Alex, an **AI assistant** for John [Last] at Tobin Acquire. This call is **recorded**. I’m not a person. I can answer questions about a possible purchase of [123 Main] or **transfer you to John**. Is this the owner, and is now an okay time?”

If no / wrong person / minor: apologize, suppress, hang up.  
If they want a human immediately: transfer. Do not “try to handle it.”

**California extra (if calling CA):** AB 2905 is aimed at **automatic dialing-announcing devices** and wants a **natural-voice** announcement that the message uses an artificial voice, plus consent to hear it. For a Conditional Go, **do not auto-dial CA**. Inbound or John-dials-then-conferences is safer until counsel maps ADAD vs conversational AI. Florida and other mini-TCPAs similarly argue for **no cold AI outbound**.

### Turn-taking and “human-like”

| Do | Don’t |
|----|-------|
| Short turns, one question | Monologue pitch |
| Allow barge-in | Talk over “hello?” |
| Fillers sparingly | Fake “uh, so yeah I was driving by” |
| Explicit uncertainty | Invent a tour date or a dollar |
| Match their language (sell / not sell) | Pressure (“this offer expires at 5”) |

United translation: same as not pretending to be a gate agent.

### Objection handling (closed book)

| Owner says | Agent does |
|------------|------------|
| “Not interested” | “Understood. I’ll mark you as no-contact. Sorry to bother you.” STOP all channels. |
| “Take me off your list” / “STOP” | Confirm once, suppress, no “are you sure?” loop. |
| “How did you get my number?” | Truth: “We matched the owner of record on public/licensed property data to a skip-trace vendor. If you want this number deleted, I’ll do that now.” |
| “Is this a recording / are you a robot?” | “Yes — I’m an AI assistant. I can transfer you to John.” |
| “What’s it worth?” | Read the **approved band** + appraisal disclaimer. No new math. |
| “Zillow says more” | Don’t fight. Offer John + comps. |
| “Are you a realtor?” | Honest yes/no. If no: “We’re a buyer, not listing the property.” |
| “Send something in writing” | Email/SMS the band + “not an offer until John signs.” |
| Legal / “I’ll sue” / shouting | Immediate transfer or polite end. No debate. |
| Price negotiate | “I can’t move the number. Transferring you to John.” |
| “Call back later” | `schedule_callback` in **quiet hours**; still disclosed AI next time. |
| Tenant / not owner | “Thanks — please ignore. We’ll stop.” Suppress. |

### Qualification (only if they engage)

1. Are you the owner or authorized to discuss a sale?  
2. Any reason you’d consider selling in the next 12 months? (open)  
3. Occupied / rented / vacant?  
4. Condition 1–5 gut check (not a home inspection).  
5. Preferred next step: John call, walk-through, or written range.

Stop after they decline. Do not “just one more question.”

### Handoff

- **Warm transfer** to John’s cell with a 15-second whisper: address, owner name, band quoted, objection.  
- If John misses: SMS both parties a scheduling link (once).  
- Desk records `handed_off` + recording URL.

### Prompt / eval (interview gold)

Ship a **golden set** of 15 transcripts (wrong number, STOP, Zillow objection, “are you real?”, price ask, transfer). Score: disclosure in turn 1, no invented price, opt-out honored, transfer on request. That eval is more United-relevant than a live dialer.

---

## G. Compliance (TCPA, DNC, recording, AI disclosure) — gates checklist

**This is not legal advice.** John needs a lawyer licensed in the target state(s) before any live owner contact. The 2026 docket is active: FCC 24-17 (Feb 8, 2024) treats AI-generated voices as **artificial/prerecorded**; August 2024 NPRM (FCC 24-84) proposed **in-call AI disclosure** and AI-specific consent language (not a final federal rule as of this writing, but states did not wait). Statutory damages **$500–$1,500 per call**, no aggregate cap; class actions are the real risk. *Caller of record is John / the entity, not the voice vendor.*

### What the law-shaped reality is (2026)

| Topic | Practical rule for Tobin Acquire |
|-------|----------------------------------|
| **AI voice** | Equals prerecorded/artificial under TCPA. “Sounds live” does not exempt. |
| **Marketing vs informational** | Buying someone’s house is **commercial solicitation**. Treat outbound as **telemarketing**. |
| **PEWC** | Prior express **written** consent (E-SIGN OK) for marketing artificial-voice calls to cell phones in most of the US. Fifth Circuit *Bradford* (Feb 2026) loosened *written* in TX/LA/MS only — **do not** generalize. Florida and others still stricter. |
| **Established business relationship** | Does **not** authorize AI marketing calls. Core Tobin tenants ≠ consent to acquire outbound. |
| **SMS** | TCPA applies to autodialed texts; 10DLC + STOP is necessary but **not sufficient**. Recycled/reassigned numbers are a known plaintiff pattern — use Lookup reassigned + “WRONG”. |
| **DNC** | National DNC + state lists + internal. Scrub **before** approve, not after a complaint. |
| **Hours** | Federal: 8am–9pm **called party local time**. Some states tighter (e.g. FL often treated as 8am–8pm). Compute TZ per number. |
| **Recording** | All-party states (CA, FL, PA, etc.): announce recording and get a yes. One-party (WA is one-party; still announce for brand). |
| **CA AB 2905** | ADAD + artificial voice: disclose AI in the opening announcement. Default: **no auto-dial into CA**. |
| **CA SB 1001** | Bot disclosure for commercial transactions. Disclose. |
| **DPPA / skip-trace** | Use vendors who warrant permissible purpose; don’t scrape DMV. |
| **FDCPA** | If messaging **pre-foreclosure** as if collecting a debt, you can wander into debt-collection rules. Script is “buyer interested in the property,” never “you’re behind on your mortgage.” |
| **Licensing** | If the pitch is brokerage (listing, representing buyers generally), need a license. Pure principal-buying-for-own-account is different — still don’t impersonate an agent. |

### Hard gates checklist (block outbound unless all pass)

**Entity / policy**

- [ ] Legal entity named on SMS/voice (not “Alex” only).  
- [ ] Written use-case memo: principal buyer vs wholesaler vs broker.  
- [ ] Separate Twilio subaccount + 10DLC campaign approved **or** interview stays on inbound/consented.  
- [ ] Counsel has reviewed SMS + voice scripts for target state(s).

**Lead source**

- [ ] Source ∈ {inbound PEWC, county public, licensed API, manual/off-market}.  
- [ ] Source ∉ {Zillow scrape, MLS login scrape, people-search scrape, mystery CSV}.  
- [ ] If inbound: timestamped consent text that names entity, number, **SMS + possible AI call**, not a condition of a service they were already getting.

**Identity of called party**

- [ ] Owner-of-record match to skip-trace above a vendor confidence threshold.  
- [ ] Not a known litigator.  
- [ ] Not deceased.  
- [ ] Not a minor / school / hospital number (line-type + crowding).  
- [ ] Twilio Lookup: not reassigned since skip; landline vs mobile recorded.

**Suppression**

- [ ] Not on National DNC (unless an EBR/PEWC exception **actually** applies — default: treat DNC as **no**).  
- [ ] Not on state DNC.  
- [ ] Not on internal STOP/WRONG/not-owner.  
- [ ] No contact in last N days (suggest 90) unless they inbound.

**Channel**

- [ ] Human approve recorded (user, timestamp, lead_id, channel, script version, offer band).  
- [ ] `AUTO_ACQUIRE_OUTREACH` is false.  
- [ ] Quiet hours OK in **their** TZ.  
- [ ] SMS first for any skipped number; voice only if inbound or documented consent to call.  
- [ ] One attempt; no parallel dialer; no voicemail drop as a loophole (prerecorded VM is still artificial voice).

**In-conversation**

- [ ] Turn-1 AI disclosure.  
- [ ] Recording disclosure + halt if all-party and no consent.  
- [ ] Immediate STOP / transfer / wrong-party handlers tested.  
- [ ] Price only from locked band.  
- [ ] Transcript stored; retention policy set (e.g. 2 years for defense, not forever marketing).

**Never “gates”**

- [ ] No “make the voice more human so they stay on.”  
- [ ] No scraping to refill the queue when licensed data is empty.  
- [ ] No using tenant phones from core Tobin.

### Recording & privacy

- Store recordings in a bucket with access logs (John + counsel).  
- Do not feed owner recordings into public model-training. Prefer zero-retention where the voice vendor allows.  
- CCPA/state privacy: skip-trace data is personal information; have a deletion path when they say WRONG/STOP.

---

## H. MVP vs v2 vs out-of-scope

### MVP-A — Interview showcase (Go, ~docs + thin spike if John says so)

- 3 fixture leads; 1 volunteer who signed a one-pager consent.  
- Desk card UI or even a Notion/JSON is fine.  
- Vapi or Retell inbound number: disclosure, comps tool, objections, transfer to John.  
- Golden-set eval (15 conversations).  
- **No** live skip-trace to strangers. **No** MLS scrape.  
- Outcome: 8–10 minute United demo + architecture diagram from this doc.

### MVP-B — Supervised desk (Conditional Go)

- One metro John knows.  
- ≤ 20 leads from county + RentCast (or ATTOM trial) + optional inbound form.  
- Skip-trace vendor with DNC flags **or** manual numbers John already has.  
- Approve email/webhook clone of Places gate.  
- SMS-only outbound; voice inbound.  
- John watches every thread (same as first Tobin Twilio tickets).  
- Success metric: **zero** unapproved sends; **zero** STOP complaints to Twilio; ≥ 1 civil conversation that was allowed to happen. Not “contracts signed.”

### v2 (only if MVP-B is boringly clean)

- RESO/Bridge comps via a broker partner.  
- BatchData (or similar) as the enrich pipe.  
- ConversationRelay to keep voice inside Twilio.  
- Letter + SMS sequence with frequency caps.  
- Landlord-facing: “watch these ZIPs for absentee + tax delq.”  
- Offer strategy: hold vs wholesale as a flag, still human-priced.

### Out of scope (No-Go unless the world changes)

- Automated MLS / Zillow / Realtor.com / Redfin scrape.  
- Undisclosed or voice-cloned outbound.  
- Predictive / power dialer, voicemail drops, STIR/SHAKEN-dodging.  
- National “we buy houses” ads without PEWC infrastructure.  
- Merging acquire graph into `ai-agent/` maintenance runtime.  
- Using core Tobin tenant/vendor numbers.  
- Multi-state auto-dial.  
- Pricing the side app as SaaS.  
- Any “set AUTO_ACQUIRE_OUTREACH=true.”

---

## I. Demo script for United Airlines interview

**Audience:** hiring loop that cares about conversational + voice agents (customer care, policy, interruption, tools, escalation).  
**Time:** 8–10 minutes. **Do not** demo a scrape or a cold call to a stranger.

### Narrative (45 seconds)

> “I run Tobin, a supervised repair coordinator for small landlords — tenant request, AI triage, preferred vendor, human approve before any cold vendor SMS. The side exploration is **Tobin Acquire**: same discipline, different domain. The naive version is scrape Zillow and robocall owners. We treated that as a **No-Go**. The version I built for this conversation is a **policy-gated voice agent**: licensed or fixture data, a human approve step, disclosed AI, tool-use for a price band, and a warm transfer. That’s the same shape as an airline agent that may only quote what the fare tool returns and must hand off when policy ends.”

### Setup (before the loop)

- Demo number on Vapi/Retell (or Twilio inbound).  
- Interviewer (or John) is the “owner” of **414 Maple Ave** (fixture).  
- Second phone is “John” for transfer.  
- Screen share: lead card with `awaiting_approve` → click Approve → show that **voice cannot dial this number** until a reply; then switch to **inbound** “owner calls us” which is the legal analog of a customer calling United.

### Minute-by-minute

| Min | What happens | What to point at |
|-----|----------------|------------------|
| 0:00 | Lead card: public-record flags, RentCast comps, offer band $310–335k, DNC=N, source=county | “Model did not invent the price. Tools did.” |
| 0:45 | Attempting outbound without approve → UI refuses | Same as Tobin `AUTO_OUTREACH=false` |
| 1:00 | Approve SMS (or skip to inbound if time) | Audit: who approved |
| 1:30 | **Inbound call** from interviewer | Real-time voice |
| 1:40 | Disclosure + recording + “I’m AI” | Non-negotiable |
| 2:00 | “How did you get my number?” | Truthful source |
| 2:30 | “Zillow says $410k” | Tool: read comps, no fight, no scrape |
| 3:30 | “Are you a realtor?” | Honest licensing line |
| 4:00 | Barge-in: interviewer interrupts | Latency / turn-taking |
| 4:30 | “Give me a better number” | **Refuse**; transfer policy |
| 5:00 | Warm transfer whisper | Human in the loop |
| 5:45 | Hang up; show transcript + `handed_off` + that STOP would suppress | Eval / audit |
| 6:15 | Slide: scrape path vs licensed path | “We challenged the obvious architecture” |
| 7:00 | Slide: TCPA gates checklist | Production thinking |
| 7:45 | Q&A | If asked “would you cold-call?”: **No, not with AI voice.** |

### Backup if voice vendors flake

Run the same conversation in **SMS or a local Gemini voice chat** with tool JSON on screen. Say: “The policy is the product; the TTS vendor is swappable.” That is a stronger engineering answer than a pretty voice.

### Questions to be ready for

- *Why not scrape?* — ToS, copyright, weak signal, CFAA-adjacent circumvention, interview/brand.  
- *Isn’t disclosure bad for conversion?* — Conversion without consent is not a KPI we will optimize.  
- *How is this like United?* — Fare tool = comps tool; gate agent transfer = John; quiet hours = TCPA hours.  
- *What model?* — Gemini (already in Tobin) + optional OpenAI; **tools own facts**.  
- *What would you not put in production?* — Auto-outreach flag, cloned voice, portal scrape.

---

## J. Risks, costs, open decisions for John

### Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| TCPA class action on AI outbound | Career-ending for a side app | SMS-first, no cold AI voice, counsel, tiny N |
| ToS/C&D from portals | High if scrape | Don’t scrape |
| Wrong-party / “you called my grandma” | High brand | WRONG keyword, Lookup reassigned, conservative match |
| 10DLC campaign rejected | Medium | Inbound-first; letter; or stay interview-only |
| Core Tobin number reputation | High | Separate SID/number |
| Hallucinated offer | Medium | Locked band; eval set |
| Licensing (acting as broker) | Medium | Principal-buyer script only until licensed |
| Skip-trace vendor overclaim | Medium | Manual audit first 20 phones |
| Opportunity cost vs $99/mo ops pilot | High | **Ops pilot is the revenue path.** Acquire is exploration. |

### Costs (if he says go)

| Bucket | Interview spike | Supervised 20-file month |
|--------|-----------------|--------------------------|
| Time (John + agent) | Dominant | Dominant |
| Data API | $0–$50 | $50–$300 |
| Skip + DNC | $0 | $0–$1k (vendor minimums) |
| Twilio + voice | < $20 | < $100 |
| 10DLC / brand | $0–$50 | $50+ |
| Counsel | Optional | **Budget a real consult** |
| Ads for inbound PEWC | $0 | Optional, easy to waste |

### Open decisions (John must answer before any build)

1. **Purpose mix:** interview-only vs real desk vs both? If interview-only, stop at MVP-A.  
2. **Entity & license:** personal name, LLC, licensed agent, or principal buyer? This rewrites the script.  
3. **Geography:** which state/metro? CA/FL = assume **no outbound AI dialer**.  
4. **Strategy:** landlord-hold (aligned with Tobin) vs wholesale? Default **hold**.  
5. **Caller of record & phone:** new Twilio subaccount? (Should be yes.)  
6. **Data vendor budget:** RentCast-only vs ATTOM vs BatchData?  
7. **Skip-trace:** paid vendor vs only numbers people gave us?  
8. **Counsel:** who reviews scripts before the first non-volunteer SMS?  
9. **Voice vendor for spike:** Vapi vs Retell vs ConversationRelay? (Recommendation: **Vapi for demo, ConvRelay if this becomes real.**)  
10. **Relationship to core pilot:** confirm Acquire does **not** delay Netlify redeploy, JOH-6, or the $99/mo ask.  
11. **Name:** “Tobin Acquire” vs something that doesn’t imply MLS.  
12. **Will John take transfers live during a demo?** Need a backup voicemail policy.

If (1) is interview-only, decisions 6–8 can wait. If (1) includes live owners, **8 is a blocker**.

---

## K. Recommended next build spike IF he says go (still approve-gated)

Still **no scrape, no dialer, no production keys in git, no changes to `ai-agent/` runtime.**

### Spike 0 (this PR) — done when this doc merges

John reads §J and replies: **Interview-only / Conditional desk / Kill.**

### Spike 1 — Interview (if “Go” on MVP-A)

1. New folder `docs/acquire-spike/` or a **throwaway** repo — not `ai-agent/` nodes.  
2. Fixture `leads.json` (3 properties) + locked offer bands.  
3. Vapi/Retell assistant with: disclosure opener, `get_lead_file` / `get_comp` tools, transfer tool, STOP.  
4. One-page desk: show lead, disable Call until `approved=true`, log approve.  
5. Record a 5-minute backup video of the happy path.  
6. Golden eval: 10 scripted tests, pass/fail on disclosure and no extra prices.  
7. Volunteer consent PDF (one page).

**Exit:** John can run the United script in §I without touching a stranger.

### Spike 2 — Desk plumbing (only if Conditional Go)

1. Schema `acquire_leads`, `acquire_events`, `acquire_suppression`.  
2. RentCast (or ATTOM trial) pull + rule-based score.  
3. Clone approve webhook (`AUTO_ACQUIRE_OUTREACH=false`).  
4. Twilio **subaccount** SMS with the §F template; STOP/WRONG.  
5. Twilio Lookup on every number.  
6. **No voice outbound.** Inbound webhook → same assistant as Spike 1.  
7. Manual CSV import from a **county download John obtained legitimately**.

**Exit:** 10 files to `awaiting_approve`; 1–2 SMS to people John personally knows **or** who inbounded.

### Spike 3 — Explicitly not scheduled

Skip-trace to cold owners, MLS, predictive dial, `AUTO_*=true`, sharing the ops Twilio number.

### Build rules for whoever implements later

- Docs and spikes may live under `docs/` and a new top-level `acquire/` **only after** John says go.  
- Default env: outreach off.  
- Tests: approve gate, STOP, quiet hours, “no price without band.”  
- Do not “just add a node” to `graph.py`.

---

## Appendix: mapping to core Tobin files (read-only)

| Core file | Lesson for Acquire |
|-----------|-------------------|
| `ai-agent/graph.py` | Conditional edges after research; outreach not automatic |
| `ai-agent/settings.py` | `AUTO_OUTREACH` default false; empty approve secret → deny |
| `ai-agent/main.py` `POST /webhook/approve-outreach` | Copy the shape, new path |
| `docs/pilot-offer.md` | Ops revenue stays first; Acquire is not the $99 product |
| `STATUS.md` | Claim/finish here so Grok Bot doesn’t treat this as a P0 vs Netlify |

---

## Document control

| | |
|--|--|
| Type | Brainstorm / design. Not an implementation plan with a ship date. |
| Author | Cursor cloud agent, 2026-09-15 |
| Intended readers | John, Grok Bot (product), future implementer |
| Next edit | After John answers §J |
| Related live systems | Do not configure. Core: Netlify form + Render API + Twilio ops |
