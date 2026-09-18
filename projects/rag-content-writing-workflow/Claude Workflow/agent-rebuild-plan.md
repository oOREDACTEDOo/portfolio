# Content Automation — Claude Code Agent Rebuild Plan

**Started:** 2026-03-20
**Goal:** Rebuild the n8n RAG content system as a Claude Code sub-agent architecture. Produce better content, faster iteration, and direct MCP access to all data sources. Fully client-agnostic — works across any industry, any number of clients.

---

## Why We're Rebuilding

The n8n system was designed before Claude Code + MCPs existed. The current approach:
- n8n orchestrates everything, Claude is just one node among many
- Data fetching happens via HTTP Request nodes (brittle, verbose)
- Iterating on prompts requires editing n8n canvas nodes
- No sub-agent architecture — one big context window for everything

The new approach:
- Claude Code is the orchestrator
- Each pipeline stage is a sub-agent with its own context window
- Supabase, GSC, GA4, DataForSEO all connect via native MCP (no HTTP nodes)
- Prompts live in code files — easy to version, edit, and improve
- n8n becomes optional (trigger/scheduler only, if needed at all)

---

## Client-Agnostic Design Principle

The pipeline has zero hardcoded client or industry knowledge. Everything client-specific comes from the database or V2O input at run time:

| What | Source |
|---|---|
| Client identity, market, industry | `clients` table |
| Writing language, location code | `clients` table |
| Google Drive folder, Slack channel | `clients` table |
| Voice, tone, vocabulary | `voice_profiles` table |
| Audience persona, struggles, scepticism | `audience_profiles` table |
| Content structure, quality criteria, common mistakes | `content_types` table |
| SEO requirements, CTA guidance, proof elements | `content_types` table |
| Existing content for RAG | `content_chunks` table |
| Client-specific editorial overrides | V2O brief at run time |

**Content types are shared across clients.** A "Blog Post" type works for a shoe retailer, a manufacturer, or a staffing agency — the `quality_criteria` and `common_mistakes` fields in that record make it context-appropriate. Adding a new client requires no changes to the pipeline — only database rows.

**To run for any client:** provide `client_name` + `content_type_slug` + `topic` + `target_keywords`. That's it.

---

## MCP Connections Available

| MCP | Purpose in system |
|---|---|
| Supabase | Read client/voice/audience/chunks, write jobs + new chunks |
| n8n | Read/modify existing workflows, deploy updates |
| GSC | New content: near-ranking queries, cannibalism check. Update mode: full page performance audit |
| GA4 | New content: top performing content format signals. Update mode: traffic trend + engagement audit |
| DataForSEO | SERP data, keyword research (location pulled from clients table per client) |
| Google Workspace | Write output to Google Docs (folder ID from clients table per client) |
| Slack | Send completion notifications (channel ID from clients table per client) |

---

## Architecture: Sub-Agent Design

```
Orchestrator Agent
├── Context Loader        ← reads Supabase: client, voice, audience, content type
├── Research Agent        ← DataForSEO SERP + keyword intelligence + Tavily (parallel)
├── GSC Research Agent    ← near-ranking queries, cannibalism check (parallel)
├── RAG Agent             ← queries content_chunks via embedding (parallel)
├── Coverage Check        ← data quality gate before writing starts
├── Research Brief        ← synthesises all research into writer-ready brief
├── Outline Agent         ← section plan with word count targets
├── Draft Agent           ← first draft (Opus)
├── Critique Agent        ← quality review: universal + content type + voice
├── Gap Research Agent    ← targeted evidence search for flagged gaps
├── Rewrite Agent         ← final polished draft (Opus)
├── Deliverables Agent    ← SEO metadata + optimised image queries
├── Fact Check Agent      ← verifies claims, gates on UNVERIFIABLE
└── Output Agent          ← Google Docs + Supabase job save + Slack notification
```

Each sub-agent:
- Gets only the context it needs
- Has a focused, client-agnostic prompt
- Returns structured output to the orchestrator
- Has its own context window (no bloat accumulation)

**Improvements over n8n:**
- Deliverables agent added (was missing) — generates SEO metadata + image queries
- Fact check actually gates the pipeline (n8n: result saved but not checked)
- Coverage check is a hard stop on bad data (n8n: ran regardless)
- V2O injected into ALL agents, not just Research Brief
- Search intent gates content type selection
- DataForSEO keyword intelligence (volume, difficulty, intent, related) added — not in n8n
- GSC research branch added — not in n8n

