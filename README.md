# Jan Manns: automation portfolio

Working examples of AI automation and agentic workflows, built at Webprofits (an AI-native marketing agency) and independently. Client names have been replaced with generic labels (Client A, Client B, and so on) throughout. The systems and results are real; the client identities have been withheld for confidentiality.

## What these are built with

n8n, Claude Code, Supabase, and GitHub form the core stack, with a set of custom MCP servers connecting Claude directly to Google Docs, Google Sheets, Search Console, Google Analytics, and DataForSEO, plus other platform APIs per project. Each report or system in this repo names its specific stack in more detail.

## `projects/`: working code and systems

| Folder | What it is |
|---|---|
| [`rag-content-writing-workflow/`](https://github.com/oOREDACTEDOo/portfolio/tree/master/projects/rag-content-writing-workflow) | A multi-agent, multi-stage RAG content production system: Supabase + pgvector for per-client voice and knowledge base, n8n for orchestration, an 8-stage Claude pipeline with a dedicated critique step. Built and tested on real client content. Full write-up in that folder. |
| [`aeo-audit-system/`](https://github.com/oOREDACTEDOo/portfolio/tree/master/projects/aeo-audit-system) | A standalone Python tool auditing how visible a brand is across ChatGPT, Gemini, and Perplexity, plus Reddit sentiment and Wikipedia/Knowledge Graph presence. Scrapers and API layer are working; the analysis/scoring layer is the remaining piece. |
| [`client-dashboard/`](https://github.com/oOREDACTEDOo/portfolio/tree/master/projects/client-dashboard) and [`client-time-manager/`](https://github.com/oOREDACTEDOo/portfolio/tree/master/projects/client-time-manager) | Two iterations of an Express + TypeScript dashboard aggregating Google Calendar, Notion, Fathom, and site-ranking data per client, with a Claude assistant layer that can extract action items straight from a meeting transcript into a task in Notion. |
| [`SMS-LEAD-QUALIFIER-CASE-STUDY.md`](./SMS-LEAD-QUALIFIER-CASE-STUDY.md) | An SMS lead-qualification agent: inbound message triggers an AI qualification step, extracts intent and urgency, logs the lead to Supabase, and sends a tailored reply. Works end to end and has been run with real Claude, Supabase, and Twilio calls; it is not live on a public webhook right now because of an n8n Cloud platform bug, not a gap in the build. |
| [`mcp-fathom-video/`](https://github.com/oOREDACTEDOo/portfolio/tree/master/projects/mcp-fathom-video) | A small MCP server built from scratch (Node.js), exposing five tools over the Fathom meeting-recording API. |
| [`mcp-gsc/`](https://github.com/oOREDACTEDOo/portfolio/tree/master/projects/mcp-gsc) | A third-party, open-source MCP server for Google Search Console, included to show real experience wiring MCP into a workflow, not claimed as original work. |
| [`enterprise-seo-proposal/`](https://github.com/oOREDACTEDOo/portfolio/tree/master/projects/enterprise-seo-proposal) | An SEO agency proposal/RFP response, included as a writing sample rather than an automation example. |

## `reports/`: output examples

Real client deliverables, each produced by a repeatable workflow rather than written by hand: multi-channel performance reporting, technical SEO and schema audits, AI-visibility/AEO auditing (testing how often a brand gets cited by ChatGPT, Gemini, and Perplexity against its competitors), CRO audits, competitor and traffic-drop analysis, and content briefs.

Each report is password-protected (real encryption, not a cosmetic gate). Password provided separately.

**Click through from here, not from the GitHub file browser.** GitHub shows `.html` files as source code when you browse the repo directly; these links go to the live rendered version instead:

| Report | Link |
|---|---|
| CRO audit dashboard | [open](https://ooredactedoo.github.io/portfolio/reports/client-d-cro-audit-dashboard.html) |
| LLM visibility & AEO performance report | [open](https://ooredactedoo.github.io/portfolio/reports/client-b-llm-visibility-aeo-performance-report.html) |
| Answer Engine Optimisation: full methodology | [open](https://ooredactedoo.github.io/portfolio/reports/aeo-outline-expansion.html) |
| Client A: FY27 unified strategy and forecast | [open](https://ooredactedoo.github.io/portfolio/reports/client-a-unified-strategy-forecast.html) |
| Client A: schema audit | [open](https://ooredactedoo.github.io/portfolio/reports/client-a-schema-audit.html) |
| Client A: page speed audit | [open](https://ooredactedoo.github.io/portfolio/reports/client-a-page-speed-audit.html) |
| Client A: suburb page plan (Burwood VIC) | [open](https://ooredactedoo.github.io/portfolio/reports/client-a-suburb-page-plan-burwood.html) |
| Client C: structured data (schema) audit | [open](https://ooredactedoo.github.io/portfolio/reports/client-c-schema-audit.html) |
| Client C: mobile nav recommendations | [open](https://ooredactedoo.github.io/portfolio/reports/client-c-mobile-nav-recommendations.html) |
| Client D: competitor SEO audit | [open](https://ooredactedoo.github.io/portfolio/reports/client-d-competitor-seo-audit.html) |
| Client D: paid media report | [open](https://ooredactedoo.github.io/portfolio/reports/client-d-paid-media-report.html) |
| Client D: organic traffic drop analysis | [open](https://ooredactedoo.github.io/portfolio/reports/client-d-traffic-drop-analysis.html) |
| Client E: keyword & page mapping | [open](https://ooredactedoo.github.io/portfolio/reports/client-e-keyword-page-mapping.html) |
| Client F: AEO visibility report | [open](https://ooredactedoo.github.io/portfolio/reports/client-f-aeo-visibility-report.html) |
| Client G: content brief | [open](https://ooredactedoo.github.io/portfolio/reports/client-g-content-brief.html) |
| Client H: SEO strategy proposal | [open](https://ooredactedoo.github.io/portfolio/reports/client-h-seo-strategy.html) |
| Claude Code training guide (internal) | [open](https://ooredactedoo.github.io/portfolio/reports/claude-code-training.html) |
