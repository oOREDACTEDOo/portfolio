# RAG Content Production System — Full Plan

## Context

This document outlines a complete system for automated, high-quality content production across multiple clients at Webprofits. It replaces the concept of training custom AI models with a more scalable approach: RAG (Retrieval-Augmented Generation) combined with a multi-stage content pipeline, orchestrated through n8n and powered by Supabase + Claude.

This plan incorporates insights from the Jan/Jay planning session (Feb 19, 2026), subsequent research into the best architecture for multi-client, multi-content-type generation, and analysis of SEOwind's agent-based content workflow architecture.

**Dual-mode system:** The pipeline handles both **new content creation** and **existing content updates**. Update mode adds an EEAT assessment and GSC performance data front-end before entering the shared generation pipeline.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Why RAG Instead of Custom Model Training](#why-rag-instead-of-custom-model-training)
3. [Architecture Diagram](#architecture-diagram)
4. [Supabase Database Design](#supabase-database-design)
5. [RAG: How It Works](#rag-how-it-works)
6. [Content Type Routing](#content-type-routing)
7. [N8N Workflows](#n8n-workflows)
8. [Multi-Stage Content Pipeline](#multi-stage-content-pipeline)
9. [Quality Enhancement Techniques](#quality-enhancement-techniques)
10. [Scaling to New Clients](#scaling-to-new-clients)
11. [Cost Estimates](#cost-estimates)
12. [Decisions Needed Before Building](#decisions-needed-before-building)
13. [Build Timeline](#build-timeline)

---

## 1. System Overview

The system has three main components:

1. **Supabase** — Stores all client data, voice profiles, content type templates, RAG knowledge base (chunked content with vector embeddings), and job tracking
2. **n8n** — Orchestrates all workflows: client onboarding/ingestion, content generation pipeline, and the feedback loop
3. **Claude API** — Powers the multi-stage content generation pipeline (research, outline, draft, critique, rewrite, polish)

Supporting services:
- **OpenAI Embeddings API** — Converts text chunks into vectors for RAG search (cheap, commodity tool)
- **Web Search API** (Tavily or Brave) — Provides current external data, stats, and competitor analysis
- **Google Search Console API** — Provides real performance data per page (rankings, impressions, CTR, keyword positions) for content update decisions
- **Google Drive** — Output destination for finished articles
- **Slack** — Notifications and optional human checkpoints

### What the system does:

**New content mode:**
- You fill out a form: select a client, content type, and target keyword(s)
- The system automatically pulls that client's brand data, voice profile, and relevant existing content from RAG
- It researches the topic via web search and analyses what's already ranking
- It generates content through a multi-stage pipeline that includes self-critique, gap research, and rewriting
- It outputs a finished article to Google Docs and logs the job
- After publishing, the article gets ingested back into RAG, growing the knowledge base

**Update content mode:**
- You provide the URL of the existing page to update, plus the target keyword(s)
- The system scrapes the current page and runs an EEAT assessment (strengths, weaknesses, gaps)
- It pulls GSC performance data for that page (current rankings, impressions, CTR, declining keywords)
- The EEAT gaps and GSC data inform the research and rewriting stages — the system knows exactly what needs improving
- The same multi-stage pipeline runs, but with targeted improvements rather than writing from scratch

---

## 2. Why RAG Instead of Custom Model Training

Jay's original recommendation was to train custom AI models per content type (e.g., a model trained on hundreds of service page examples). This is the right instinct — the AI needs deep knowledge of how to produce each content type well. But the implementation is better served by RAG + structured templates for the following reasons:

| Factor | Custom Model Training | RAG + Templates |
|---|---|---|
| Availability | Claude doesn't offer fine-tuning. OpenAI does but with limitations | Works with any LLM, including Claude |
| Multi-client | Separate model per client voice = expensive, hard to maintain | One model, per-client data stored in Supabase |
| Updatability | Retrain the model every time something changes | Edit a row in Supabase |
| Content types | Separate model per type = 5-10+ models to manage | One pipeline, different templates pulled dynamically |
| Cost | Training costs + per-model hosting | Only API usage costs per generation |
| Quality | ~90-95% with fine-tuning | ~85-95% with RAG + multi-stage pipeline + strong prompts |
| Time to build | Weeks of data preparation + training per model | Days to set up, iterative refinement |

The key insight: what makes content good isn't baked into model weights — it's in the **process** (research, outlining, critique, rewriting) and the **inputs** (client voice, content structure rules, real data). Both of those are better handled by RAG and pipeline design than by model training.

---

## 3. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                          FRONT END                                │
│                                                                   │
│   NEW:    Select Client → Content Type → Keyword → Generate       │
│   UPDATE: Select Client → Paste URL → Keyword → Update            │
│   (Client selection auto-pulls brand data from Supabase)          │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                        N8N WORKFLOWS                              │
│                                                                   │
│   Workflow 1: Client Onboarding (ingest content into RAG)         │
│   Workflow 2: Content Generation — NEW (multi-stage pipeline)     │
│   Workflow 3: Content Update — UPDATE (EEAT + GSC → pipeline)     │
│   Workflow 4: Feedback Loop (re-ingest published content)         │
└──────────────────────────┬───────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                  ▼
┌──────────────────┐ ┌──────────┐ ┌─────────────────────┐
│    SUPABASE       │ │  CLAUDE  │ │   EXTERNAL APIS      │
│                   │ │   API    │ │                      │
│ - Clients table   │ │          │ │ - Web Search         │
│ - Voice profiles  │ │ Multi-   │ │   (Tavily/Brave)     │
│ - Content types   │ │ stage    │ │ - Google Search       │
│ - RAG chunks      │ │ pipeline │ │   Console API        │
│   (pgvector)      │ │          │ │ - OpenAI Embeddings  │
│ - EEAT assess.    │ │          │ │ - Page scraping      │
│ - GSC page data   │ │          │ │   (for updates)      │
│ - Job tracking    │ │          │ │                      │
└──────────────────┘ └──────────┘ └─────────────────────┘
```

---

## 4. Supabase Database Design

Supabase handles everything: client data, content intelligence, RAG storage, and job tracking. It supports pgvector natively, so the vector database and relational data live in one place.

### Table: clients

This table already exists in the current Supabase setup. Fields to ensure are present:

| Field | Type | Purpose | Example |
|---|---|---|---|
| id | uuid | Primary key | auto-generated |
| brand_name | text | Client display name | "Client A" |
| business_type | text | Lead gen or eCommerce | "lead_generation" |
| industry | text | Client's industry/vertical | "property management" |
| market | text | Geographic market | "AU" |
| currency | text | Currency for any pricing references | "AUD" |
| website_url | text | Primary website | "https://clienta.example.com" |
| target_audience_summary | text | Brief audience description | "Property managers, 50-500 units" |
| ga4_property_id | text | For future analytics integration | "G-XXXXXXX" |
| ga4_conversion_events | jsonb | Key conversion events | ["form_submit", "phone_click"] |
| key_facts | text | Short factual summary of client differentiators, certifications, key stats — injected conditionally into Draft + Rewrite prompts where relevant | "ISO 27001 certified. Average staff tenure ~5 years." |
| created_at | timestamp | Record creation | auto |

### Table: voice_profiles

Generated automatically by Claude during client onboarding. One row per client.

| Field | Type | Purpose | Example |
|---|---|---|---|
| id | uuid | Primary key | auto-generated |
| client_id | uuid | FK to clients | links to Client A |
| sentence_patterns | text | How they construct sentences | "Short opening statements. Average 14 words. Uses rhetorical questions as transitions." |
| vocabulary_preferences | text | Words they use and avoid | "Uses 'property managers' not 'landlords'. Never uses 'leverage' or 'utilize'. Prefers 'straightforward' over 'simple'." |
| structure_patterns | text | How they organize content | "Opens with a scenario or pain point, never a definition. Uses H2s as questions. Ends sections with one-line takeaways." |
| tone_description | text | Overall feel | "Professional but conversational. Confident without being salesy. Occasionally uses dry humor." |
| opening_style | text | How they start pieces | "Always opens with a specific scenario the reader recognizes. Never starts with 'In today's...' or broad statements." |
| closing_style | text | How they end pieces | "Ends with a direct challenge or question to the reader. CTA feels like a natural next step, not a pitch." |
| proof_style | text | How they support claims | "Always cites specific numbers. Prefers own case study data over third-party stats. Uses 'we found that...' framing." |
| sample_passages | text | 3-5 representative passages | Direct quotes from their best content |
| generated_at | timestamp | When profile was created | auto |
| last_updated | timestamp | Last refresh | auto |

This profile is generated by feeding 10-20 of the client's best articles into Claude with a detailed analysis prompt. It should be regenerated every 6-12 months or when the client's voice evolves.

### Table: content_types

Defines the structure, rules, and examples for each type of content the agency produces. This is where the "trained model" concept gets replaced — instead of training a model on service page examples, you define what makes a great service page here.

| Field | Type | Purpose |
|---|---|---|
| id | uuid | Primary key |
| type_name | text | Human-readable name |
| type_slug | text | Machine-readable identifier |
| business_context | text | When this type is used (lead gen, ecom, both) |
| purpose | text | What this content is meant to achieve |
| audience_mindset | text | What the reader is thinking/feeling when they land on this |
| structure_template | text | Required sections and their order |
| seo_requirements | text | SEO-specific rules for this content type |
| proof_elements | text | What kinds of evidence/social proof to include |
| cta_guidance | text | What the CTA should look like |
| internal_linking_rules | text | How to handle internal links |
| quality_criteria | text | What "good" looks like for this type |
| common_mistakes | text | What to avoid |
| example_references | jsonb | URLs or stored examples of excellent versions |
| word_count_range | text | Target length range |
| primary_intent | text | Search intent this serves |

**This table needs to be thoroughly populated per content type. Each content type should be its own deeply considered entry. See Section 6 for the full breakdown of each type.**

### Table: audience_profiles

Detailed audience definitions per client. A client may have multiple audiences (e.g., an ecom brand targeting both consumers and wholesale buyers).

| Field | Type | Purpose | Example |
|---|---|---|---|
| id | uuid | Primary key | auto-generated |
| client_id | uuid | FK to clients | links to Client A |
| audience_name | text | Identifier | "Property Managers" |
| role_or_persona | text | Who they are | "VP Operations or property manager at mid-market firm" |
| already_knows | text | What they don't need explained | "Basic property management. Familiar with competitor tools." |
| struggling_with | text | Their pain points | "Getting owner buy-in. Proving ROI. Managing multiple properties with small teams." |
| skeptical_of | text | What turns them off | "Vague 'AI-powered' claims. Enterprise case studies irrelevant to their scale." |
| responds_to | text | What resonates | "Specific numbers. Stories from similar-sized companies. Tactical advice." |
| reading_level | text | Target readability | "Grade 9-10. Professional but not academic." |
| content_preferences | text | Format preferences | "Prefers scannable content. Wants actionable takeaways." |

### Table: content_chunks (RAG Knowledge Base)

This is the core RAG table. Stores chunked, tagged, contextualized content with vector embeddings for semantic search. Uses Supabase's pgvector extension.

| Field | Type | Purpose | Example |
|---|---|---|---|
| id | uuid | Primary key | auto-generated |
| client_id | uuid | FK to clients | links to Client A |
| chunk_text | text | The actual content chunk (~400 words) | "We reduced onboarding time from 14 days to 3 by..." |
| context_prefix | text | One-line summary prepended for retrieval clarity | "In an article about streamlining property manager onboarding, the author discusses results:" |
| source_article_title | text | Original article this came from | "How We Cut Onboarding Time by 80%" |
| source_url | text | URL if available | "https://clienta.example.com/blog/..." |
| source_date | date | When the original was published | 2025-03-15 |
| chunk_position | int | Position within the original article | 3 (of 5) |
| topic_tags | text[] | Broad themes | ["onboarding", "time-to-value", "product-led growth"] |
| keyword_tags | text[] | What someone would search | ["reduce onboarding time", "SaaS onboarding"] |
| content_type_tag | text | What kind of content this came from | "case_study" |
| intent_tag | text | What the content is doing | "proving results with data" |
| asset_tags | text[] | Useful elements contained | ["statistic", "before-after comparison", "process description"] |
| funnel_stage | text | Where this sits in the buyer journey | "bottom" |
| embedding | vector(1536) | Vector representation for similarity search | [0.023, -0.841, 0.119, ...] |
| created_at | timestamp | When ingested | auto |

**Key design decisions:**
- context_prefix is generated by Claude during ingestion — it gives each chunk self-contained meaning so retrieval quality is high
- Tags are generated by Claude during ingestion — they power the coverage analysis that determines generation strategy
- embedding uses OpenAI's text-embedding-3-small (1536 dimensions) — stored via pgvector
- chunk_position allows retrieving neighboring chunks for additional context when needed

### Table: content_jobs

Tracks every content generation request and its output. Replaces Notion for content task tracking.

| Field | Type | Purpose | Example |
|---|---|---|---|
| id | uuid | Primary key | auto-generated |
| client_id | uuid | FK to clients | links to Client A |
| content_type | text | FK slug to content_types | "service_page_leadgen" |
| target_keywords | text[] | Keywords to target | ["property management software", "PM tools"] |
| topic | text | Human description of the topic | "Property management software for mid-market" |
| mode | text | "new" or "update" | "update" |
| source_url | text | URL of existing page (update mode only) | "https://clienta.example.com/guide/..." |
| status | text | Current state | "generating" / "ready_for_review" / "approved" / "published" |
| coverage_level | text | RAG coverage assessment | "strong" / "partial" / "none" |
| outline | text | Generated outline (for review) | Full outline text |
| final_output | text | The finished article | Full article text |
| output_url | text | Link to Google Doc | "https://docs.google.com/..." |
| research_brief | text | Research stage output | Stored for reference |
| critique | text | Critique stage output | Stored for reference |
| model_used | text | Which Claude model | "claude-sonnet-4-6" |
| total_tokens | int | Total tokens consumed | 45000 |
| estimated_cost | decimal | Estimated API cost | 0.85 |
| created_at | timestamp | When requested | auto |
| completed_at | timestamp | When generation finished | auto |
| published_at | timestamp | When published (triggers re-ingestion) | manual update |

### Table: published_content_map

Tracks what's live on each client's website for internal linking awareness and content ecosystem management.

| Field | Type | Purpose | Example |
|---|---|---|---|
| id | uuid | Primary key | auto-generated |
| client_id | uuid | FK to clients | links to Client A |
| page_title | text | Title of the published page | "Property Management Software Guide" |
| page_url | text | Live URL | "https://clienta.example.com/guide/..." |
| content_type | text | What type of page | "blog_post" |
| primary_keyword | text | Main keyword targeted | "property management software" |
| topic_tags | text[] | What topics it covers | ["property management", "software", "comparison"] |
| publish_date | date | When it went live | 2025-06-01 |
| is_cornerstone | boolean | Is this a key/pillar page | true |

This table enables the pipeline to:
- Suggest internal links to existing content during generation
- Avoid producing content that duplicates what's already published
- Understand the client's content ecosystem when choosing angles

### Table: eeat_assessments

Stores EEAT (Experience, Expertise, Authoritativeness, Trustworthiness) assessments for existing content being updated. Generated by Claude during the update pipeline's assessment stage.

| Field | Type | Purpose | Example |
|---|---|---|---|
| id | uuid | Primary key | auto-generated |
| job_id | uuid | FK to content_jobs | links to the update job |
| client_id | uuid | FK to clients | links to Client A |
| page_url | text | URL of the assessed page | "https://clienta.example.com/guide/..." |
| scraped_content | text | Full text of current page | Stored for reference |
| overall_score | text | Summary EEAT rating | "weak" / "moderate" / "strong" |
| experience_assessment | text | Does the content demonstrate real experience? | "No first-hand examples or case studies. Generic advice only." |
| expertise_assessment | text | Does the content show subject expertise? | "Covers basics but lacks depth on technical aspects. Missing comparison framework." |
| authority_assessment | text | Are claims supported by authoritative sources? | "Only 1 named source. No regulatory references. No industry data." |
| trust_assessment | text | Is the content balanced, accurate, transparent? | "Overly positive — risks section is thin. No dates on statistics." |
| strengths | text[] | What's working well | ["Clear structure", "Good FAQ section", "Proper H2 hierarchy"] |
| weaknesses | text[] | What needs improvement | ["No data sources cited", "Thin risk coverage", "Missing comparison table"] |
| gaps | text[] | What's completely missing | ["Tax section", "SMSF considerations", "How to evaluate products"] |
| actionable_suggestions | text[] | Specific improvements to make | ["Add 3+ named data sources", "Expand risks to match benefits depth"] |
| priority_actions | text[] | Ordered list of highest-impact changes | ["Add comparison table", "Cite industry reports", "Add tax section"] |
| assessed_at | timestamp | When assessment was run | auto |

### Table: gsc_page_data

Stores Google Search Console performance data per page. Pulled via GSC API during the update pipeline to inform what's working, what's declining, and where opportunities exist.

| Field | Type | Purpose | Example |
|---|---|---|---|
| id | uuid | Primary key | auto-generated |
| client_id | uuid | FK to clients | links to Client D |
| page_url | text | The page URL | "https://clientd.example.com/investments/private-credit" |
| date_range_start | date | Start of data period | 2025-11-01 |
| date_range_end | date | End of data period | 2026-02-01 |
| total_clicks | int | Total clicks in period | 1,240 |
| total_impressions | int | Total impressions in period | 45,000 |
| average_ctr | decimal | Average click-through rate | 0.028 |
| average_position | decimal | Average search position | 14.3 |
| top_queries | jsonb | Keywords driving traffic with metrics | [{"query": "private credit Australia", "clicks": 320, "impressions": 8000, "position": 6.2}] |
| declining_queries | jsonb | Keywords losing position over period | [{"query": "private credit funds", "position_change": +4.5, "clicks_change": -40%}] |
| opportunity_queries | jsonb | High-impression, low-CTR keywords | [{"query": "private credit vs bonds", "impressions": 2000, "ctr": 0.005, "position": 18}] |
| fetched_at | timestamp | When GSC data was pulled | auto |

This table enables the update pipeline to:
- Understand what keywords the page already ranks for (don't lose these)
- Identify declining keywords that need strengthening
- Spot opportunity keywords with high impressions but low CTR/position
- Make data-driven decisions about what to improve vs. leave alone

---

## 5. RAG: How It Works

RAG (Retrieval-Augmented Generation) means the AI **looks up relevant information before writing** instead of relying on its training data alone.

### The Process:

**During ingestion (one-time per article):**
1. An article gets split into ~400 word chunks at paragraph boundaries
2. Claude generates tags and a context prefix for each chunk
3. An embedding model converts each chunk into a vector (a list of 1,536 numbers representing the chunk's meaning)
4. The chunk, tags, context prefix, and vector get stored in Supabase

**During generation (every time you create content):**
1. The target keyword gets converted into a vector
2. Supabase's pgvector finds the chunks with the most similar vectors (semantic search)
3. Tags are used to filter (only this client, relevant topics)
4. Retrieved chunks get included in the prompt alongside the client's voice profile and content type template
5. Claude writes using that retrieved context as source material

### Important: The AI doesn't copy-paste chunks together.

The retrieved chunks are **source material**, not building blocks. Claude reads them for context (data points, terminology, brand voice, past arguments) and then writes original content informed by that knowledge. The output is coherent, flowing, and original — not a patchwork.

### Coverage-Aware Generation:

The tag system enables a coverage check before writing. The system assesses how much relevant content exists in RAG for the given topic:

- **Strong coverage** — Multiple tagged chunks on this exact topic. Write with authority using the client's own data and examples.
- **Partial coverage** — Related content exists but not direct. Bridge from the client's strengths to the new topic.
- **No coverage** — Entirely new territory. Lean on web research for substance. Use RAG only for voice/style matching. Flag for human review.

This means the system automatically adjusts its strategy based on what it knows and doesn't know, rather than producing the same quality regardless of available input.

### Self-Growing Knowledge Base:

After content is published, it gets re-ingested into RAG. Topics that started with no coverage become well-covered after a few articles. The knowledge base compounds over time.

---

## 6. Content Type Routing

Instead of training separate AI models per content type, the system stores detailed templates and rules for each type in the content_types table. The n8n workflow pulls the right template based on the selected content type and injects it into the generation pipeline.

### Routing Logic in n8n:

```
Content type selected in form
    │
    ▼
Supabase query: Pull template where type_slug = selected type
    │
    ▼
Template gets injected into the pipeline prompts
    │
    ▼
Same pipeline runs, different rules applied
```

### Content Types to Define (full schemas needed per type):

**Lead Generation:**
- Informative blog post
- Service page
- Case study
- Landing page
- Comparison page
- Location page

**eCommerce:**
- Product page
- Collection/category page
- Buying guide
- Blog post (informational/educational)

**Both:**
- FAQ page
- About page
- Resource/guide (long-form)

**Each content type entry should thoroughly define:**
1. Purpose — what this content exists to do
2. Audience mindset — what the reader is thinking when they arrive
3. Structure template — required sections in order
4. SEO requirements — keyword placement, meta structure, schema markup
5. Proof elements — what kind of evidence belongs here
6. CTA guidance — what action to drive and how
7. Internal linking rules — how to link to other content
8. Quality criteria — what makes this type excellent vs mediocre
9. Common mistakes — what to explicitly avoid
10. Examples — 2-3 reference examples of excellent versions
11. Word count range — target length
12. Search intent — informational, transactional, navigational, commercial

**These schemas need to be individually planned and fleshed out with thorough detail. This is the next step before building.**

---

## 7. N8N Workflows

### Workflow 1: Client Onboarding — Content Ingestion

Run once per new client. Ingests their existing published content into RAG knowledge base. Voice profile generation handled separately.

**n8n workflow name:** "Client Onboarding - Content Ingestion"

**Status:** ✅ COMPLETE — All 10 nodes built, tested, and verified. Client D 16-page batch successfully run.

**Canvas node names (exact — used in n8n expressions):**
1. "On form submission" → 2. "Supabase" → 3. "Fetch Page HTML" → 4. "Code in JavaScript" → 5. "Extract Clean Content" → 6. "Chunk and Tag" → 7. "Parse Chunks" → 8. "Generate Embedding" → 9. "Merge Embedding" → 10. "Store Chunk"

```
Node 1: "On form submission" (Form Trigger)
  Fields: Client ID (text), Client Name (text)
  URL: bookmarkable form — submit to trigger workflow
    │
    ▼
Node 2: "Supabase" (Supabase — Get Many Rows)
  Table: published_content_map
  Filter: client_id = form input
  Returns: all page URLs for that client
    │
    ▼
Node 3: "Fetch Page HTML" (HTTP Request)
  Method: GET
  URL: {{ $json.page_url }} from each row
  Loops through all URLs automatically
    │
    ▼
Node 4: "Code in JavaScript" (Code node — JS, Run Once for Each Item)
  Removes scripts, styles, comments, HTML tags
  Decodes entities, collapses whitespace
  Truncates to 50,000 chars if needed
  Outputs: clean_text, page_url, original_length, cleaned_length
    │
    ▼
Node 5: "Extract Clean Content" (Anthropic — Sonnet)
  Skips fund listing blocks (product/fund name/objective/min.investment rows)
  Extracts: title, meta_description, headings[], clean_content
  Returns structured JSON
    │
    ▼
Node 6: "Chunk and Tag" (Anthropic — Sonnet, Max Tokens: 8192)
  Splits content into ~400 word chunks at paragraph boundaries
  Generates per-chunk: chunk_text, chunk_position, context_prefix,
  topic_tags, keyword_tags, content_type_tag, intent_tag,
  asset_tags, funnel_stage
  Returns raw JSON array (no markdown code blocks)
    │
    ▼
Node 7: "Parse Chunks" (Code node — JS, Run Once for All Items)
  Strips any markdown fences if present
  Parses JSON array from Claude output
  Attaches page_url (from "Supabase" node) and client_id (from "On form submission")
  Outputs one item per chunk
    │
    ▼
Node 8: "Generate Embedding" (HTTP Request — POST to OpenAI)
  URL: https://api.openai.com/v1/embeddings
  Body mode: Using Fields (NOT Using JSON — avoids character escaping issues)
  model: text-embedding-3-small
  input: {{ $json.context_prefix + " " + $json.chunk_text }}
    │
    ▼
Node 9: "Merge Embedding" (Code node — JS, Run Once for Each Item)
  Merges embedding array from OpenAI response with chunk data from "Parse Chunks"
  Outputs: client_id, chunk_text, context_prefix, source_url, chunk_position,
  topic_tags, keyword_tags, content_type_tag, intent_tag, asset_tags,
  funnel_stage, embedding
    │
    ▼
Node 10: "Store Chunk" (Supabase — Create a Row)
  Table: content_chunks
  Maps all fields from Merge Embedding output
  embedding field: JSON.stringify($json.embedding)
    │
    ▼
Content ingestion complete ✓
```

**Key design decisions:**
- URLs pulled from `published_content_map` (not hardcoded) — same workflow works for any client
- HTML stripped in a Code node before Claude sees it (raw HTML exceeded 200k token limit)
- Fund listing blocks explicitly excluded in Extract Clean Content prompt — pages with listings + educational content below will still produce good chunks
- Form trigger with bookmarkable URL — no need to open n8n editor to run it
- content_type_tag is inferred by Claude from the content — no manual configuration per client or content type
- **Body mode "Using Fields"** required for Generate Embedding — "Using JSON" breaks when chunk text contains special characters

**n8n lessons learned:**
- Node names matter — expressions reference nodes by their exact canvas name (e.g., `$('Supabase').first().json.page_url`)
- Parse Chunks must run in "Run Once for All Items" mode (not per item) and use `$input.all()`
- OpenAI embeddings node: use HTTP Request with "Using Fields" body mode, not JSON string interpolation

### Workflow 2: New Content Generation

**Status: ✅ COMPLETE AND TESTED — 22 nodes + 2 Google Docs output nodes. Multiple test runs completed (Feb 2026)**

Triggered by form submission. Runs the full multi-stage pipeline from Stage 1.

**Form inputs:** Client ID, Content Type Slug (e.g. `asset-class-page`), Target Keywords, Topic, Content Brief / V2O (optional)

```
Node 1: "On form submission" (Form Trigger)
    │
    ▼ (8 parallel branches)
Node 2:  "Get Client"          — Supabase, clients table
Node 3:  "Get Content Type"    — Supabase, content_types, filter: type_slug
Node 4:  "Get Audience Profile"— Supabase, audience_profiles, filter: client_id
Node 5:  "Get Voice Profile"   — Supabase, voice_profiles, filter: client_id
Node 6:  "Get Published Pages" — Supabase, published_content_map, filter: client_id
Node 7:  "Embed Keywords"      — OpenAI HTTP Request, text-embedding-3-small
Node 8:  "RAG Search"          — Supabase RPC match_content_chunks (connects from Node 7)
Node 9:  "SERP Search"         — DataForSEO HTTP Request, Basic Auth
Node 10: "Tavily Stats"        — Tavily HTTP Request, api_key in body
    │
    ▼
Node 11: "Merge" (Append mode — all 8 branches)
    │
    ▼
Node 12: "Merge Context" (Code node — assembles all data into single JSON object)
    │
    ▼ (sequential Claude pipeline)
Node 13: "Coverage Check"   — Sonnet, 1000 tokens — JSON output: coverage score, gaps, duplicate risk
Node 14: "Research Brief"   — Sonnet, 2000 tokens — synthesises SERP + Tavily + RAG
Node 15: "Outline"          — Opus,   2000 tokens — section-by-section, follows structure_template
Node 16: "Draft"            — Opus,   8000 tokens — full article, markdown, with links
Node 17: "Critique"         — Opus,   2000 tokens — editorial critique vs quality_criteria
Node 18: "Gap Research"     — Sonnet, 2000 tokens — extracts evidence to address critique gaps
Node 19: "Rewrite"          — Opus,   8000 tokens — final article incorporating critique + gap research
Node 20: "Fact Check"       — Sonnet, 1500 tokens — JSON output: passed, issues[], summary
Node 21: "Deliverables"     — Sonnet, 500 tokens  — JSON: seo_title, meta_description, slug, h1, image_alt
    │
    ▼
Node 22: "Save to content_jobs" (Supabase — Create Row)
  Fields: client_id, content_type, target_keywords, topic, mode=new,
          status=draft, outline, research_brief, critique, final_output, model_used
```

**Key design decisions:**
- All prompts are client-agnostic — client-specific context comes from database expressions, never hardcoded
- Internal links: publishedPages only. External citations: Tavily only. SERP = insights, never linked (competitor pages).
- Universal style rules in Draft + Rewrite system prompts: no em-dashes, no filler phrases, no repetition, 15-30 word sentences, active voice, E-E-A-T
- Simplify Output ON for all Anthropic nodes — downstream references use `.json.content[0].text` (NOT `.json.text`)
- Google Docs output: 2 nodes added after Node 22
  - Node 23 "Format for Google Docs" (Code): markdown → HTML + multipart/related body construction
  - Node 24 "Create Google Doc" (HTTP Request): POST to Drive API with multipart/related body, converts HTML to formatted Google Doc
  - Output folder: Google Drive folder ID `1tWup1S3S7GGFing1CS9-iKPUBzd6qKOf`
  - Doc naming: `[Client Name] — [Topic] — [YYYY-MM-DD]`
- Word count: set wordCountRange ~20% below actual target — Claude overshoots by 10-15% consistently
- Word count constraint must be in Outline prompt (section count planning) AND Rewrite prompt — Outline is where scope is locked
- Citations: Rewrite prompt includes "one hyperlink per source, first mention only" rule
- Tavily query: `$json['Target Keywords'] || $json['Topic']` — fallback prevents blank topic searches
- Why no GSC/EEAT in Workflow 2: new content has no existing URL → no GSC data, no content to assess. Both belong in Workflow 3 only.
- **V2O (Content Brief) — per-job editorial override layer:**
  - Form field renamed from "Notes" to "Content Brief (V2O)"
  - Accepts freeform text using a structured format convention: QUOTES / MUST COVER / RESOURCES / EXCLUDE
  - Passed through Merge Context as `v2o` field
  - V2O instructions take precedence over all research and standard guidelines — they are editorial directives, not suggestions
  - Appears at the TOP of Research Brief, Outline, Draft, and Rewrite prompts with mandatory framing
  - Critique node includes a V2O compliance check — flags anything missed so Gap Research + Rewrite can address it
  - Conditional expression: `{{ v2o ? '...' + v2o : '' }}` — empty field has zero impact on standard runs
  - No database tables required — entirely form-level, per-job input
  - Format convention (shown as placeholder in form):
    ```
    QUOTES:
    [Speaker Name, Title]: "Quote text"

    MUST COVER:
    - Point or angle to include

    RESOURCES:
    - URL or data point to reference

    EXCLUDE:
    - Topic or angle to avoid
    ```

### Workflow 3: Content Update

Triggered by form submission in "update" mode. Starts with EEAT assessment and GSC data pull (Stage 0), then runs the shared pipeline with update context injected at each stage.

```
TRIGGER: Form submission (webhook)
  Inputs: client_id, page_url, content_type, target_keywords, notes
  Mode: UPDATE
    │
    ▼
STAGE 0 — ASSESSMENT (update-only):
  ├── Scrape existing page content from page_url
  ├── Claude: EEAT assessment → store in eeat_assessments table
  └── GSC API: Pull performance data → store in gsc_page_data table
    │
    ▼
PARALLEL DATA PULL (same as new, plus assessment data):
  ├── Supabase: Client data (brand, type, market)
  ├── Supabase: Voice profile
  ├── Supabase: Content type template
  ├── Supabase: Vector search for relevant chunks
  ├── Supabase: Published content map (for internal linking)
  ├── Supabase: EEAT assessment (just generated)
  ├── Supabase: GSC page data (just fetched)
  ├── Web Search: SERP analysis for target keyword
  └── Web Search: Current data, stats, references
    │
    ▼
MULTI-STAGE PIPELINE: Stages 1-7 with update context
  (see Section 8 — [UPDATE MODE] additions at each stage)
    │
    ▼
OUTPUT:
  ├── Create Google Doc in client folder (marked as "UPDATE")
  ├── Supabase: Log job in content_jobs (mode: "update")
  └── Slack: Notify reviewer with EEAT before/after summary
```

### Workflow 4: Feedback Loop

Triggered when a content job status is updated to "published."

```
TRIGGER: Supabase webhook — content_jobs.status = "published"
    │
    ▼
Fetch the published article text
    │
    ▼
Run through ingestion pipeline:
  Chunk → Tag → Embed → Store in content_chunks
    │
    ▼
Update published_content_map with the new URL
    │
    ▼
Knowledge base grows ✓
```

---

## 8. Multi-Stage Content Pipeline

This is the core of the system. The pipeline operates in two modes — **new content** and **content updates** — sharing the same core stages but with different entry points.

For new content, the pipeline starts at Stage 1. For updates, it starts at Stage 0 (EEAT Assessment + GSC data pull), which informs every subsequent stage with specific knowledge of what needs improving.

### Update-Only Stages (Stage 0)

These stages only run when updating existing content. They provide the assessment and performance data that make updates targeted rather than blind.

### Stage 0a: EEAT Assessment (UPDATE MODE ONLY)
**Model: Opus (analytical, editorial judgment)**

```
Input: Scraped content from the existing page URL

Job: "You are a senior content strategist and SEO expert.
Assess this existing page against Google's E-E-A-T framework:

EXPERIENCE:
- Does the content show first-hand experience?
- Are there real examples, case studies, or original data?

EXPERTISE:
- Does it demonstrate subject-matter depth?
- Are technical concepts handled accurately?
- Does it go beyond surface-level coverage?

AUTHORITATIVENESS:
- Are claims supported by named, credible sources?
- Are industry reports, regulatory bodies, or expert
  quotes referenced?
- How many unsupported claims exist?

TRUSTWORTHINESS:
- Is coverage balanced (benefits AND risks)?
- Are statistics dated and attributed?
- Is the content transparent about limitations?

Output a structured assessment:
1. Overall rating: weak / moderate / strong
2. Strengths (what to preserve)
3. Weaknesses (what to improve)
4. Gaps (what's completely missing)
5. Priority actions (ordered by impact)"

Output: EEAT assessment (stored in eeat_assessments table)
```

### Stage 0b: GSC Data Pull (UPDATE MODE ONLY)
**Model: N/A (API call, no Claude needed)**

```
Input: Page URL + client's GSC property ID

Job: Pull from Google Search Console API:
- Top queries driving traffic to this page (last 90 days)
- Click, impression, CTR, position per query
- Queries where position is declining (compare 90d vs prior 90d)
- High-impression, low-CTR opportunities (position 8-20)

Output: GSC performance data (stored in gsc_page_data table)

This data feeds into Stage 2 (Research) and Stage 3 (Outline)
so the pipeline knows:
- Which keywords to protect (already ranking well)
- Which keywords to strengthen (declining)
- Which keywords to target (high impressions, low position)
```

---

### Shared Pipeline (Both Modes)

The following stages run for both new content and updates. When in update mode, the EEAT assessment and GSC data are injected as additional context into the relevant stages.

### Stage 1: Coverage Check
**Model: Sonnet (fast, analytical)**

```
Input: Retrieved RAG chunks + their tags
       + [UPDATE MODE] EEAT assessment, GSC data

Job: "Based on the tagged chunks retrieved for this client
and topic, assess coverage:
- How many relevant chunks exist?
- What subtopics are well-covered?
- What's missing?
- Recommend: authority approach, bridge approach,
  or research-heavy approach.
- [UPDATE MODE] Cross-reference with EEAT gaps —
  which weaknesses can RAG help address?"

Output: Coverage strategy document
```

### Stage 2: Research
**Model: Sonnet (fast, information processing)**

```
Input: Web search results, SERP analysis, RAG chunks,
       competitor content, coverage strategy
       + [UPDATE MODE] EEAT gaps, GSC declining/opportunity keywords

Job: "Synthesize all research:
- What's already been said about this topic?
- What do the top-ranking results have in common?
- What gaps exist that nobody is covering?
- What data/statistics are available?
- What angles are overdone?
- What questions is the audience actually asking?
- [UPDATE MODE] Specifically find data, sources, and
  evidence to fill these EEAT gaps: [gap list]
- [UPDATE MODE] Research these declining/opportunity
  keywords for content angle: [GSC keyword list]"

Output: Research brief
```

### Stage 3: Angle + Outline
**Model: Opus (creative thinking, strategic)**

```
Input: Research brief, audience profile, content type
       template, coverage strategy
       + [UPDATE MODE] EEAT assessment, GSC data,
         existing page structure

Job:
  [NEW MODE] "Based on the research, determine a fresh angle
  that differentiates from what's already ranking.
  Create a detailed outline:
  - Hook that isn't generic
  - Section-by-section breakdown with key points
  - Where to use client's own data vs external sources
  - Internal linking opportunities
  - Must follow the [content type] structure template
  - Must address what this [audience profile] cares about"

  [UPDATE MODE] "Based on the EEAT assessment and GSC data,
  create an outline for the updated page:
  - Preserve sections identified as strengths
  - Restructure or expand sections identified as weak
  - Add entirely new sections for identified gaps
  - Ensure declining keywords are addressed in relevant sections
  - Incorporate opportunity keywords where natural
  - Must follow the [content type] structure template"

Output: Detailed outline

🔴 OPTIONAL HUMAN CHECKPOINT: Send outline via Slack
   for approval before proceeding to draft
```

### Stage 4: Draft
**Model: Opus (core writing quality)**

```
Input: Approved outline, voice profile, relevant RAG chunks,
       source material, content type template
       + [UPDATE MODE] existing page content (to preserve good sections)

Job: "Write the full piece following this outline exactly.
Match this voice fingerprint:
[full voice profile injected]

Follow this structure:
[content type template injected]

Use these sources:
[retrieved chunks + web research injected]

Reference the client's own data where available.
Cite external sources where needed.

[UPDATE MODE] Preserve the strongest sections from the
existing content. Rewrite weak sections. Write new sections
for identified gaps. Do not lose ranking-relevant content
for these keywords: [GSC top queries list]"

Output: First draft
```

### Stage 5: Critique + Gap Identification
**Model: Opus (strong editorial judgment)**

```
Input: First draft, content type quality criteria
       + [UPDATE MODE] EEAT assessment (to verify gaps were addressed)

Job: "You are a senior editor. Review this draft:
- Does the opening hook or does it bore?
- Are there unsupported claims?
- Are there sections that tell instead of show?
- Identify filler paragraphs that add nothing
- Flag AI-typical phrasing: 'In today's...', 'It's
  important to note', 'When it comes to', 'At the
  end of the day', 'In the ever-evolving world of'
- Flag vague language: 'many companies', 'significant
  improvement', 'various factors'
- Does every section earn its place?
- Does it actually deliver on the headline promise?
- Does it match the [content type] structure?
- Would the target audience find this valuable?
- [UPDATE MODE] Were all EEAT gaps addressed? Which remain?

CRITICAL — For each unsupported claim or weak section,
specify exactly what kind of evidence is needed:
- 'Needs a specific statistic from [type of source]'
- 'Needs a named expert quote or industry report citation'
- 'Needs a concrete example or case study'
This gap list will be used to fetch additional data."

Output: Detailed critique + specific evidence gap list
```

### Stage 5b: Gap Research
**Model: Sonnet (targeted information retrieval)**

```
Input: Evidence gap list from Stage 5 critique

Job: "The editor identified these specific gaps in the draft.
For each gap, find the exact data needed:

[gap list, e.g.:]
- Section 3 claims 'significant growth' — find actual
  market size data with named source
- Section 5 lists risks without examples — find a real
  case or incident that illustrates each risk
- Section 7 gives generic fee guidance — find actual
  typical fee ranges for this asset class in Australia

Search for each gap. Return findings as a structured list
matching each gap to its evidence. If evidence cannot be
found, return [NEEDS VERIFICATION] for that item."

Output: Evidence package (matched to specific gaps)
```

### Stage 6: Rewrite
**Model: Sonnet (following specific instructions)**

```
Input: First draft + critique + evidence package from gap research

Job: "Rewrite this draft addressing every point in
the critique. You now have additional evidence to fill
gaps — integrate it naturally:

[evidence package injected]

Don't just polish surface-level — fix structural issues,
replace generic language with the specific data provided,
and strengthen weak sections with the new evidence.
Maintain the same voice throughout."

Output: Second draft (stronger, with evidence gaps filled)
```

### Stage 7: Fact-Check + Polish
**Model: Sonnet (verification, precision)**

```
Input: Second draft, web search for claim verification,
       published content map
       + [UPDATE MODE] GSC top queries (to verify keyword coverage)

Job: "Final pass:
1. Verify all statistics and claims. Flag anything
   that cannot be confirmed with a [NEEDS VERIFICATION] tag.
2. Check for consistency with the voice profile.
3. Add internal links to relevant existing client content
   where they fit naturally. Available pages: [list from
   published_content_map]
4. Readability check — target [grade level from audience profile].
   Simplify any overly complex sentences.
5. Final copyedit: grammar, flow, transitions.
6. [UPDATE MODE] Verify that top GSC queries are still
   represented in the content. Flag any ranking keywords
   that may have been accidentally removed."

Output: Final article
```

---

## 9. Quality Enhancement Techniques

These are additional techniques built into the pipeline that push output quality beyond standard AI content.

### Voice Fingerprinting
During onboarding, Claude performs deep analysis of 10-20 client articles to extract specific patterns — not just "professional tone" but exact sentence lengths, vocabulary choices, structural habits, and proof styles. This fingerprint is referenced at every stage of generation.

### SERP Intent Analysis
Before writing, the system analyses what Google is actually ranking for the target keyword. This ensures the content matches search intent, includes must-have elements, and differentiates where competitors are weak.

### Anti-Generic Filtering
Stage 5 (Critique) explicitly flags and removes AI-typical writing patterns: generic openings, filler phrases, vague claims, and repetitive list formatting. This is the single biggest quality lever for making AI content not read like AI content.

### Source Hierarchy
The pipeline prioritizes sources in this order:
1. Client's own data and case studies (highest authority)
2. Primary research, surveys, and industry reports
3. Named expert quotes and academic research
4. Reputable publication articles
5. General web sources (lowest priority)

This prevents the content from being a generic summary of Google results and instead anchors it in the client's own expertise.

### Content Ecosystem Awareness
The published_content_map table ensures new content references and links to existing client content. It also prevents duplicate coverage and positions new pieces within the broader content strategy.

### Audience-Specific Adaptation
The audience_profiles table contains detailed information about what the reader already knows, what they're struggling with, what they're skeptical of, and what resonates. The outline stage uses this to ensure every section speaks to real reader concerns.

### Self-Growing Knowledge Base
Every published article gets re-ingested into RAG. Topics with initially weak coverage become strong coverage areas over time. The system literally gets better with each piece of content it produces.

### Performance Feedback Loop (Future Enhancement)
Track article performance (traffic, time on page, rankings) and periodically analyse top performers vs underperformers. Update voice profiles and content type templates based on what actually works for each client's audience.

---

## 10. Scaling to New Clients

### Onboarding an existing client (has content):
1. Upload their articles into the ingestion workflow
2. Voice fingerprint generates automatically
3. Fill in audience profile (30 min)
4. Verify client data in Supabase (10 min)
5. Test-generate 2-3 articles, review quality (2-3 hours)
6. Refine voice profile or prompts if needed

**Total per client: approximately half a day to one full day**

### Onboarding a new client (no content yet):
1. Gather brand guidelines, website copy, any available samples
2. Run what's available through ingestion (even a few pages help)
3. Voice profile will be thinner — supplement with manual style notes
4. System operates in "research-heavy" mode for first articles
5. After first batch of articles are published and re-ingested, coverage builds

### What scales automatically:
- All n8n workflows work for any client — parameterized by client_id
- Content type templates are shared across all clients
- The pipeline logic never changes per client

### What needs manual attention per client:
- Audience profile definition
- Quality review of initial outputs
- Ongoing spot-checking

---

## 11. Cost Estimates

### Infrastructure:
- n8n Cloud: ~$24/month (or self-hosted for free)
- Supabase: Free tier handles significant volume. Pro plan $25/month if needed.
- Claude API: Pay per use (see below)
- OpenAI Embeddings: ~$0.02 per million tokens (negligible)
- Web Search API: Tavily free tier = 1,000 searches/month
- Google Search Console API: Free (requires GSC property access per client)

### Per-article generation cost — NEW content (8 Claude calls):

| Stage | Model | Estimated Cost |
|---|---|---|
| Coverage check | Sonnet | ~$0.01 |
| Research | Sonnet | ~$0.03 |
| Angle + outline | Opus | ~$0.15 |
| Draft | Opus | ~$0.20 |
| Critique + gap identification | Opus | ~$0.15 |
| Gap research | Sonnet | ~$0.03 |
| Rewrite | Sonnet | ~$0.05 |
| Fact-check + polish | Sonnet | ~$0.03 |
| **Total per new article** | | **~$0.55 - $2.10** |

### Per-article generation cost — UPDATE content (9-10 Claude calls):

| Stage | Model | Estimated Cost |
|---|---|---|
| EEAT assessment | Opus | ~$0.15 |
| GSC data pull | N/A (API) | ~$0.00 |
| Coverage check | Sonnet | ~$0.01 |
| Research (informed by EEAT/GSC) | Sonnet | ~$0.04 |
| Outline changes | Opus | ~$0.15 |
| Draft/rewrite | Opus | ~$0.20 |
| Critique + gap identification | Opus | ~$0.15 |
| Gap research | Sonnet | ~$0.03 |
| Rewrite | Sonnet | ~$0.05 |
| Fact-check + polish | Sonnet | ~$0.03 |
| **Total per update** | | **~$0.70 - $2.50** |

Cost varies with article length and prompt size. Updates cost slightly more due to the EEAT assessment stage. Even at the high end, producing hundreds of articles per month costs under $250 in API fees.

### Per-client onboarding cost:
- Ingestion (chunking + tagging): ~$0.50 - $2.00 depending on volume of existing content
- Voice fingerprint generation: ~$0.10
- Negligible overall

---

## 12. Decisions Needed Before Building

Before construction begins, the following decisions need to be made:

### 1. Pilot Client
Which client to onboard first? Ideal: one with the most existing content (gives RAG the best starting material) and a clear, established voice.

### 2. First Content Type
Which content type to build and test first? Likely the type produced most frequently — probably blog posts or service pages.

### 3. Quality Benchmark
Select 5-10 examples of content the team considers excellent. These become the standard that pipeline output is measured against.

### 4. Review Process
Who reviews generated content before publishing? Options:
- Jan reviews all output initially
- Consultants (Alex/Jess) review for their clients
- Client reviews directly

### 5. Full Content Type List
Confirm every content type the agency produces. Each needs its own thorough schema in the content_types table. Current list from discussion:

**Lead Gen:** Service page, informative blog post, case study, landing page, comparison page, location page

**eCom:** Product page, collection page, buying guide, blog post

**Both:** FAQ page, resource/guide

### 6. Content Type Schemas
Each content type needs to be fully fleshed out with structure, rules, examples, quality criteria, and SEO requirements. This is the most important planning step remaining and should be done before building.

---

## 13. Build Timeline

### Phase 1: Setup + First Client (estimated ~10-12 hours hands-on)
- ✅ Supabase tables and pgvector setup (9 tables, schema + seed data deployed)
- ✅ n8n Workflow 1: Content Ingestion (complete — all clients ingested, loop fix applied)
- ✅ Ingest first client's content (Client D — all 16 pages ingested into content_chunks)
- ✅ n8n Workflow 2: New Content Generation pipeline (complete — tested, Client K onboarded)
- ⬜ n8n Workflow 4: Feedback Loop (simpler — re-uses ingestion logic)
- ⬜ n8n Workflow 3: Content Update pipeline (most complex — GSC API + EEAT)
- ✅ Test generation with Private Equity page and refine prompts
- ⬜ Voice profile generation (separate workflow or manual step)

### Phase 2: Subsequent Clients (estimated ~4-8 hours per client)
- Upload content, auto-ingest
- Define audience profile
- Test and review outputs
- Refine as needed

### Phase 3: Ongoing
- Prompt refinement as patterns emerge
- Re-ingest published content
- Add performance tracking (when ready)
- Add new content types as needed

### Build Log
- **Session 1 (Feb 2026):** Plan document created. Architecture decided. Dual-mode pipeline designed.
- **Session 2 (Feb 2026):** Supabase schema built (9 tables). Client D seed data loaded (client, audience, content type, voice profile, 16 published URLs). n8n workflow started — Nodes 1-5 of ingestion pipeline built and tested.
  - Supabase connected to n8n (API credentials configured)
  - Anthropic connected to n8n (API credentials configured)
  - Discovered raw HTML exceeds Claude's 200k token limit — added Strip HTML code node as preprocessing step
  - Tested end-to-end: Form → Supabase URL lookup → HTML fetch → Strip → Claude extraction. Working for single page (Private Equity). Full 16-page batch pending workflow completion.
- **Session 3 (Feb 2026):** Workflow 1 completed. All 10 nodes built and verified. Full 16-page Client D batch run successfully. Data confirmed in Supabase content_chunks table.
  - OpenAI credentials configured in n8n (for embeddings)
  - Nodes 6-10 built: Chunk+Tag (Claude) → Parse Chunks (Code) → Generate Embedding (OpenAI HTTP Request) → Merge Embedding (Code) → Store Chunk (Supabase)
  - Key fix: Extract Clean Content prompt updated to skip fund listing blocks
  - Key fix: Generate Embedding uses "Using Fields" body mode (not "Using JSON")
  - Key fix: Parse Chunks runs in "Run Once for All Items" mode with `$input.all()`
  - Dedup node added (node 11): deletes existing chunks for source_url + client_id before re-ingesting
  - Next: Build Workflow 2 (New Content Generation)
- **Session 4 (Feb 2026):** Workflow 2 completed and tested. Google Docs output added. Multiple Private Equity article runs with iterative quality improvements.
  - All 22 pipeline nodes working. All fields saving correctly to content_jobs.
  - Key fixes: camelCase Merge Context field names throughout all prompts; `.json.content[0].text` output path for all Anthropic nodes; client_id from form input directly
  - Google Docs output: Node 23 "Format for Google Docs" (Code — markdown→HTML + multipart body) + Node 24 "Create Google Doc" (HTTP Request — Drive API multipart/related upload)
  - Google Drive credential: Google Drive OAuth2 API (Google Drive account 3 in n8n)
  - Word count: wordCountRange in Outline prompt (section planning) + Rewrite prompt (prose tightening). Set DB value ~20% below actual target due to Claude overshoot.
  - Citation discipline: "one hyperlink per source, first mention only" added to Rewrite prompt
  - Tavily query: Topic fallback added — `$json['Target Keywords'] || $json['Topic']`
  - Content quality assessed as publishable: current data (2025 Yearbook), balanced coverage, strong source discipline
  - Next: Build Workflow 3 (Content Update) — V2O integration
- **Session 5 (Feb 2026):** Prompt and data quality improvements to Workflow 2. V2O architecture designed.
  - Draft + Rewrite prompts updated to use all 8 voice profile fields (was 3/8) + full audience context (all 5 fields, was 1)
  - Merge Context ragChunks updated: now includes sourceTitle, sourceDate, assetTags fields
  - Supabase voice_profiles trigger bug fixed: column is `last_updated` not `updated_at` — new trigger created, old dropped
  - sample_passages populated for Client D with 3 representative passages — most impactful voice profile field
  - DataForSEO SERP node fixed (401 credentials error resolved)
  - relatedSearches added to serpData extraction in Merge Context (was only capturing organic + PAA)
  - Research Brief prompt: added RELATED SEARCH QUERIES section + section 6 "Investor questions to address"
  - Outline prompt: added SEARCH INTENT SIGNALS block + FAQ instruction to draw from related searches
  - V2O (Content Brief) feature designed and implementation plan completed:
    - Form-level per-job editorial override — no new database tables
    - Structured freeform text: QUOTES / MUST COVER / RESOURCES / EXCLUDE
    - Injected at top of Research Brief, Outline, Draft, Rewrite with mandatory framing
    - Critique node: V2O compliance check added
    - V2O takes priority over all research — human editorial directive, not suggestion
  - Three article versions compared (V1/V2/V3): V3 best — narrative citations, stronger risk coverage, audience-aware
  - Next: Implement V2O in workflow (form + Merge Context + prompts), then Workflow 3
- **Session 6 (Feb/Mar 2026):** V2O implemented in Workflow 2. Client K onboarded as second client.
  - V2O fully implemented: form field, Merge Context mapping, injected into Research Brief + Outline + Draft + Critique + Rewrite prompts
  - Client K set up: client record, audience profile, voice profile, gblog content type, published_content_map populated (~387 blog URLs), content ingested via Workflow 1
  - Client D: all ~272 article URLs added to published_content_map (4-part SQL insert)
  - im-article content type created for Client D blog articles (900-1200 word target)
  - Workflow 1 rate limiting fix: Loop Over Items (batch size 1) added before Fetch Page HTML to prevent 504 gateway timeout from simultaneous HTTP requests
  - Workflow 1 reliability fix: Always Output Data ON for all nodes; On Error: Continue on Fetch Page HTML; Return All enabled on Supabase node
- **Session 7 (Mar 2026):** Client facts system, USP RAG seeding, internal linking and CTA fixes.
  - `key_facts` column added to clients table — short factual summary injected conditionally into Draft + Rewrite prompts
  - Client K key_facts populated (ISO 27001, SOC 2, Great Place to Work, tenure stats, 3:1 cost ratio, UTC+8, staff augmentation model)
  - 7 USP chunks manually seeded into content_chunks for Client K — contextual retrieval of differentiators without forcing into every article
  - "Generate Embeddings" mini-workflow created (3 nodes) for backfilling embeddings on manually seeded chunks
  - Critical bug fixed: Draft + Rewrite prompts used `p.page_title`/`p.page_url` but Merge Context maps these to `p.title`/`p.url` — internal links were resolving to `undefined`
  - internalLinkingRules and ctaGuidance added explicitly to Draft + Rewrite prompts
  - cta_guidance updated for Client K with actual book-consultation URL
  - Next: Workflow 3 (Content Update)
- **Session 9 (Mar 2026):** Google Docs output improvements, Shutterstock image integration, token cost diagnosis and Tavily fix.
  - **Format for Google Docs** fully rebuilt: metadata header (CLIENT/URL/PAGE TITLE/META DESCRIPTION), blockquote handler (plain indented style — no blue boxes), IMAGE placeholder handler (plain paragraph with bold icon + URL link), table/list/heading/paragraph markdown→HTML conversion
  - **Shutterstock image integration**: Deliverables node outputs `image_queries` array (5 search terms). New 3-node chain: "Parse Image Queries" (Code) → "Shutterstock Search" (HTTP Request, Basic Auth) → "Collect Images" (Code). Image URLs injected into article at `[IMAGE: description]` placeholders. n8n Code nodes cannot use fetch()/https/http — must use dedicated HTTP Request nodes.
  - **Deliverables JSON parse fix**: Claude wraps output in markdown code fences. Fix: strip fences with regex before JSON.parse + system message "Respond with raw JSON only. No markdown code fences."
  - **Workflow topology**: Deliverables branches to two parallel paths — "Save to content_jobs" (dead end) and image chain leading to "Format for Google Docs". These are separate branches, not sequential.
  - **Token cost diagnosis**: Added debug Code node before Research Brief logging `charSizes` and `estimatedTokens` per Merge Context field. Identified Tavily as 213k tokens (853k chars) — `raw_content` was untruncated.
  - **Tavily fix**: `(r.raw_content || r.content || '').slice(0, 6000)` — ~1,000 words per result. Enough for key facts/stats, eliminates full article ingestion bloat. Total Tavily tokens now ~7,500.
  - **RAG chunks empty**: ragChunks showing 2 chars (empty array) — needs investigation. Likely match_content_chunks RPC or embedding mismatch for current client/topic.
  - Next: Fix RAG chunks returning empty + build Workflow 3 (Content Update)
- **Session 8 (Mar 2026):** Tavily token fix, V2O clarification, Workflow 1 loop fix.
  - **Tavily 602k token error fixed**: `raw_content` field returns full article text per result (10,000-60,000 chars each). Fix: truncate to `.slice(0, 8000)` per result in Merge Context tavilyData mapping + reduce max_results from 10 to 5. Total Tavily tokens now ~10,000 — well within 200k limit.
  - **V2O clarification**: V2O is for per-article editorial overrides including expert quotes. Paste relevant client executive quotes + MUST COVER directives into the Content Brief (V2O) field when submitting each job. NOT a database column — entirely form-level, per-job input.
  - **Workflow 1 root cause identified**: Loop Over Items (batch size 1) was sending 6 items per batch. Generate Embedding error branch dead-ended (didn't reconnect to Loop Over Items). Loop waited for all 6 items to return, only received 5, stalled indefinitely. Workflow "completed successfully" after hitting n8n 15-min execution timeout with only 6 items processed.
  - **Workflow 1 fix**: Removed Loop Over Items entirely. Fetch Page HTML has a built-in **Batching** option (Add option → Batching): batch size 1, interval 3000ms. n8n processes all items sequentially with 3-second gaps — same rate-limiting effect without the loop stall risk. Supabase node now connects directly to Fetch Page HTML.
  - Next: Test Workflow 2 with Client K + build Workflow 3 (Content Update)

---

---

## 14. Pilot Client: Client D

### Client Overview

- **Brand:** Client D
- **Website:** clientd.example.com
- **Business type:** Marketplace / Lead gen (connects investors with investment products)
- **Market:** Australia
- **Industry:** Financial services / Investment marketplace
- **Model:** Investors browse asset class pages → find products → enquire/apply (lead gen for fund managers)

### What the Site Does

Client D is an Australian investment marketplace that lists investment products (managed funds, ETFs, LICs, term deposits, unlisted shares, etc.) across multiple asset classes. It allows investors to find, compare, and enquire about investments. Revenue comes from fund managers advertising their products on the platform.

Each asset class has a dedicated page that serves two purposes:
1. **Product directory** — filterable listings of investment products in that asset class
2. **Educational content** — a comprehensive guide explaining the asset class to help investors make informed decisions

### Existing Asset Class Pages (16 total)

| Page | URL | Content Depth |
|---|---|---|
| Private Equity | /investments/private-equity | Minimal — listings only, no educational content |
| Large Caps Australia | /investments/large-caps-australia | Moderate — brief educational section + FAQ |
| Australian Equity Funds | /investments/australian-equity-funds | TBD |
| Small Caps Australia | /investments/small-caps-australia | Moderate — brief educational section + FAQ |
| Exchange Traded Funds | /investments/exchange-traded-funds | Deep — comprehensive guide with sections, tables, strategies, FAQs |
| Large Caps Global | /investments/large-caps-global | TBD |
| Bond Funds | /investments/bond-funds | Moderate — standard educational section + FAQ |
| Income Funds | /investments/income-funds | TBD |
| Property | /investments/property | TBD |
| Property Funds | /investments/property-funds | Minimal — listings only, no educational content |
| Mortgage Funds | /investments/mortgage-funds | Deep — comprehensive guide, risk framework, comparison tables |
| Private Credit | /investments/private-credit | Deep — comprehensive guide with market data, types, strategies |
| LICs/LITs | /investments/lics-lits | TBD |
| Multi-Asset Portfolios | /investments/multi-asset-portfolios | TBD |
| Managed Accounts | /investments/managed-accounts | TBD |
| Cash | /investments/cash | Moderate — standard educational section + FAQ |

### Content Quality Analysis

After analysing 8 of the 16 pages, there is a **significant quality gap** across pages:

**Tier 1 — Deep, comprehensive content (the benchmark):**
- ETFs page: ~4,000+ words. Covers what ETFs are, types, benefits, risks, strategies, tax, comparison tables, FAQs. Well-structured, data-rich, cites specific sources (ASIC, CommSec, Canstar).
- Private Credit page: ~3,000+ words. Market context, growth drivers, types of private credit, benefits, risks, comparison framework. Cites Morgan Stanley, McKinsey, Russell Investments, PGIM.
- Mortgage Funds page: ~3,000+ words. Strong risk framework, pooled vs contributory distinction, comparison table vs other income investments, common misconceptions section.

**Tier 2 — Basic educational content:**
- Large Caps Australia: ~1,000 words. Covers types, features, risks, FAQs. Functional but thin.
- Small Caps Australia: ~800 words. Similar structure, even thinner.
- Bond Funds: ~1,000 words. Standard coverage, nothing distinctive.
- Cash: ~800 words. Basic coverage of cash and money market accounts.

**Tier 3 — Listings only, no educational content:**
- Private Equity: Product listings with filters, no educational guide.
- Property Funds: Same — listings only.

**The goal should be to bring every page up to Tier 1 quality.**

### Voice Fingerprint — Client D

Based on analysis of the existing content across pages:

**Tone:** Informative, professional, neutral. Not promotional — the site positions itself as an independent research platform, not a seller. Educational without being patronising.

**Sentence patterns:** Medium-length sentences (15-20 words average). Declarative and explanatory. Uses definition-first structure ("Private credit is a form of non-bank lending whereby..."). Minimal use of questions in body copy.

**Vocabulary:**
- Uses: "investors", "asset class", "risk-adjusted returns", "portfolio diversification", "due diligence"
- Avoids: Hard sales language, first person ("we"), informal/casual phrasing
- Financial terminology used freely but explained on first use
- Australian spelling and regulatory references (ASIC, APRA, ASX, FCS, ATO, SMSF)

**Structure patterns (Tier 1 pages):**
- Opens with a definition of the asset class
- Sections follow a logical progression: What → Types → Benefits → Risks → How to Compare → How to Invest → FAQ
- Uses comparison tables to contrast with alternative investments
- Cites specific data sources and industry reports
- FAQs address practical investor questions
- Closes with a balanced summary

**Proof/evidence style:**
- Cites industry reports by name (Morgan Stanley, McKinsey, Russell Investments, PGIM)
- Includes specific numbers ("$200 billion in AUM by 2024", "correlation of only 0.33 with US equities")
- References regulatory bodies (ASIC RG45, APRA)
- Balanced — always pairs benefits with risks

**What the voice is NOT:**
- Not opinion-driven or editorial
- Not first-person ("we believe...")
- Not promotional toward any specific product
- Not dumbed-down — assumes some financial literacy
- Not US-centric — always Australian context

---

## 15. Content Type Schema: Asset Class Page

This is the detailed schema for the first content type to be built. It defines every aspect of what makes an excellent asset class page on Client D.

### Purpose
Educate investors about a specific asset class so they can make informed decisions about whether to invest, how to evaluate products, and what risks to consider. Simultaneously serve as an SEO landing page that ranks for "[asset class] Australia" and related searches, driving organic traffic to the product listings.

### Audience Mindset
The reader is an Australian investor (retail or wholesale) who is:
- Researching whether this asset class belongs in their portfolio
- Trying to understand how it works, what the risks are, and how to get started
- Comparing this asset class against alternatives they already know
- Looking for a trustworthy, independent source (not a fund manager's sales pitch)
- May be a self-directed investor, SMSF trustee, or working with a financial adviser

### Audience Profile: Client D

| Field | Detail |
|---|---|
| **Primary audience** | Australian retail and wholesale investors researching asset classes |
| **Secondary audience** | Financial advisers, SMSF trustees, accountants researching on behalf of clients |
| **Already knows** | Basic investing concepts (shares, bonds, property). Familiar with the ASX. Understands risk/return tradeoff at a high level. |
| **Struggling with** | Understanding niche/alternative asset classes. Knowing which product structures suit them (managed fund vs ETF vs LIC). Evaluating risk beyond surface-level descriptions. Understanding tax implications. |
| **Skeptical of** | Marketing from fund managers. Promises of high returns without risk context. Overly simplified explanations that gloss over downsides. |
| **Responds to** | Specific data and statistics. Named sources and industry reports. Balanced coverage of both benefits and risks. Comparison frameworks that help them evaluate. Practical "how to" guidance. |
| **Reading level** | Grade 11-12. Professional, assumes financial literacy but not expertise. |

### Structure Template

The following sections are required, in this order. This structure is derived from the best-performing existing pages (ETFs, Private Credit, Mortgage Funds).

```
1. INTRODUCTION / DEFINITION
   - What is [asset class]?
   - Clear, concise definition in 2-3 sentences
   - Brief context: why this asset class matters in the Australian market
   - Key market data (AUM, growth, market size if available)

2. MARKET CONTEXT & GROWTH
   - How the asset class has evolved in Australia
   - Key growth drivers (regulatory, institutional, market conditions)
   - Current market size and trajectory
   - Cited data from industry reports (named sources)

3. TYPES / CATEGORIES
   - Break down the asset class into its distinct sub-types
   - Each sub-type gets:
     - Name and definition
     - How it differs from other sub-types
     - Who it suits best
     - Risk level relative to other sub-types
   - Aim for 4-8 sub-types depending on the asset class

4. KEY FEATURES & BENEFITS
   - 4-6 distinct benefits, each with:
     - A clear heading
     - Explanation of why this matters to the investor
     - Supporting data or evidence where available
   - Must include: return potential, diversification benefit,
     accessibility, and any unique structural advantage

5. RISKS & CONSIDERATIONS
   - 4-8 distinct risks, each with:
     - A clear heading
     - Honest explanation of the risk (not downplayed)
     - How the risk manifests in practice
     - How it can be mitigated (if applicable)
   - Must include: market risk, liquidity risk, and any risks
     specific to this asset class
   - This section should be roughly equal in depth to the
     benefits section — balanced coverage is critical

6. COMPARISON WITH ALTERNATIVES
   - Comparison table: this asset class vs 3-4 alternatives
   - Columns: Income source, Liquidity, Risk level, Typical returns,
     Minimum investment, Best suited for
   - Brief paragraph interpreting the table

7. HOW TO EVALUATE / COMPARE [ASSET CLASS] PRODUCTS
   - 4-6 evaluation criteria specific to this asset class
   - Each criterion explained: what to look for, why it matters
   - Practical guidance, not generic ("check fees" → "compare
     management fees, performance fees, and entry/exit fees;
     typical range for this asset class is X% to Y%")

8. HOW TO INVEST
   - All available access methods in Australia:
     - Direct from fund manager
     - Through a broker/trading platform
     - Via superannuation
     - Through SMSFs (with compliance notes)
     - Via robo-advisors (if applicable)
     - Through financial advisers
   - Specific to this asset class — not generic

9. TAX CONSIDERATIONS (if substantial)
   - Australian tax treatment specific to this asset class
   - Income tax on distributions
   - Capital gains tax implications
   - SMSF-specific treatment
   - Franking credits (if applicable)
   - Reference ATO/ASIC where appropriate

10. FAQ SECTION
    - 8-14 questions
    - Questions should be the actual questions investors ask
    - Answers should be concise but complete (2-4 sentences)
    - Must cover: minimum investment, risk level, liquidity,
      tax, suitability, and fees
    - Should target Google's "People Also Ask" for the keyword

11. CONCLUSION
    - 2-3 sentence balanced summary
    - Restate the key value proposition and key risk
    - Encourage informed decision-making (not a sales push)
```

### SEO Requirements

| Element | Requirement |
|---|---|
| **Primary keyword** | "[Asset class] Australia" or "[Asset class] investments Australia" |
| **H1** | Include primary keyword naturally |
| **H2s** | Each major section should target a related keyword or question |
| **Meta title** | "[Asset Class] in Australia: Find & Compare [Asset Class] Investments" (match existing pattern) |
| **Meta description** | 150-160 chars, include primary keyword, mention compare/find |
| **FAQ schema** | Implement FAQ structured data for all FAQ questions |
| **Internal links** | Link to related asset class pages where contextually relevant (e.g., bond funds page links to income funds, cash) |
| **Word count** | 2,500 - 4,500 words for the educational section (excluding listings) |
| **Readability** | Scannable with clear H2/H3 hierarchy. Short paragraphs (3-4 sentences max). Use tables and lists to break up dense information. |

### Proof Elements & Source Requirements

Content must include:
- **At minimum 3 named data sources** (e.g., Morgan Stanley, ASIC, ABS, RBA, McKinsey, Morningstar, ASX, Bloomberg)
- **At minimum 2 specific statistics** with attribution
- **Australian regulatory references** where relevant (ASIC, APRA, ATO)
- **Comparison table** vs alternative asset classes
- **No unattributed claims** — every assertion about returns, risk levels, or market size must cite a source or be flagged [NEEDS VERIFICATION]

### CTA Guidance

Client D is a marketplace, not a fund manager. CTAs should:
- **NOT** push a specific product
- Encourage exploring the product listings on the page ("Compare [asset class] products listed on Client D")
- Encourage signing up for the newsletter
- Reference the ability to filter and compare products
- Maintain the independent, educational positioning

### Internal Linking Rules

- Link to **related asset class pages** where they share characteristics (e.g., private credit → mortgage funds → bond funds)
- Link to **relevant articles/guides** if they exist on the site
- Link to the **main investments hub** (/investments/)
- Do NOT link to specific product pages — the listings section handles that
- Internal links should feel natural within the educational content, not forced

### Quality Criteria — What "Excellent" Looks Like

An excellent asset class page:
1. **Educates completely** — a reader with basic investing knowledge could understand this asset class well enough to decide whether to research further
2. **Is balanced** — benefits and risks receive equal treatment. No cheerleading.
3. **Is data-rich** — specific numbers, named sources, market data. Not vague generalisations.
4. **Is Australian-specific** — Australian market context, Australian regulatory framework, Australian tax treatment. Not generic global content.
5. **Is structured for scanning** — clear headings, short paragraphs, tables, FAQs. An investor can find what they need without reading everything.
6. **Is differentiated** — doesn't read like every other financial education site. Includes unique comparison frameworks, addresses common misconceptions, or provides angles that competitors miss.
7. **Is current** — references recent market data, not outdated statistics.
8. **Maintains neutrality** — reads as independent research, not as a sales funnel.

### Common Mistakes to Avoid

1. **Generic introductions** — "In today's volatile market..." or "Investing is an important part of building wealth..." These waste the reader's time and signal generic AI content.
2. **US-centric content** — Referencing TIPS, 401(k)s, municipal bonds, SEC. Everything must be Australian context (SMSF, ASX, ASIC, ATO, FCS).
3. **Unbalanced coverage** — All benefits, light on risks. The existing Tier 1 pages are notably honest about risks. This must be maintained.
4. **Missing comparison framework** — The reader needs to understand how this asset class compares to alternatives. A comparison table is mandatory.
5. **Vague claims** — "Strong returns" without numbers. "Growing market" without data. Everything needs specifics.
6. **Promotional tone** — This is an independent marketplace. Content should never sound like a fund manager pitch.
7. **Missing SMSF coverage** — A significant portion of the audience are SMSF trustees. Tax and compliance implications for SMSFs should always be addressed.
8. **Thin FAQ section** — FAQs should target real investor questions and "People Also Ask" queries. Generic questions waste the opportunity.
9. **No internal links** — Every asset class page should link to related asset class pages where natural.
10. **Inconsistent depth** — The current site has pages ranging from zero educational content to 4,000+ words. All pages should target Tier 1 depth.

### Reference Examples (Benchmark Pages)

These are the current best pages on the site and represent the minimum quality target:

1. **ETFs page** (clientd.example.com/investments/exchange-traded-funds)
   - Why it's good: Comprehensive coverage of types, strategies, tax, comparison tables. Cites ASIC, ASX, MoneySmart, Canstar. Strong FAQ section. ~4,000+ words.

2. **Private Credit page** (clientd.example.com/investments/private-credit)
   - Why it's good: Strong market context with growth data. Cites Morgan Stanley, McKinsey, Russell Investments. Six distinct lending strategy types. Balanced risk coverage.

3. **Mortgage Funds page** (clientd.example.com/investments/mortgage-funds)
   - Why it's good: Excellent risk framework. Common misconceptions section (unique angle). Comparison table vs alternative income investments. ASIC regulatory reference.

### Pages Needing Content (Priority List)

**High priority — no or minimal educational content:**
- Private Equity (currently listings only)
- Property Funds (currently listings only)

**Medium priority — content exists but is thin (Tier 2):**
- Large Caps Australia
- Small Caps Australia
- Bond Funds
- Cash / Money Market
- Australian Equity Funds
- Income Funds

**Lower priority — need to assess:**
- Large Caps Global
- Property
- LICs/LITs
- Multi-Asset Portfolios
- Managed Accounts

---

## 16. RAG Ingestion Plan for Client D

### What to Ingest

1. **All 16 existing asset class pages** — even the thin ones provide voice and structure patterns
2. **Any blog articles on clientd.example.com** that relate to asset classes, investing education, or market commentary
3. **The site's About page and any brand/editorial guidelines** — for voice and positioning context

### How Chunks Will Be Tagged for This Client

Each chunk from Client D will carry:

```
{
  client_id: "investment_markets",
  topic_tags: ["private_credit", "non_bank_lending", "alternative_income"],
  keyword_tags: ["private credit Australia", "private credit funds"],
  content_type_tag: "asset_class_page",
  intent_tag: "educating_on_asset_class",
  asset_tags: ["statistic", "market_data", "risk_description", "comparison_table"],
  funnel_stage: "top_to_mid",
  source_article_title: "Private Credit in Australia: An Investor's Guide",
  source_url: "https://clientd.example.com/investments/private-credit"
}
```

### Coverage Map (After Ingestion)

```
Client D — CONTENT COVERAGE
─────────────────────────────────────────────────
Asset Class             │ Est. Chunks │ Coverage
─────────────────────────────────────────────────
ETFs                    │   30-40     │ ████████ Strong
Private Credit          │   25-30     │ ████████ Strong
Mortgage Funds          │   25-30     │ ████████ Strong
Large Caps AU           │   8-12      │ ████ Moderate
Small Caps AU           │   6-10      │ ███ Moderate
Bond Funds              │   8-12      │ ████ Moderate
Cash / Money Market     │   6-10      │ ███ Moderate
Private Equity          │   0-2       │ ▏ Minimal
Property Funds          │   0-2       │ ▏ Minimal
─────────────────────────────────────────────────
```

For asset classes with strong coverage, the system can generate content drawing heavily from existing material. For minimal coverage (Private Equity, Property Funds), the system will lean on web research and use existing content only for voice matching — which is the correct behaviour.

---

## 17. Next Steps

### Completed
- ✅ Supabase database (9 tables, seed data for Client D)
- ✅ Workflow 1: Content Ingestion (11 nodes including dedup, full Client D batch ingested)
- ✅ RAG knowledge base seeded: Client D content chunks with embeddings in Supabase
- ✅ Workflow 2: New Content Generation (24 nodes including Google Docs output)
  - Multiple test runs completed on Private Equity asset class page
  - Output quality assessed as publishable — strong data sourcing, current stats, balanced coverage
  - Google Docs output: formatted HTML doc delivered to Drive folder automatically
  - Prompt refinements: word count planning in Outline, citation discipline in Rewrite, Tavily fallback

### Immediate Next Steps

1. **Implement V2O in Workflow 2** — form + Merge Context + prompt updates (7 steps, no new DB tables):
   - Step 1: Rename "Notes" form field to "Content Brief (V2O)" with format placeholder
   - Step 2: Update Merge Context — `v2o: formData['Content Brief (V2O)'] || ''`
   - Step 3-7: Add V2O block to Research Brief, Outline, Draft, Critique, Rewrite prompts

2. **Build Workflow 3 (Content Update)** — most complex workflow. Requires:
   - GSC API OAuth setup (Client D GSC property access)
   - Stage 0a: EEAT assessment of existing page content
   - Stage 0b: GSC data pull (top queries, declining keywords, opportunities)
   - Injection of EEAT gaps + GSC data into pipeline stages 1-7
   - V2O field carries across from Workflow 2 design — same pattern

3. **Build Workflow 4 (Feedback Loop)** — simpler. Triggers when content_jobs.status = "published", re-ingests the article into RAG via Workflow 1 logic.

4. **Test additional content types** — run Workflow 2 on different content type slugs to verify the dynamic template system works across types.

### Decisions Still Open
- Review process: who approves generated content before publishing?
- GSC API OAuth credentials: need access to Client D GSC property for Workflow 3
- Additional content type schemas: need to build out schemas for blog posts, service pages etc.
