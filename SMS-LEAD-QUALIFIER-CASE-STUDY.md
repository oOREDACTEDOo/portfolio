# SMS lead qualifier, built for this application

Not something pulled from the Webprofits workspace. I built this on the day I applied, because working examples make a stronger case than a cover letter on its own.

## What it does

Inbound SMS triggers an AI qualification step that extracts intent and urgency from the message, logs the lead to a database, and sends a tailored reply back to the sender.

- **n8n** as the orchestration layer (webhook trigger → qualification → database write → reply)
- **Claude Haiku** does the qualification: reads the inbound message, extracts structured lead data (intent, urgency, key details), drafts a reply
- **Supabase** stores the lead (row-level security enabled, service-role key only, since this holds real phone numbers and message content)
- **Twilio** sends the reply

## What's actually proven

Ran the full pipeline end to end with real services, not mocked: a real inbound message, a real Claude qualification call, a real row written to Supabase, and a real reply sent and received over Twilio. The logic works.

## What's not live, and why

The production webhook trigger hits a genuine platform bug on n8n Cloud: every production webhook returns "not registered" despite showing as active. I reproduced it across three separate workflows, including a brand-new minimal one built through the normal UI (which rules out anything specific to how I'd built the first one), and tried four different fixes: republishing via the API, toggling publish/unpublish in the editor, the dashboard-level toggle, and a fresh webhook node on a new path. None of it changed the result. It matches several open GitHub issues describing the same "tenant-level routing desync." I also ruled out a plan/billing cause by upgrading mid-troubleshooting, which made no difference.

Filed a detailed support ticket with the full reproduction steps. n8n's support team confirmed the standard causes don't apply and escalated it to an engineer.

As a fallback I started standing up a self-hosted n8n instance locally to get a live version working regardless of the Cloud bug.

## Why this is in here anyway

This is what fixing a real platform bug looks like in practice: reproduce it cleanly, rule out your own mistakes first, gather enough evidence that support can't wave it off, and have a fallback path ready while you wait. Happy to walk through the n8n workflow, the qualification prompt, or the bug report itself in more detail.
