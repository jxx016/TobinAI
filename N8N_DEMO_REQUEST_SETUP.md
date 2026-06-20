# n8n Demo Request / Interest Form Setup Guide

This guide will help you set up an n8n workflow to capture demo requests and send confirmation emails.

## Overview

The workflow will:
1. Receive demo requests from your landing page
2. Save the lead to Google Sheets (or your preferred storage)
3. Send a confirmation email to the user
4. Optionally notify you via Slack/Discord so you can follow up

---

## Step 1: Create the Webhook

1. Open n8n and create a new workflow
2. Add a **Webhook** node
3. Configure it:
   - **HTTP Method**: POST
   - **Path**: `demo-request`
4. Click "Listen for test event" to get your webhook URL
5. Your URL will look like: `http://localhost:5678/webhook/demo-request`

> **For Production**: Use your n8n cloud URL or deployed instance URL

---

## Step 2: Add Google Sheets (Store Leads)

1. Add a **Google Sheets** node after the Webhook
2. Connect your Google account
3. Configure:
   - **Operation**: Append Row
   - **Document**: Create a new spreadsheet called "Tobin AI Demo Requests"
   - **Sheet**: Sheet1
   - **Columns to Match On**: Leave empty
   
4. Map the fields:
   ```
   Name            → {{ $json.name }}
   Email           → {{ $json.email }}
   Phone           → {{ $json.phone }}
   Properties      → {{ $json.property_count }}
   Message         → {{ $json.message }}
   Source          → {{ $json.source }}
   Submitted At    → {{ $json.timestamp }}
   Status          → Pending
   ```

### Google Sheet Setup

Create a Google Sheet with these columns:
| Name | Email | Phone | Properties | Message | Source | Submitted At | Status |
|------|-------|-------|------------|---------|--------|--------------|--------|

---

## Step 3: Send Confirmation Email

### Option A: Using Gmail

