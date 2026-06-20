# n8n Waitlist Email Capture Setup Guide

This guide will help you set up an n8n workflow to capture waitlist signups and send confirmation emails.

## Overview

The workflow will:
1. Receive waitlist signups from your landing page
2. Save the lead to Google Sheets (or your preferred storage)
3. Send a confirmation email to the user
4. Optionally notify you via Slack/Discord

---

## Step 1: Create the Webhook

1. Open n8n and create a new workflow
2. Add a **Webhook** node
3. Configure it:
   - **HTTP Method**: POST
   - **Path**: `waitlist-signup`
4. Click "Listen for test event" to get your webhook URL
5. Your URL will look like: `http://localhost:5678/webhook/waitlist-signup`

> **For Production**: Use your n8n cloud URL or deployed instance URL

---

## Step 2: Add Google Sheets (Store Leads)

1. Add a **Google Sheets** node after the Webhook
2. Connect your Google account
3. Configure:
   - **Operation**: Append Row
   - **Document**: Create a new spreadsheet called "Tobin AI Waitlist"
   - **Sheet**: Sheet1
   - **Columns to Match On**: Leave empty
   
4. Map the fields:
   ```
   Name         → {{ $json.name }}
   Email        → {{ $json.email }}
   Properties   → {{ $json.property_count }}
   Source       → {{ $json.source }}
   Signed Up    → {{ $json.timestamp }}
   ```

### Google Sheet Setup

Create a Google Sheet with these columns:
| Name | Email | Properties | Source | Signed Up |
|------|-------|------------|--------|-----------|

---

## Step 3: Send Confirmation Email

### Option A: Using Gmail

1. Add a **Gmail** node
2. Connect your Gmail account
3. Configure:
   - **Operation**: Send
   - **To**: `{{ $json.email }}`
   - **Subject**: `Welcome to the Tobin AI Waitlist! 🎉`
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
    .benefits { background: rgba(0, 212, 255, 0.1); border-radius: 12px; padding: 20px; margin: 24px 0; }
    .benefits li { color: #e2e8f0; margin-bottom: 8px; }
    .footer { text-align: center; margin-top: 30px; color: #64748b; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">🤖 Tobin AI</div>
    </div>
    <div class="card">
      <h1>You're on the list, {{ $json.name }}!</h1>
      <p>Thank you for joining the Tobin AI waitlist. You're now among the first to experience the future of AI-powered property management.</p>
      
      <div class="benefits">
        <p style="color: #00d4ff; font-weight: 600; margin-bottom: 12px;">As an early adopter, you'll get:</p>
        <ul>
          <li>🚀 Priority access when we launch</li>
          <li>💰 Exclusive founding member pricing</li>
          <li>🎯 Direct input on features we build</li>
          <li>🎁 Special bonuses for early supporters</li>
        </ul>
      </div>
      
      <p>We're working hard to bring you an AI assistant that will transform how you manage properties. Expect updates soon!</p>
      
      <p style="margin-top: 24px;">
        Cheers,<br>
        <span class="highlight">The Tobin AI Team</span>
      </p>
    </div>
    <div class="footer">
      <p>© 2024 Tobin AI. All rights reserved.</p>
      <p>You're receiving this because you signed up at tobinai.com</p>
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
     "subject": "Welcome to the Tobin AI Waitlist! 🎉",
     "html": "<your HTML here>"
   }
   ```

---

## Step 4: Notify Yourself (Optional)

### Slack Notification

1. Add a **Slack** node
2. Connect your Slack workspace
3. Configure:
   - **Channel**: #waitlist (or your preferred channel)
   - **Message**:
   ```
   🎉 New Waitlist Signup!
   
   Name: {{ $json.name }}
   Email: {{ $json.email }}
   Properties: {{ $json.property_count }}
   Time: {{ $json.timestamp }}
   ```

### Discord Notification

1. Add **HTTP Request** node
2. Configure:
   - **URL**: Your Discord webhook URL
   - **Method**: POST
   - **Body**:
   ```json
   {
     "content": "🎉 **New Waitlist Signup!**\n\n**Name:** {{ $json.name }}\n**Email:** {{ $json.email }}\n**Properties:** {{ $json.property_count }}"
   }
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
     "message": "Successfully added to waitlist"
   }
   ```

---

## Complete Workflow Structure

```
[Webhook] → [Google Sheets] → [Gmail] → [Slack (optional)] → [Respond to Webhook]
```

---

## Step 6: Update Frontend URL

Once your n8n workflow is ready:

1. Get your production webhook URL from n8n
2. Update `waitlist.tsx`:

```typescript
// Change this line at the top of the file:
const N8N_WAITLIST_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/waitlist-signup";
```

---

## Testing

1. Activate your n8n workflow
2. Go to your waitlist page: `http://localhost:3000/waitlist`
3. Fill out the form and submit
4. Check:
   - ✅ Google Sheet has new row
   - ✅ Confirmation email received
   - ✅ Slack/Discord notification (if set up)

---

## Production Checklist

- [ ] Deploy n8n to cloud (n8n.cloud or self-hosted)
- [ ] Update webhook URL in frontend to production URL
- [ ] Set up proper email domain (for better deliverability)
- [ ] Test the complete flow
- [ ] Deploy frontend to Netlify

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

