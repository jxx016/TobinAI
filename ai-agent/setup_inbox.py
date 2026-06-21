"""Run once to create the Tobin AgentMail inbox and get the inbox_id."""
import os
from dotenv import load_dotenv
from agentmail import AgentMail

load_dotenv()

client = AgentMail(api_key=os.getenv("AGENTMAIL_API_KEY"))
inbox = client.inboxes.create(username="tobin", client_id="tobin-ai-main")

print(f"\n✅ Inbox created!")
print(f"   Email:    {inbox.inbox_id}@agentmail.to")
print(f"   Inbox ID: {inbox.inbox_id}")
print(f"\nAdd this to your ai-agent/.env:")
print(f"   AGENTMAIL_INBOX_ID={inbox.inbox_id}")
