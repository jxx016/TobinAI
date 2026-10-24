# 🏗️ Tobin AI - System Architecture

## 📊 Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Landing Page    │  │ Maintenance Form │  │  Status Check    │  │
│  │  (Port 5555)     │  │   (Port 5173)    │  │   (Port 5173)    │  │
│  │                  │  │                  │  │                  │  │
│  │ • Marketing      │  │ • Submit Request │  │ • Enter Ref #    │  │
│  │ • Features       │  │ • Get Ref Number │  │ • View Details   │  │
│  │ • Admin Link     │  │ • Check Status   │  │ • See Status     │  │
│  │ • Submit Button  │──┼─────────────────>│  │                  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                              │                         │             │
└──────────────────────────────┼─────────────────────────┼─────────────┘
                               │                         │
                               │ POST                    │ GET
                               ↓                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         n8n WORKFLOWS                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  MAIN WORKFLOW: Submit Maintenance Request                     │ │
│  │                                                                │ │
│  │  [Webhook] → [Postgres Insert] → [AI Agent]                   │ │
│  │      ↓              ↓                  ↓                       │ │
│  │  Receive Form   Save to DB     Analyze Issue                  │ │
│  │                 Get ID         • Category                      │ │
│  │                                • Urgency                       │ │
│  │                                • Summary                       │ │
│  │                                • Query Vendors                 │ │
│  │                                                                │ │
│  │  [Code Node] → [Postgres Update] → [Switch by Urgency]        │ │
│  │      ↓              ↓                    ↓                     │ │
│  │  Generate Ref   Update Request    Route by Priority           │ │
│  │  TM-DATE-####   with AI Data                                  │ │
│  │                                                                │ │
│  │  [Twilio SMS] → [Email Landlord] → [Wait] → [Check Response]  │ │
│  │      ↓              ↓                ↓           ↓            │ │
│  │  Notify Vendor  Summary Email   15 min    Vendor Reply?      │ │
│  │                                                                │ │
│  │  [Respond to Webhook] ─────────────────────────────┐          │ │
│  │      ↓                                              │          │ │
│  │  Return reference_number to frontend                │          │ │
│  └────────────────────────────────────────────────────┼──────────┘ │
│                                                        │            │
│  ┌────────────────────────────────────────────────────┼──────────┐ │
│  │  NEW WORKFLOW: Check Request Status                │          │ │
│  │                                                     │          │ │
│  │  [Webhook GET] → [Postgres Query] → [IF Exists?]   │          │ │
│  │      ↓                ↓                  ↓          │          │ │
│  │  ?ref=TM-###    Find by request_id   Check Result  │          │ │
│  │                                                     │          │ │
│  │  [Respond Found] ←─── YES ───┘                     │          │ │
│  │  [Respond Not Found] ←── NO                        │          │ │
│  │      ↓                                              │          │ │
│  │  Return request details or error                   │          │ │
│  └────────────────────────────────────────────────────┼──────────┘ │
│                                                        │            │
└────────────────────────────────────────────────────────┼────────────┘
                                                         │
                                                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DATABASE                             │
├─────────────────────────────────────────────────────────────────────┤
│  Database: tobin_maintenance                                         │
│                                                                       │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│  │ maintenance_requests │  │     vendors      │  │   landlords    ││
│  │──────────────────────│  │──────────────────│  │────────────────││
│  │ • id (auto)          │  │ • id             │  │ • id           ││
│  │ • request_id (REF)   │  │ • vendor_name    │  │ • name         ││
│  │ • tenant_name        │  │ • phone_number   │  │ • email        ││
│  │ • tenant_phone       │  │ • email          │  │ • phone        ││
│  │ • property_address   │  │ • specialty      │  │ • preferred_*  ││
│  │ • apartment_unit     │  │ • is_active      │  │                ││
│  │ • issue_description  │  │ • hourly_rate    │  │                ││
│  │ • category ────────────►│ • rating         │  │                ││
│  │ • urgency            │  │ • total_jobs     │  │                ││
│  │ • summary            │  └──────────────────┘  └────────────────┘│
│  │ • status             │                                            │
│  │ • assigned_vendor_id │  ┌──────────────────┐                    │
│  │ • created_at         │  │   properties     │                    │
│  │ • ...                │  │──────────────────│                    │
│  └──────────────────────┘  │ • id             │                    │
│                             │ • name           │                    │
│                             │ • address        │                    │
│                             │ • landlord_id ──────────────────┐    │
│                             └──────────────────┘               │    │
│                                                                │    │
└────────────────────────────────────────────────────────────────┼────┘
                                                                 │
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Twilio SMS     │  │   Email Service  │  │   OpenAI API     │  │
│  │──────────────────│  │──────────────────│  │──────────────────│  │
│  │ • Notify Vendor  │  │ • Landlord Email │  │ • AI Agent       │  │
│  │ • Notify Tenant  │  │ • Summary Report │  │ • Analyze Issue  │  │
│  │ • Status Updates │  │ • Status Updates │  │ • Find Vendor    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## 🔄 Request Flow Diagram

### Flow 1: Submit Maintenance Request

