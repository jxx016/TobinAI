# n8n Workflow Updates Guide

## ✅ Completed Frontend Changes
- ✅ Created `CheckStatusForm.jsx` - Status checking page
- ✅ Updated `MaintenanceRequestForm.jsx` - Shows reference number after submission
- ✅ Added routing in `App.jsx` - Supports `/check-status` path
- ✅ Updated landing page CTA button - Links to maintenance form
- ✅ Updated navigation - "Submit Request" button

## 🔧 n8n Workflow Updates Needed

### 1. Update Code Node - Generate Clean Reference Numbers

Replace your existing Code node (after AI Agent) with this updated version:

```javascript
// Get the AI analysis from previous node
const aiOutput = $input.first().json;

// Get the original webhook data
const webhookData = $('Webhook').first().json.body;

// Get the database ID from the Insert node
const insertedData = $('Insert rows in a table1').first().json;
const databaseId = insertedData.id;

// Generate a clean reference number: TM-20231124-0001
const now = new Date();
const dateStr = now.toISOString().split('T')[0].replace(/-/g, ''); // 20231124
const requestId = `TM-${dateStr}-${String(databaseId).padStart(4, '0')}`; // TM-20231124-0001

// Parse the AI output
let parsedAI;
if (typeof aiOutput.output === 'string') {
  let cleanOutput = aiOutput.output.trim();
  // Remove markdown code blocks if present
  if (cleanOutput.startsWith('```')) {
    cleanOutput = cleanOutput.split('\n').slice(1, -1).join('\n');
  }
  parsedAI = JSON.parse(cleanOutput);
} else {
  parsedAI = aiOutput;
}

// Return combined data with clean reference number
return {
  json: {
    id: databaseId,
    request_id: requestId,  // ✨ Clean reference number!
    urgency: parsedAI.urgency || 'medium',
    category: parsedAI.category || 'general',
    summary: parsedAI.summary || webhookData.issue_description,
    handyman_notes: parsedAI.handyman_notes || parsedAI.summary,
    requires_photos: parsedAI.requires_photos || false,
    estimated_time: parsedAI.estimated_time || '1-2hrs',
    
    // Original form data
    tenant_name: webhookData.tenant_name || 'Unknown',
    tenant_phone: webhookData.tenant_phone || '',
    property_address: parsedAI.property_address || webhookData.property_address || '',
    apartment_unit: webhookData.apartment_unit || '',
    issue_description: webhookData.issue_description || '',
    
    // Metadata
    date_created: new Date().toISOString(),
    status: 'pending',
    
    // Landlord info (make dynamic later)
    landlord_email: 'your-email@example.com',
    landlord_name: 'Test Landlord'
  }
};
```

### 2. Add "Respond to Webhook" Node

After your main webhook flow, add a "Respond to Webhook" node to return the reference number:

**Settings:**
- **Response Code**: 200
- **Response Body**: Expression mode

```json
{
  "success": true,
  "message": "Maintenance request submitted successfully",
  "reference_number": "{{ $('Code in JavaScript1').first().json.request_id }}"
}
```

### 3. Create New Webhook - Check Status

Create a **separate workflow** or add to existing:

#### Node 1: Webhook (Check Status)
- **Method**: GET
- **Path**: `check-status`
- **Respond**: Using 'Respond to Webhook' Node

#### Node 2: Postgres Query
- **Operation**: Execute Query
- **Query**:

```sql
SELECT 
  request_id,
  status,
  urgency,
  category,
  summary,
  created_at,
  tenant_name,
  property_address,
  apartment_unit
FROM maintenance_requests
WHERE request_id = '{{ $json.query.ref }}'
LIMIT 1;
```

#### Node 3: IF Node (Check if found)
- **Condition**: `{{ $json.request_id }}` exists
- **If true**: Go to "Respond Found"
- **If false**: Go to "Respond Not Found"

#### Node 4a: Respond to Webhook (Found)
- **Response Code**: 200
- **Response Body**:

```json
{
  "found": true,
  "reference": "{{ $json.request_id }}",
  "status": "{{ $json.status }}",
  "urgency": "{{ $json.urgency }}",
  "category": "{{ $json.category }}",
  "summary": "{{ $json.summary }}",
  "submitted": "{{ $json.created_at }}",
  "tenant": "{{ $json.tenant_name }}",
  "property": "{{ $json.property_address }}",
  "unit": "{{ $json.apartment_unit }}"
}
```

#### Node 4b: Respond to Webhook (Not Found)
- **Response Code**: 404
- **Response Body**:

```json
{
  "found": false,
  "error": "Request not found"
}
```

## 🎯 Testing the Setup

### 1. Test Maintenance Form
1. Go to `http://localhost:5173`
2. Fill out the form
3. Submit
4. You should see a reference number like `TM-20231124-0001`

### 2. Test Status Check
1. Copy the reference number
2. Click "Check Request Status" link
3. Enter the reference number
4. Should display full request details

### 3. Test Landing Page Links
1. Go to `http://localhost:5555` (or your landing page port)
2. Click "Submit Request" in navigation
3. Should open maintenance form in new tab

## 📊 Reference Number Format

**Format**: `TM-YYYYMMDD-####`

Examples:
- `TM-20231124-0001` - First request on Nov 24, 2023
- `TM-20231124-0042` - 42nd request on Nov 24, 2023
- `TM-20231201-0001` - First request on Dec 1, 2023

**Benefits:**
- ✅ Easy to read and share
- ✅ Sortable by date
- ✅ Unique identifier
- ✅ Professional appearance

## 🚀 Next Steps

1. Update your n8n Code node with the new reference number generator
2. Add "Respond to Webhook" node to your main workflow
3. Create the "Check Status" webhook workflow
4. Test both forms
5. Deploy to production!

## 🔗 URLs Summary

| Service | Local URL | Purpose |
|---------|-----------|---------|
| Maintenance Form | `http://localhost:5173` | Submit requests |
| Status Check | `http://localhost:5173/check-status` | Check status |
| Landing Page | `http://localhost:5555` | Marketing site |
| Admin Dashboard | `http://localhost:5555/admin` | Manage data |
| n8n | `http://localhost:5678` | Workflow editor |

## 📝 Notes

- The frontend will show a temporary reference number (`TM-YYYYMMDD-PENDING`) if n8n doesn't return one
- Make sure to activate both webhooks in n8n
- Test the database query with sample reference numbers first
- Update URLs for production deployment