1. Add a **Gmail** node
2. Connect your Gmail account
3. Configure:
   - **Operation**: Send
   - **To**: `{{ $json.email }}`
   - **Subject**: `Thanks for Your Interest in Tobin AI! 🤖`
   - **Email Type**: HTML
   - **Message** (paste the HTML below):

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #0a0a0a; color: #ffffff; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
    .header { text-align: center; margin-bottom: 30px; }
    .logo { font-size: 28px; font-weight: bold; color: #00d4ff; }
    .card { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 16px; padding: 32px; border: 1px solid rgba(0, 212, 255, 0.2); }
    h1 { color: #00d4ff; margin: 0 0 16px 0; font-size: 24px; }
    p { color: #94a3b8; line-height: 1.6; margin: 0 0 16px 0; }
    .highlight { color: #00d4ff; font-weight: 600; }
    .next-steps { background: rgba(0, 212, 255, 0.1); border-radius: 12px; padding: 20px; margin: 24px 0; }
    .next-steps li { color: #e2e8f0; margin-bottom: 8px; }
    .footer { text-align: center; margin-top: 30px; color: #64748b; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">🤖 Tobin AI</div>
    </div>
    <div class="card">
      <h1>Thanks for your interest, {{ $json.name }}!</h1>
      <p>We've received your demo request and are excited to show you how Tobin AI can transform your property management.</p>
      
      <div class="next-steps">
        <p style="color: #00d4ff; font-weight: 600; margin-bottom: 12px;">What happens next:</p>
        <ul>
          <li>📞 We'll reach out within 24 hours to schedule your demo</li>
          <li>🎯 Get a personalized walkthrough tailored to your needs</li>
          <li>❓ Have all your questions answered by our team</li>
          <li>🚀 See exactly how Tobin AI can help your {{ $json.property_count }} properties</li>
        </ul>
      </div>
      
      <p>In the meantime, feel free to explore our website or reach out if you have any immediate questions.</p>
      
      <p style="margin-top: 24px;">
        Looking forward to speaking with you,<br>
        <span class="highlight">The Tobin AI Team</span>
      </p>
    </div>
    <div class="footer">
      <p>© 2024 Tobin AI. All rights reserved.</p>
      <p>You're receiving this because you requested a demo at tobinai.com</p>
    </div>
  </div>
</body>
</html>
```

### Option B: Using SendGrid / Resend / Other

If you prefer a transactional email service:

1. Add **HTTP Request** node
2. Configure for your email provider's API
3. Example for Resend:
   ```
   URL: https://api.resend.com/emails
   Method: POST
   Headers: 
     Authorization: Bearer YOUR_API_KEY
     Content-Type: application/json
   Body:
   {
     "from": "Tobin AI <hello@tobinai.com>",
     "to": "{{ $json.email }}",
     "subject": "Thanks for Your Interest in Tobin AI! 🤖",
     "html": "<your HTML here>"
   }
   ```

---

## Step 4: Notify Yourself (IMPORTANT for Follow-up!)

### Slack Notification

1. Add a **Slack** node
2. Connect your Slack workspace
3. Configure:
   - **Channel**: #demo-requests (or your preferred channel)
   - **Message**:
   ```
   🎯 *New Demo Request!*
   
   *Name:* {{ $json.name }}
   *Email:* {{ $json.email }}
   *Phone:* {{ $json.phone || 'Not provided' }}
   *Properties:* {{ $json.property_count }}
   *Challenges:* {{ $json.message || 'Not specified' }}
   *Time:* {{ $json.timestamp }}
   
   👉 Follow up within 24 hours!
   ```

### Discord Notification

1. Add **HTTP Request** node
2. Configure:
   - **URL**: Your Discord webhook URL
   - **Method**: POST
   - **Body**:
   ```json
   {
     "content": "🎯 **New Demo Request!**\n\n**Name:** {{ $json.name }}\n**Email:** {{ $json.email }}\n**Phone:** {{ $json.phone || 'Not provided' }}\n**Properties:** {{ $json.property_count }}\n**Challenges:** {{ $json.message || 'Not specified' }}\n\n👉 Follow up within 24 hours!"
   }
   ```

### Email Notification to Yourself

1. Add another **Gmail** node
2. Configure:
   - **To**: your-email@example.com
   - **Subject**: `🎯 New Demo Request: {{ $json.name }} ({{ $json.property_count }} properties)`
   - **Message**:
   ```
   New demo request received!
   
   Name: {{ $json.name }}
   Email: {{ $json.email }}
   Phone: {{ $json.phone || 'Not provided' }}
   Properties: {{ $json.property_count }}
   
   Their Challenges:
   {{ $json.message || 'Not specified' }}
   
   Submitted: {{ $json.timestamp }}
   
   ---
   Follow up within 24 hours to schedule the demo!
   ```

---

## Step 5: Respond to Webhook

1. Add a **Respond to Webhook** node at the end
2. Configure:
   - **Response Code**: 200
   - **Response Body**:
   ```json
   {
     "success": true,
     "message": "Demo request received. We'll be in touch within 24 hours!"
   }
   ```

---

## Complete Workflow Structure

```
[Webhook] → [Google Sheets] → [Gmail to User] → [Gmail to You / Slack] → [Respond to Webhook]
```

---

## Step 6: Update Frontend URL (for Production)

Once your n8n workflow is ready:

1. Get your production webhook URL from n8n
2. Update `waitlist.tsx`:

```typescript
// Change this line at the top of the file:
const N8N_INTEREST_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/demo-request";
```

---

## Testing

1. Activate your n8n workflow
2. Go to your demo request page: `http://localhost:3000/waitlist`
3. Fill out the form and submit
4. Check:
   - ✅ Google Sheet has new row
   - ✅ Confirmation email received by user
   - ✅ You received notification (Slack/Discord/Email)

---

## Production Checklist

- [ ] Deploy n8n to cloud (n8n.cloud or self-hosted)
- [ ] Update webhook URL in frontend to production URL
- [ ] Set up proper email domain (for better deliverability)
- [ ] Set up Slack/Discord notifications for quick follow-up
- [ ] Test the complete flow
- [ ] Deploy frontend to Netlify

---

## Follow-up Best Practices

1. **Respond within 24 hours** - The sooner you follow up, the higher the conversion
2. **Personalize your outreach** - Reference their property count and challenges
3. **Offer flexible scheduling** - Provide a Calendly link or multiple time options
4. **Prepare a demo script** - Have a consistent demo flow ready

---

## Troubleshooting

### Webhook not receiving data
- Make sure n8n workflow is **active**
- Check browser console for CORS errors
- Verify the webhook URL is correct

### Emails going to spam
- Set up SPF/DKIM records for your domain
- Use a transactional email service (SendGrid, Resend, Postmark)

### Google Sheets not updating
- Check Google Sheets permissions
- Verify column names match exactly

---

## Need Help?

If you run into issues, check:
1. n8n execution logs (click on the workflow run)
2. Browser developer console (F12 → Console)
3. Network tab for API responses

