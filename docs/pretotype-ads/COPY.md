# TobinAI Meta pretotype — ad copy

**Geo default:** Austin, TX  
**Offer:** 2 weeks free, then $99/mo  
**Destination base:** https://cool-cannoli-68cac9.netlify.app/submit-request  

**DO NOT SPEND** until notify PR #5 is merged **and** Render retest passes. Creatives + copy only.

---

## Concept A — Night dispatcher

**Image:** `concept-a-night-dispatcher-1080.png` (feed) · `concept-a-night-dispatcher-1080x1920.png` (Stories)

### Primary text (short ≤125)
When the AC dies at 11pm, you become the night dispatcher. Tobin triages the ticket and notifies your vendors — you only approve cold outreach.

### Primary text (long ≤500)
Small landlords shouldn’t run a 24/7 dispatch desk from their phone. TobinAI is a supervised maintenance coordinator: tenant submits a ticket, AI triage classifies urgency, preferred vendors get notified, and Google Places cold SMS only goes out after you approve. Austin pilot: 2 weeks free, then $99/mo for up to 5 properties. Start with one ticket — keep the veto on strangers.

### Headline (≤40)
Stop being the night dispatcher

### Description (≤30)
Austin landlords · free pilot

### CTA button
Learn more

### Destination URL
https://cool-cannoli-68cac9.netlify.app/submit-request?utm_source=meta&utm_medium=paid&utm_campaign=austin_pilot_sep26&utm_content=concept_a

---

## Concept B — Three steps

**Image:** `concept-b-three-steps-1080.png` (feed) · `concept-b-three-steps-1080x1920.png` (Stories)

### Primary text (short ≤125)
Ticket → Tobin → Vendor. Tenants submit once. Tobin triages and notifies preferred vendors. You approve any cold outreach.

### Primary text (long ≤500)
Maintenance shouldn’t live in scattered texts. With TobinAI: (1) Tenant sends a ticket. (2) Tobin triages category and urgency. (3) Preferred vendors get the job; Places candidates wait for your approve. Supervised pilot for Austin landlords — 2 weeks free, then $99/mo. Send your first ticket and see the loop without hiring a PM.

### Headline (≤40)
Ticket. Tobin. Vendor.

### Description (≤30)
3 steps. You stay in control.

### CTA button
Sign up

### Destination URL
https://cool-cannoli-68cac9.netlify.app/submit-request?utm_source=meta&utm_medium=paid&utm_campaign=austin_pilot_sep26&utm_content=concept_b

---

## Concept C — Price / offer

**Image:** `concept-c-price-1080.png` (feed) · `concept-c-price-1080x1920.png` (Stories)

### Primary text (short ≤125)
2 weeks free, then $99/mo. Supervised maintenance coordination for Austin landlords — preferred vendors notified; cold SMS only after you approve.

### Primary text (long ≤500)
Clear offer, no pricing menu: TobinAI runs a 2-week free supervised pilot, then $99/month for one landlord and up to 5 properties. Tenants use the web form. AI triage + preferred-vendor notify are included. Google Places outreach stays gated until you say yes. Built for independent Austin landlords who are too small for a PM and too busy to dispatch every repair themselves.

### Headline (≤40)
2 weeks free · then $99/mo

### Description (≤30)
Austin pilot · up to 5 doors

### CTA button
Sign up

### Destination URL
https://cool-cannoli-68cac9.netlify.app/submit-request?utm_source=meta&utm_medium=paid&utm_campaign=austin_pilot_sep26&utm_content=concept_c

---

## Landing one-pager paste

Use on the form page hero / Meta Instant Experience / notes field if needed:

**Problem**  
When a tenant texts “the AC died,” you become the night dispatcher — triage, chase vendors, update the tenant. That loop eats nights and weekends.

**3 steps**  
1. Tenant submits a ticket on the form.  
2. Tobin AI triages category, urgency, and a vendor-ready summary.  
3. Preferred vendors get notified; Places cold SMS only after you approve.

**Offer**  
Austin supervised pilot: **2 weeks free**, then **$99/mo** (up to 5 properties). Invoice after trial — no card required to start.

**CTA**  
Start free pilot → send your first ticket:  
https://cool-cannoli-68cac9.netlify.app/submit-request?utm_source=meta&utm_medium=paid&utm_campaign=austin_pilot_sep26&utm_content=landing_paste

---

## Tracking checklist

Before any spend (after PR #5 + Render retest):

- [ ] Meta Pixel installed on landing domain; events: **PageView** + **Lead** (form submit success)
- [ ] Confirm Lead fires once per successful ticket create (not on page load)
- [ ] UTMs on every ad URL: `utm_source=meta` · `utm_medium=paid` · `utm_campaign=austin_pilot_sep26` · `utm_content=concept_a|concept_b|concept_c`
- [ ] Lead sheet columns: `timestamp` · `utm_content` · `name` · `phone/email` · `property/city` · `ticket_id` · `qualified?` · `booked_call?` · `notes`
- [ ] Campaign budget: **$100 hard cap** (account or campaign spend limit)
- [ ] Ads Manager naming: `Austin Pilot Sep26 / Concept X / Feed|Stories`

---

## Kill / pass criteria

| Signal | Action |
|--------|--------|
| **$100 cap** | Absolute max for this pretotype; do not raise without a new decision |
| ~0 form submits after ~**$80** spend, or dead CTR (near-zero link clicks) | **Kill** — pause all ads same day |
| ≥**3 qualified submits** (real Austin landlord / property context) **or** ≥**1 booked call** | **PASS** — pause or throttle; debrief before next dollar |
| Fake leads / spam / non-landlord | Mark unqualified; do not count toward PASS |

**Qualified** = independent landlord (or decision-maker) with ≥1 rental door in/near Austin who could start a supervised pilot.

---

## Spend gate (hard)

**DO NOT SPEND** until:

1. Notify / approve-path **PR #5** is merged into the pilot branch, and  
2. **Render** retest confirms the live agent path still healthy (`/health` + a supervised smoke).

Creatives in this folder are for Ads Manager upload prep only — not a green light to run.