```
   TENANT                    n8n                    DATABASE            VENDOR
     │                        │                         │                 │
     │  1. Fill form          │                         │                 │
     │  "HVAC broken"         │                         │                 │
     ├───────────────────────>│                         │                 │
     │                        │                         │                 │
     │                        │  2. Insert request      │                 │
     │                        ├────────────────────────>│                 │
     │                        │  (get ID: 42)           │                 │
     │                        │<────────────────────────┤                 │
     │                        │                         │                 │
     │                        │  3. AI analyzes         │                 │
     │                        │  • Category: hvac       │                 │
     │                        │  • Urgency: High        │                 │
     │                        │  • Query vendors        │                 │
     │                        │                         │                 │
     │                        │  4. Find best vendor    │                 │
     │                        ├────────────────────────>│                 │
     │                        │  WHERE specialty='hvac' │                 │
     │                        │<────────────────────────┤                 │
     │                        │  (Joe's HVAC)           │                 │
     │                        │                         │                 │
     │                        │  5. Generate ref #      │                 │
     │                        │  TM-20231124-0042       │                 │
     │                        │                         │                 │
     │                        │  6. Update request      │                 │
     │                        ├────────────────────────>│                 │
     │                        │  with AI data & ref     │                 │
     │                        │                         │                 │
     │                        │  7. Send SMS            │                 │
     │                        ├────────────────────────────────────────>│
     │                        │  "HVAC issue at..."     │                 │
     │                        │                         │                 │
     │  8. Show success       │                         │                 │
     │  Ref: TM-20231124-0042 │                         │                 │
     │<───────────────────────┤                         │                 │
     │                        │                         │                 │
```

### Flow 2: Check Request Status

```
   TENANT                    n8n                    DATABASE
     │                        │                         │
     │  1. Enter ref #        │                         │
     │  TM-20231124-0042      │                         │
     ├───────────────────────>│                         │
     │                        │                         │
     │                        │  2. Query database      │
     │                        ├────────────────────────>│
     │                        │  WHERE request_id=...   │
     │                        │<────────────────────────┤
     │                        │  (found: urgency, etc)  │
     │                        │                         │
     │  3. Display details    │                         │
     │  • Status: Assigned    │                         │
     │  • Priority: High      │                         │
     │  • Category: HVAC      │                         │
     │  • Summary: ...        │                         │
     │<───────────────────────┤                         │
     │                        │                         │
```

## 🎯 Data Flow

### Reference Number Generation

```javascript
// Input
insertedData.id = 42;
now = "2023-11-24T15:30:00Z";

// Process
dateStr = "20231124";
paddedId = "0042";

// Output
request_id = "TM-20231124-0042";
```

### AI Agent Processing

```
Input: "It's too hot in unit 4B, please help"

AI Agent:
1. Analyzes urgency → "High"
2. Categorizes → "hvac"
3. Queries vendors → SELECT * FROM vendors WHERE specialty='hvac'
4. Returns best vendor → Joe's HVAC
5. Generates summary → "Tenant reports HVAC cooling issue..."

Output JSON:
{
  "urgency": "High",
  "category": "hvac",
  "summary": "Tenant reports HVAC cooling issue...",
  "vendor_id": 3,
  "vendor_name": "Joe's HVAC",
  "vendor_phone": "+15555550100"
}
```

## 🔐 Security Considerations

1. **Input Validation**: All form inputs sanitized
2. **SQL Injection Protection**: Parameterized queries
3. **Rate Limiting**: Prevent spam submissions
4. **Reference Number Privacy**: Not predictable (uses DB auto-increment)
5. **CORS**: Properly configured for cross-origin requests

## 📈 Scalability

### Current Capacity
- **Database**: PostgreSQL (thousands of requests/day)
- **n8n**: Single workflow (hundreds of executions/hour)
- **Frontend**: Static files (unlimited with CDN)

### Future Scaling
- **Database**: Add read replicas
- **n8n**: Horizontal scaling with queue
- **Frontend**: CDN deployment (Netlify/Vercel)
- **API**: Add caching layer (Redis)

## 🚀 Deployment Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    PRODUCTION                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Netlify CDN                Cloud PostgreSQL              │
│  ┌─────────────┐            ┌─────────────┐              │
│  │  Frontend   │            │  Database   │              │
│  │  (Static)   │            │  (Managed)  │              │
│  └─────────────┘            └─────────────┘              │
│         │                          │                       │
│         │                          │                       │
│         ↓                          ↓                       │
│  ┌─────────────────────────────────────┐                  │
│  │       n8n (Self-hosted / Cloud)      │                  │
│  │       • Webhook endpoints            │                  │
│  │       • AI processing                │                  │
│  │       • Database updates             │                  │
│  └─────────────────────────────────────┘                  │
│         │                                                   │
│         ↓                                                   │
│  ┌─────────────────────────────────────┐                  │
│  │       External Services              │                  │
│  │       • Twilio (SMS)                 │                  │
│  │       • SendGrid (Email)             │                  │
│  │       • OpenAI (AI Agent)            │                  │
│  └─────────────────────────────────────┘                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 📊 Tech Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | React + Vite | Maintenance form & status check |
| Landing | React + TypeScript | Marketing site |
| Workflow | n8n | Business logic automation |
| Database | PostgreSQL 15 | Data persistence |
| AI | OpenAI GPT-4 | Request analysis |
| SMS | Twilio | Vendor notifications |
| Email | SMTP/SendGrid | Landlord notifications |
| Hosting | Netlify | Static site deployment |

## 🎯 Next Implementation Phase

After completing the n8n updates, the next major features to implement are:

1. **Landlord Intelligence**
   - Match request to property
   - Query landlord's preferred vendors
   - Send landlord summary email

2. **Vendor Response Tracking**
   - Webhook for vendor replies
   - Update request status
   - Notify tenant of ETA

3. **Advanced Analytics**
   - Response time metrics
   - Vendor performance
   - Request trends

See the original user request for the advanced AI agent workflow details!