---

## Quality Standards Architecture

Three layers — none of them hardcoded to a specific client:

1. **Universal standards** → `prompts/eeat-criteria.md`
   Specificity, evidence, no filler, originality, E-E-A-T, narrative craft, depth calibration. Applies to every piece regardless of client or topic.

2. **Content type criteria** → `content_types.quality_criteria` + `content_types.common_mistakes`
   What "good" looks like for this content format. Loaded per job. Shared across clients using the same type.

3. **Voice profile** → `voice_profiles.*`
   How to write, not what to write. Tone, vocabulary, sentence patterns, proof style. Per client.

V2O override always takes priority over all three layers.

---

## Onboarding a New Client

No pipeline changes required. Database only:

1. Add row to `clients` — brand_name, market, industry, website_url, gsc_property_id, ga4_property_id, currency, writing_language, language_code, dataforseo_location_code, google_drive_folder_id, slack_channel_id
2. Run content ingestion agent against their published URLs → populates `content_chunks` + generates `voice_profiles`
3. Add row to `audience_profiles` for this client
4. Confirm relevant `content_types` exist (or add new ones) — these are reusable across clients

Done. Run the pipeline with `client_name = "New Client"`.

---

## Build Phases

### Phase 1 — Understand existing system ✅ COMPLETE
- [x] Connect Supabase MCP — confirmed, all 9 tables visible
- [x] Connect n8n MCP — confirmed, both workflows accessible (via 1Password)
- [x] Install Superpowers plugin — v5.0.5, user scope
- [x] Read Content Ingestion workflow (12 nodes) — fully mapped
- [x] Read New Content Generation workflow (29 nodes) — extracted to reference/workflow-2-extracted.md
- [x] Document full prompt content from each Claude node in Workflow 2

---

### Phase 2 — Build Content Generation Agent ✅ COMPLETE
**Goal: produce one great piece of content end-to-end.**

All 15 agent instruction files written and reviewed. All 4 shared prompt files written.
Pipeline is fully client-agnostic — no hardcoded client, industry, or market assumptions.

#### Agents built (agents/ folder)

| File | Role | Model |
|---|---|---|
| orchestrator.md | Master controller, 12 stages (incl. Stage 1.5 keyword gate), error handling | — |
| context-loader.md | Supabase lookup: client, voice, audience, content type | — |
| research.md | DataForSEO SERP + keyword intelligence + WebSearch (Tavily when configured) | Sonnet |
| gsc-research.md | Near-ranking queries, cannibalism check | Sonnet |
| rag.md | Embedding → match_content_chunks → filtered chunks | — |
| coverage-check.md | Data quality gate, internal linking targets | Sonnet |
| research-brief.md | Synthesise all research into writer-ready brief | Sonnet |
| outline.md | Section plan with calibrated word count targets | Sonnet |
| draft.md | Full first draft | **Opus** |
| critique.md | Universal + content type + voice quality review | Sonnet |
| gap-research.md | Targeted evidence search for flagged gaps | Sonnet |
| rewrite.md | Final polished draft with all fixes applied | **Opus** |
| deliverables.md | SEO metadata + 5 optimised Shutterstock image queries | Sonnet |
| fact-check.md | Claim verification — UNVERIFIABLE gates pipeline | Sonnet |
| output.md | Google Docs + Supabase content_jobs + Slack | — |

#### Shared prompts (prompts/ folder)

| File | Contents |
|---|---|
| eeat-criteria.md | Universal quality standards + critique scoring rubric |
| seo-aeo-standards.md | SEO/AEO standards: titles, meta, headings, BLUF, scannability, entity density, schema, AEO answer blocks ← NEW |
| system-base.md | Shared preamble template (V2O block, client context, writing language) |
| voice-injection.md | How voice_profiles data flows into agents |

