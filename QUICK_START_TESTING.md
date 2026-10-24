# 🚀 Quick Start Testing Guide

## ⚡ Fast Track - Test Everything in 5 Minutes

### Step 1: Start All Services (2 minutes)

Open 4 terminal windows:

```bash
# Terminal 1 - PostgreSQL
brew services start postgresql@15

# Terminal 2 - Frontend (Maintenance Form)
cd /path/to/TobinAI/frontend
npm run dev
# ✅ Should open at http://localhost:5173

# Terminal 3 - Landing Page
cd /path/to/TobinAI/landing_page/TobinPropertyAssistant
npm run dev
# ✅ Should open at http://localhost:5555

# Terminal 4 - n8n
docker ps -a | grep n8n
# Find your container name, then:
docker start [your-container-name]
# ✅ Access at http://localhost:5678
```

### Step 2: Update n8n (5 minutes)

Before testing, you need to update your n8n workflow. Follow **N8N_UPDATES_GUIDE.md** for detailed instructions.

**Quick version:**

1. Open n8n: `http://localhost:5678`
2. Open your maintenance request workflow
3. Update the "Code in JavaScript1" node with the new reference number generator
4. Add a "Respond to Webhook" node at the end
5. Activate the workflow
6. (Optional) Create the "Check Status" webhook workflow

### Step 3: Test Submit Request (1 minute)

**From Landing Page:**
1. Go to `http://localhost:5555`
2. Click **"Submit Request"** button (top right navigation)
3. New tab opens with maintenance form

**Fill the form:**
- **Tenant Name**: John Doe
- **Phone Number**: 555-0100
- **Property Address**: 123 Main Street
- **Apartment Unit**: 4B
- **Issue Description**: "No heat in apartment, it's freezing!"

**Click Submit**

**✅ Expected Result:**
```
✅ Request submitted successfully!

Reference Number:
┌──────────────────┐
│ TM-20231124-0001 │
└──────────────────┘
Save this number to check your request status
```

### Step 4: Check n8n Execution (30 seconds)

1. Go to `http://localhost:5678`
2. Click **Executions** tab
3. Should see your workflow just ran
4. Click on it to see the flow
5. Check each node to verify data

**✅ Verify:**
- Webhook received form data
- Database inserted request (got ID)
- AI Agent analyzed issue
- Code node generated reference number
- Database updated with AI data
- SMS sent (if Twilio configured)

### Step 5: Verify Database (30 seconds)

```bash
psql tobin_maintenance -c "
SELECT 
  request_id,
  tenant_name,
  urgency,
  category,
  summary,
  status
FROM maintenance_requests
ORDER BY id DESC
LIMIT 1;
"
```

**✅ Expected Output:**
```
    request_id     | tenant_name | urgency | category |         summary          | status  
-------------------+-------------+---------+----------+--------------------------+---------
 TM-20231124-0001  | John Doe    | High    | hvac     | Tenant reports heating...|  pending
```

### Step 6: Test Status Check (1 minute)

**Option A: From the form**
1. On the maintenance form, scroll down
2. Click **"🔍 Check Request Status"** link
3. Or directly go to: `http://localhost:5173/check-status`

**Option B: Direct URL**
1. Go to `http://localhost:5173/check-status`

**Enter reference number:**
- Paste: `TM-20231124-0001`
- Click **"Check Status"**

**✅ Expected Result:**
```
Request Details
────────────────────────────────
Reference: TM-20231124-0001
Status: [Pending Review]
Priority: High
Category: HVAC
Summary: Tenant reports heating issue...
Submitted: Nov 24, 2023, 3:45 PM
Property: 123 Main Street, unit 4B
```

### Step 7: Test Admin Dashboard (30 seconds)

1. Go to `http://localhost:5555/admin`
2. Should see the new request in the list
3. Verify all fields are populated correctly

**✅ Verify:**
- Request appears in "Maintenance Requests" tab
- Shows correct urgency (High)
- Shows correct category (HVAC)
- Summary is populated (not "Not Analyzed")
- Can click "Edit" to modify

---

## 🧪 Test Scenarios

### Scenario 1: Emergency Request

**Issue**: "Gas leak in apartment!"

**Expected**:
- ✅ Urgency: Emergency
- ✅ Category: plumbing or general
- ✅ Immediate priority routing
- ✅ SMS sent to vendor instantly

### Scenario 2: Low Priority Request

**Issue**: "Light bulb needs replacing in bathroom"

**Expected**:
- ✅ Urgency: Low
- ✅ Category: electrical or general
- ✅ Normal processing

### Scenario 3: HVAC Issue

**Issue**: "Air conditioner not cooling, very hot"

**Expected**:
- ✅ Urgency: High
- ✅ Category: hvac
- ✅ AI queries hvac vendors
- ✅ Assigns best hvac vendor

### Scenario 4: Plumbing Issue

**Issue**: "Toilet overflowing, water everywhere"

