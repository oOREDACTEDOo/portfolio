# Webprofits Content Agent System

Automated multi-client SEO content production using Claude Code sub-agents, Supabase RAG, and native MCPs.

## What This Does
Generates publication-ready content by loading client context (voice, audience, content type) from Supabase, running web research, querying the RAG knowledge base, then running a multi-stage writing pipeline (outline → draft → critique → rewrite → fact-check). Output goes to Google Docs + Slack.

## Folder Map
- `agents/` — sub-agent instruction files (start here when something goes wrong)
- `prompts/` — shared prompt blocks reused across agents (EEAT rubric, voice template)
- `scripts/` — JavaScript utilities (embeddings, API calls, formatters)
- `config/clients/` — one JSON file per client (IDs, content types, settings)
- `outputs/drafts/` — locally saved drafts (not committed)
- `outputs/logs/` — pipeline run logs (not committed)
- `reference/` — read-only reference material (n8n extractions, lessons learned)

## How to Run
Start by telling Claude: "Run the content generation pipeline" and provide:
- Client name (e.g. Client D, Client K)
- Content type slug (e.g. asset_class_page, so-blog-post)
- Target keywords
- Topic
- V2O brief (optional — paste transcript or client notes)

The orchestrator agent handles the rest.

## Adding a New Client
1. Add client row to Supabase `clients` table
2. Run content ingestion agent against their published URLs
3. Add `config/clients/[client-name].json` with their GSC and GA4 property IDs
4. Done — the pipeline picks them up automatically

## When Something Goes Wrong
1. Check `outputs/logs/` for the last run log
2. Find the agent that failed in `agents/`
3. Read its instruction file — the problem is usually in the prompt or the data shape
4. Check `reference/n8n-lessons-learned.md` for known gotchas

## MCPs Required
- Supabase (project: REDACTED_PROJECT)
- DataForSEO
- GSC
- Google Workspace
- Slack
