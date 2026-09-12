# TobinAI — supervised pilot offer

**For:** one independent landlord (1–5 properties)  
**Ask:** two free weeks, then **$99/month**  
**Live tenant form:** https://cool-cannoli-68cac9.netlify.app/  
**API:** https://tobinai.onrender.com

This is the commercial offer for v1. Not a pricing menu. Invoice monthly after the trial (no card required to start).

---

## The problem

When a tenant texts “the AC died,” the landlord becomes the night dispatcher: judge urgency, pick a vendor, chase a reply, text a backup, then update the tenant. That loop is 30–60 minutes per ticket and it lands on nights and weekends.

Small landlords are too small for a property manager (8–12% of rent) and too busy to run every repair themselves. Requests live in texts. Preferred vendors live in someone’s head. Tenants wait.

---

## What Tobin does

Tobin is a repair coordinator, not a chatbot.

1. **Triage** — Tenant submits on the web form. AI classifies category, urgency, and a vendor-ready summary.
2. **Vendor match** — If a preferred vendor is in the database for that trade, Tobin texts/emails them with the ticket and a YES/NO reply.
3. **Supervised outreach** — If no preferred vendor exists, Tobin researches nearby shops (Google Places), emails the landlord the candidate list, and **does not send cold SMS** until the landlord approves.

The landlord gets the coordination. The landlord keeps the veto on strangers.

---

## Supervised vs automated in v1

v1 is a **supervised single-landlord pilot**. `AUTO_OUTREACH=false`. This is not multi-tenant SaaS and not unattended cold outreach.

| Step | Automated | Supervised (human) |
|------|-----------|--------------------|
| Tenant intake + reference number | Yes | — |
| AI category / urgency / summary | Yes | — |
| Tenant “we got it” SMS | Yes | — |
| SMS/email to **DB preferred vendors** | Yes | Landlord lists who is allowed |
| Google Places candidate research | Yes | — |
| Cold SMS to Places vendors | **No** until approve | Landlord (or John) approves via `POST /webhook/approve-outreach` |
| Vendor YES/NO + landlord notify | Yes (after someone was contacted) | John watches Twilio on the first live tickets |

**In short:** preferred vendors can be notified without a per-ticket click. Places vendors cannot. That gate stays on for the pilot.

---

## Recommended price (the one structure)

**2-week supervised pilot at $0, then $99/month** for one landlord and up to 5 properties.

| Term | Detail |
|------|--------|
| Trial | 14 days, one landlord, live tickets |
| Then | $99 / month, billed in arrears |
| Included | Intake, AI triage, preferred-vendor notify, landlord-approved Places outreach, tenant + landlord updates |
| Cap | 5 properties / ~20 units. Extra doors: talk, don’t auto-upgrade |
| Cancel | After the first paid month, cancel anytime (end of that month) |
| Payment | Invoice (ACH, card, or Venmo). No self-serve billing yet |

**Why this and not a menu:** $99 is a clear yes/no. It is far below a PM’s per-unit fee and high enough that the landlord is a customer, not a demo. A per-ticket fee would need metering we do not have. The older $49 “autopilot” number assumed no human in the loop; v1 still has one.

---

## What the landlord must provide

Before day 1:

1. **Decision-maker email** — receives approve-outreach mail and ticket summaries (`LANDLORD_EMAIL`).
2. **Property list** — address and unit IDs for every door in the pilot.
3. **Preferred vendors** — for each trade they already use: name, phone, optional email, category (plumbing, HVAC, electrical, general). These can be notified without extra approval.
4. **Who approves Places lists** — landlord or John; same-day reply expected (target: 4 business hours).
5. **Tenant path** — they send tenants the live form URL (or John hosts a short link).

John provides Twilio, the form, and the approve webhook. The landlord does not need to install software.

---

## Pilot success metric

The trial **succeeds** if both are true at day 14:

1. **Volume:** at least **5 tickets** handled end-to-end (submit → triage → vendor contacted or landlord given a Places list to approve).
2. **Speed:** median **time-to-vendor ≤ 2 hours** (tenant submit → first preferred-vendor SMS) on tickets that already have a DB vendor, measured during 8am–8pm local.

**Hard fail:** any Google Places SMS sent without an approve-outreach action.

If volume is under 5 because tenants simply did not file, success is **coverage** (the form stayed live for 14 days and every submitted ticket met the speed + gate rules). The paid conversion ask is the same: $99/month to keep the coordinator on.

---

## How to say it

> Two weeks free. I sit on the vendor texts with you. After that it’s $99 a month for your properties — your regular vendors get the job automatically; anyone new I found online only gets a text after you say yes.
