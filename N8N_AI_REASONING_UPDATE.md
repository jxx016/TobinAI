# n8n AI Reasoning - Implementation Guide

## Update Your n8n Code Node

Replace your existing Code node with this updated version that captures AI reasoning:

```javascript
// Get the AI analysis from previous node
const aiOutput = $input.first().json;

// Get the original webhook data
const webhookData = $('Webhook').first().json.body;

// Get the database ID from the Insert node
const insertedData = $('Insert rows in a table1').first().json;
const databaseId = insertedData.id;

// Generate a clean reference number
const now = new Date();
const dateStr = now.toISOString().split('T')[0].replace(/-/g, '');
const requestId = `TM-${dateStr}-${String(databaseId).padStart(4, '0')}`;

// Parse the AI output
let parsedAI;
let aiReasoningSteps = [];

// Track reasoning steps
aiReasoningSteps.push("📝 Received maintenance request");
aiReasoningSteps.push(`🏠 Property: ${webhookData.property_address}`);
aiReasoningSteps.push(`📍 Unit: ${webhookData.apartment_unit}`);

if (typeof aiOutput.output === 'string') {
  aiReasoningSteps.push("🤖 Parsing AI analysis...");
  
  let cleanOutput = aiOutput.output.trim();
  if (cleanOutput.startsWith('```')) {
    cleanOutput = cleanOutput.split('\n').slice(1, -1).join('\n');
  }
  parsedAI = JSON.parse(cleanOutput);
} else {
  parsedAI = aiOutput;
}

// Log AI decisions
aiReasoningSteps.push(`⚡ Classified as: ${parsedAI.category || 'general'}`);
aiReasoningSteps.push(`🚨 Urgency level: ${parsedAI.urgency || 'medium'}`);
aiReasoningSteps.push(`⏱️ Estimated time: ${parsedAI.estimated_time || '1-2hrs'}`);

// Check if vendor was found
if (parsedAI.vendor_name) {
  aiReasoningSteps.push(`🔍 Found vendor: ${parsedAI.vendor_name}`);
  aiReasoningSteps.push(`📞 Contact: ${parsedAI.vendor_phone}`);
} else {
  aiReasoningSteps.push("⚠️ No vendor found, using defaults");
}

aiReasoningSteps.push("✅ Work order created successfully");

// Return combined data with AI reasoning
return {
  json: {
    id: databaseId,
    request_id: requestId,
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
    
    // AI Reasoning Steps (NEW!)
    ai_reasoning: aiReasoningSteps,
    
    // Landlord info
    landlord_email: 'your-email@example.com',
    landlord_name: 'Test Landlord'
  }
};
```

## Add Respond to Webhook Node

After your Code node, add a "Respond to Webhook" node with this configuration:

**Response Body (Expression mode):**

```json
{
  "success": true,
  "reference_number": "={{ $json.request_id }}",
  "ai_reasoning": "={{ $json.ai_reasoning }}",
  "urgency": "={{ $json.urgency }}",
  "category": "={{ $json.category }}",
  "estimated_time": "={{ $json.estimated_time }}"
}
```

This will send back:
- The real reference number
- The AI's reasoning steps
- Key analysis results

## Result

Your frontend will now receive real AI reasoning like:
- 📝 Received maintenance request
- 🏠 Property: 980 Jefferson Commons Circle
- 📍 Unit: #2402D
- 🤖 Parsing AI analysis...
- ⚡ Classified as: hvac
- 🚨 Urgency level: High
- ⏱️ Estimated time: 1-2hrs
- 🔍 Found vendor: Joe's HVAC
- 📞 Contact: +12064893667
- ✅ Work order created successfully