**Expected**:
- ✅ Urgency: Emergency
- ✅ Category: plumbing
- ✅ AI queries plumbing vendors
- ✅ Immediate notification

---

## 🐛 Troubleshooting

### Problem: Form submits but no reference number

**Solution:**
- Check n8n execution logs
- Verify "Respond to Webhook" node exists
- Check browser console for errors

### Problem: Status check returns "Not found"

**Solution:**
```bash
# Check if data is in database
psql tobin_maintenance -c "SELECT request_id FROM maintenance_requests ORDER BY id DESC LIMIT 5;"

# Verify reference number format matches
# Should be: TM-YYYYMMDD-####
```

### Problem: AI analysis missing (all requests show "Not Analyzed")

**Solution:**
- Check n8n "Update rows in a table" node
- Verify it's matching on correct ID
- Should use: `{{ $('Insert rows in a table1').first().json.id }}`

### Problem: Vendor not assigned

**Solution:**
```bash
# Check if vendors exist
psql tobin_maintenance -c "SELECT * FROM vendors WHERE is_active = true;"

# If empty, add sample vendors:
psql tobin_maintenance -c "
INSERT INTO vendors (vendor_name, phone_number, email, specialty, is_active, is_primary, hourly_rate, rating)
VALUES 
  ('Joe''s HVAC', '+15555550100', 'joe@hvac.com', 'hvac', true, true, 75.00, 4.8),
  ('Quick Plumbing', '+12065551234', 'quick@plumbing.com', 'plumbing', true, true, 80.00, 4.9),
  ('Bright Electric', '+12065555678', 'bright@electric.com', 'electrical', true, true, 85.00, 4.7);
"
```

### Problem: Frontend shows CORS error

**Solution:**
- Check n8n webhook settings
- Ensure "OPTIONS" method allowed
- Verify webhook is active

### Problem: Services not starting

**Solution:**
```bash
# Check ports
lsof -i :5173  # Frontend should be here
lsof -i :5555  # Landing page should be here
lsof -i :5678  # n8n should be here

# Kill if needed
kill -9 [PID]

# Restart
npm run dev
```

---

## ✅ Success Checklist

After testing, verify:

- [ ] Can submit maintenance request from landing page
- [ ] Receive reference number after submission
- [ ] Reference number has format `TM-YYYYMMDD-####`
- [ ] Can check status using reference number
- [ ] Status check shows all request details
- [ ] Admin dashboard shows new requests
- [ ] AI analysis is working (urgency populated)
- [ ] Vendors are being assigned
- [ ] Database is being updated correctly
- [ ] n8n workflow executes without errors

---

## 📊 Sample Test Data

Use these to test different scenarios:

### Test Case 1: HVAC Emergency
```
Tenant Name: Sarah Johnson
Phone: 555-123-4567
Property: 123 Main Street
Unit: Apt 4B
Issue: "Heater completely broken, no heat for 2 days in winter"
Expected: Urgency=Emergency, Category=hvac
```

### Test Case 2: Plumbing Routine
```
Tenant Name: Mike Chen
Phone: 555-987-6543
Property: 456 Oak Avenue
Unit: Unit 12C
Issue: "Slow drain in kitchen sink"
Expected: Urgency=Low/Medium, Category=plumbing
```

### Test Case 3: Electrical Urgent
```
Tenant Name: Emily Rodriguez
Phone: 555-456-7890
Property: 789 Elm Street
Unit: Suite 3A
Issue: "Sparking outlet in bedroom, smell of burning"
Expected: Urgency=High/Emergency, Category=electrical
```

### Test Case 4: General Maintenance
```
Tenant Name: David Kim
Phone: 555-111-2222
Property: 321 Pine Road
Unit: #7D
Issue: "Door handle is loose and wobbly"
Expected: Urgency=Low, Category=general
```

---

## 🎯 What Success Looks Like

After completing all tests, you should have:

1. **3+ maintenance requests** in the database
2. **All requests have reference numbers** (`TM-YYYYMMDD-####`)
3. **AI analysis completed** (urgency, category, summary populated)
4. **Vendors assigned** where applicable
5. **Status check working** for all reference numbers
6. **Admin dashboard** showing all requests with proper data

---

## 📞 Need Help?

If tests fail:
1. Check `IMPLEMENTATION_SUMMARY.md` for overview
2. Review `N8N_UPDATES_GUIDE.md` for n8n setup
3. See `SYSTEM_ARCHITECTURE.md` for data flow
4. Check n8n execution logs
5. Query database directly
6. Review browser console errors

---

## 🚀 Ready for Production?

Once all tests pass:
1. Update webhook URLs to production
2. Deploy frontend to Netlify
3. Deploy landing page
4. Set up monitoring
5. Test end-to-end in production
6. 🎉 Launch!

**Estimated Testing Time: 10-15 minutes**
**Estimated Production Deployment: 1-2 hours**