#### Key design decisions made
- **RAG threshold: 0.5** (matches n8n baseline; post-retrieval filter trims weak matches)
- **Word count calibration: ×1.15 below target** (Claude overshoots ~15%)
- **Opus for Draft + Rewrite only** — Sonnet for all research/analysis stages
- **Shutterstock queries** come from Deliverables agent (optimised), not raw image placeholders
- **Citation rule**: external sources hyperlinked on first mention only; never fabricate URLs
- **Image placement**: exactly 5 placeholders — featured image + first 4 H2 sections
- **V2O quotes**: blockquote format, placed after the point they support, no editorial framing

#### Clients table — new columns ✅ ADDED (2026-03-20)
Migration applied. All 3 client rows populated with `writing_language`, `language_code`, `dataforseo_location_code`. The `google_drive_folder_id` and `slack_channel_id` columns exist but are null — Output agent falls back to Drive folder search and `#content-automation` respectively.
- `writing_language` TEXT — "Australian English" for all current clients
- `language_code` TEXT — "en" for all current clients
- `dataforseo_location_code` INTEGER — 2036 (Australia) for all current clients
- `google_drive_folder_id` TEXT — null (fallback: search Drive for folder named after brand_name)
- `slack_channel_id` TEXT — null (fallback: #content-automation)

---

### Phase 3 — Test & Iterate ✅ CORE PIPELINE VALIDATED
- [x] Add new columns to `clients` table (migration applied 2026-03-20)
- [x] Populate all 3 client rows — writing_language, language_code, dataforseo_location_code, google_drive_folder_id set. slack_channel_id null (pipeline fallback handles this)
- [x] **Test #1** — Client K / so-blog-post — COMPLETE. Doc: https://docs.google.com/document/d/1yHEuhF8tTRSUoKGuUR2iRVMl8NjR7pSMVR0wUI4IRsY/edit. Job: 450d6403
- [x] **Test #2** — Client D / im-article / "Investing After 60" — COMPLETE. Client-agnostic design validated. Doc: https://docs.google.com/document/d/1dhO6gLJuKDRztMGIrnHzCh_nRQfnrLcNC89BaJjkNK4/edit. Job: 17b768e8
- [x] **Test #3** — Client K / so-blog-post / "Building Hybrid Tech Teams" — COMPLETE. Keyword pivot workflow validated. Doc: https://docs.google.com/document/d/1I8K031qV-Fz4nnx4Wz8IwcmufivpWL8sjr8OVkE-j_8/edit. Job: b55f84ff
- [x] Post-test audit completed — gaps identified and fixed (see Pipeline Fixes Applied below)
- [ ] Run fourth test with all fixes in place — full pipeline including Critique → Gap Research → Rewrite loop
- [ ] Compare output quality before/after critique loop
- [ ] Slack delivery: pending app approval by workspace admin (app ID: A0ANM1CM708)

#### Pipeline Fixes Applied (post-test-3 audit, 2026-03-20)

| Fix | File changed | Detail |
|---|---|---|
| Tavily → WebSearch | `research.md` | Tavily not configured. WebSearch replaces it (3 searches instead of 2). `tavilyData` → `webResearch` throughout. Note added for future Tavily setup. |
| Keyword validation gate | `orchestrator.md` | New Stage 1.5 — triggers on volume=0 or intent mismatch. Runs DataForSEO, presents options table, **hard stops for user authorization** before continuing. |
| Critique loop mandatory | `orchestrator.md` | Stages 6-8 (Critique → Gap Research → Rewrite) now explicitly marked as always-run. Previously skipped during testing. |
| Coverage check STOP adjusted | `coverage-check.md` | Zero-volume STOP now has carve-out: if Stage 1.5 already authorized a keyword pivot, the check uses the replacement keywords. |
| `tavilyData` references cleaned | `research-brief.md`, `fact-check.md`, `coverage-check.md`, `orchestrator.md` | All renamed to `webResearch`. Reference file (`workflow-2-extracted.md`) left unchanged — n8n reference only. |

#### What was NOT used in tests (gaps identified)
- **Tavily**: not configured — now replaced with WebSearch in spec
- **GSC**: called in prior session but not freshly in test #3 — must call every run
- **DataForSEO Branches 2a/2b/2c**: in the spec, but not followed in orchestrator execution — execution discipline issue, not a file issue
- **Critique → Gap Research → Rewrite loop**: skipped in all 3 tests — now marked mandatory
- **Fact Check**: inline only — formal agent not dispatched in any test

---

### Phase 4 — Content Ingestion Agent 🔲 PENDING
**Goal: ingest new client content into Supabase knowledge base.**

Replaces Workflow 1. Steps:
1. Accept list of URLs (or sitemap)
2. Fetch + clean HTML (rate-limited, batched)
3. Delete existing chunks for URL (deduplication)
4. Extract clean editorial content (skip product/fund listing blocks)
5. Chunk + tag (~400 words per chunk, full tag schema)
6. Generate embeddings via OpenAI (text-embedding-3-small — keep consistent with existing chunks)
7. Store in content_chunks with all metadata
8. Generate voice_profile from ingested content

Key improvement over n8n: no loop stall risk, better error handling, can scrape Notion/Slack/Google Docs too.

---

### Phase 5 — Content Update Agent 🔲 PENDING
**Goal: improve existing pages based on GSC data + EEAT assessment.**

Stage 0 (update-mode only) — Performance Audit sub-agent:

**GSC MCP pulls:**
- All queries the page ranks for (impressions, clicks, CTR, avg position)
- Position 6–20 queries with decent impressions — "nearly there" opportunities
- Declining keywords (position dropping month-over-month)
- CTR outliers — high impressions, low CTR (title/meta opportunity)

**GA4 MCP pulls:**
- Traffic trend for the page (last 90 days vs prior period)
- Engagement metrics (session duration, bounce rate, scroll depth if available)

**EEAT assessment:**
- Score existing content against universal quality standards
- Identify specific weaknesses

All stored in `eeat_assessments` + `gsc_page_data` tables, then injected as update context into the standard pipeline.

---

## Key Decisions

| Decision | Status | Notes |
|---|---|---|
| Does n8n stay? | Undecided | Keep as trigger/scheduler option; Claude Code is now execution layer |
| Embedding model | Keeping OpenAI text-embedding-3-small | Consistency with 1,631 existing chunks |
| Input interface | CLI for now | Slack command or form trigger later |
| Output storage | Google Docs + Supabase job | Both retained |
| Config storage | Database only | No per-client JSON config files needed — everything in clients table |

---

## Files in This Folder

```
Claude Workflow/
├── CLAUDE.md                        project config — Claude reads this first
├── agent-rebuild-plan.md            this file
├── agents/
│   ├── orchestrator.md              master controller (11 stages)
│   ├── context-loader.md            Supabase: client, voice, audience, content type
│   ├── research.md                  DataForSEO SERP + keyword intelligence + WebSearch (Tavily when configured)
│   ├── gsc-research.md              GSC: near-ranking queries, cannibalism check
│   ├── rag.md                       RAG: embedding → match_content_chunks
│   ├── coverage-check.md            data quality gate before writing starts
│   ├── research-brief.md            synthesise all research into structured brief
│   ├── outline.md                   section plan with word count targets
│   ├── draft.md                     first draft (Opus)
│   ├── critique.md                  quality review: universal + content type + voice
│   ├── gap-research.md              targeted evidence search for flagged gaps
│   ├── rewrite.md                   final polished draft (Opus)
│   ├── deliverables.md              SEO metadata + optimised image queries ← NEW
│   ├── fact-check.md                claim verification — gates on UNVERIFIABLE
│   ├── output.md                    Google Docs + Supabase + Slack
│   └── performance-audit.md         [Phase 5] GSC + GA4 audit for update mode
├── prompts/
│   ├── system-base.md               shared preamble (V2O block, writing language)
│   ├── voice-injection.md           voice profile injection template
│   └── eeat-criteria.md             universal quality standards + critique rubric
├── scripts/
│   ├── generate-embeddings.js       OpenAI embedding calls
│   └── utils/
│       └── supabase-client.js       shared Supabase connection
├── outputs/
│   ├── drafts/                      generated content (gitignored)
│   └── logs/                        run logs (gitignored)
└── reference/
    ├── workflow-2-extracted.md       full n8n workflow 2 extraction (29 nodes)
    └── n8n-lessons-learned.md        known gotchas from n8n build
```

---

## Reference: Existing n8n Workflows

| Workflow | n8n ID | Nodes | Status |
|---|---|---|---|
| New Content Generation | `73lMIBHKbWIWwuNP` | 29 | Active — reference only |
| Client Onboarding - Content Ingestion | `QIChmeBWedU5OYbh` | 12 | Active — reference only |
