# V2 Pipeline Plan
_Created 2026-03-23 — based on Fitz meeting + full tool audit_

---

## What's Driving V2

V1 produces solid, well-structured content. The gap Fitz identified: the pipeline doesn't explicitly establish what "the best version of this content" looks like before it starts writing. Without a named benchmark, there's no quality floor — and no way to demonstrate the output beats what's already out there.

V2 fixes this by restructuring the front end of the pipeline:
- Research produces richer output (benchmark, engagement signals, content ecosystem, LLM citation landscape)
- Research saves as a readable artifact (Google Doc) per run — reviewable without stopping the pipeline
- Critique explicitly compares against the benchmark, not just abstract E-E-A-T criteria

Everything else — the 15 agents, the database design, the output format, the Google Doc deliverable — stays largely the same.

---

## What's New in V2

### 1. Benchmark Identification + Article Reading

**What it does:** Identifies the single best-ranking piece of content for the target keyword and actually reads it — not just notes its URL.

**Tool:** `mcp__dataforseo__on_page_content_parsing` on the #1 organic result from the SERP.

**Output:**
- Benchmark URL + title
- Word count, heading structure, content depth
- What sources they cite
- What angles they cover well
- Where they're weak or thin
- Estimated traffic (from SERP data)

**Why this matters:** Currently the pipeline knows who's ranking but has never read what they wrote. This is the foundation of the "how do we beat it" strategy.

**Option A (recommended):** Parse top 1 result only — focused, fast
**Option B:** Parse top 3 — richer picture, slower, more token-heavy

---

### 2. Reddit + Engagement Signals

**What it does:** Finds real audience conversations on the topic — what people are actually asking, debating, struggling with. Also measures whether existing content is generating engagement (shares, citations) or just ranking quietly.

**Tools:**
- **Tavily** with `include_domains: ["reddit.com"]` — surfaces Reddit threads on the topic with upvote/comment context
- **`mcp__dataforseo__content_analysis_search`** — finds articles mentioning the topic across the web with social share counts, citation frequency, sentiment

**Output:**
- Top Reddit threads: title, upvotes, comment count, key questions/pain points raised
- Most-cited articles on the web for this topic (by external link count)
- Social share leaders — what content is actually spreading?
- Recurring audience questions not answered by top SERP results

**Why this matters:** Rankings tell you what Google rewards. Reddit tells you what people actually care about. These two often don't fully overlap — the gap is a content opportunity.

---

### 3. LLM Citation Landscape (AEO Intelligence — new territory)

**What it does:** Checks which domains and pages are being cited by AI systems (ChatGPT, Google AI Overviews) when users ask about this topic.

**Tools:**
- `mcp__dataforseo__ai_opt_llm_ment_top_pages` — specific pages most cited by AI for this keyword
- `mcp__dataforseo__ai_opt_llm_ment_top_domains` — domains most cited by AI in this topic space

**Output:**
- Top 5 pages being cited by AI for the target keyword
- Top 5 domains dominating AI citations in this content area
- Whether the client's existing content appears in AI citations
- Gap: is anyone being cited, or is there an open opportunity?

**Why this matters:** V1 was built for Google ranking. AI-generated answers are now a meaningful traffic channel. This data tells us whether the content we're about to produce has a realistic path to AI citation — and what the existing citation leaders are doing that we should match or beat.

**Note:** This is genuinely differentiated. No current competitor in the AU digital marketing space is building this into their content workflow.

---

### 4. Trend Direction

**What it does:** Checks whether the target keyword is growing, stable, or declining — informs how much to invest and whether the content angle should be forward-looking or evergreen.

**Tools:**
- `mcp__dataforseo__dataforseo_labs_google_historical_keyword_data` — volume trend since 2021
- `mcp__dataforseo__content_analysis_phrase_trends` — citation frequency trend for the topic

**Output:**
- Volume trend line (growing / stable / declining)
- Citation trend — is this topic getting more or less coverage over time?
- Recommendation: invest heavily / standard investment / reconsider

---

### 5. Content Ecosystem Mapping

**What it does:** Identifies who else is covering this topic beyond direct competitors — insurance companies covering superannuation, HR platforms covering offshore staffing, etc. Finds the crossover content landscape.

**Tool:** `mcp__dataforseo__dataforseo_labs_google_serp_competitors` — all domains ranking for the keyword, not just the top 5.

**Output:**
- Full domain list ranking for the keyword
- Domain types: direct competitors / adjacent domains / authority sites / media
- Crossover domains worth noting (these are potential citation sources and link targets)

---

### 6. SERP Feature Map (expanded from V1)

**What it does:** V1 already calls the SERP but doesn't fully mine what features are present. V2 explicitly maps the SERP landscape.

**Tool:** `mcp__dataforseo__serp_organic_live_advanced` (already used in V1 — just extracting more from it)

**Output:**
- Featured snippet: exists? Format? (paragraph / list / table) — this is the AEO target format
- People Also Ask questions — these become H3s and FAQ items in the outline
- Video results present? (informs whether to recommend a video companion)
- Number of ads — indicates commercial intent strength
- Top 10 domains — for ecosystem map above

---

## Research Artifact — Google Doc per Run

Every pipeline run saves a Research Brief Google Doc to the client's Drive folder before content production begins.

**Location:** Client Drive folder (same as article deliverable)
**Title:** `[Client] — Research Brief: [Topic] — [Date]`
**Format:** HTML import (same as article)

**Sections:**
1. Job overview (client, topic, keyword, date)
2. Keyword data (volume, KD, intent, trend direction)
3. SERP snapshot (top 10, features present, PAA questions)
4. Benchmark article (URL, summary, word count, strengths, weaknesses)
5. How we plan to beat it (strategy statement — written by Claude)
6. Engagement signals (Reddit threads, most-cited content)
7. LLM citation landscape (who AI is citing, gap assessment)
8. Content ecosystem (who else covers this topic)
9. Recommended content angles / H2 structure (feeds directly into Outline)

The pipeline continues automatically after saving this doc. No manual approval gate needed — the artifact is there to inspect when you want it.

---

## Changes to Existing Agents

### research.md — Expanded branches
Current: 4 branches (keyword data, GSC, web research, primary source URLs)
V2: 7 branches

| Branch | What | Tool |
|--------|------|------|
| 1 | Keyword data (unchanged) | DataForSEO keyword overview |
| 2a | GSC near-ranking + cannibalism (unchanged) | GSC MCP |
| 2b | Trend direction (new) | historical_keyword_data + content_analysis_phrase_trends |
| 3 | Web research (unchanged) | Tavily primary / WebSearch fallback |
| 4 | Reddit engagement (new) | Tavily site:reddit.com |
| 5 | Benchmark article reading (new) | on_page_content_parsing on #1 SERP result |
| 6 | LLM citation landscape (new) | ai_opt_llm_ment_top_pages + top_domains |
| 7 | Primary source URLs (unchanged, renumbered) | Targeted site: searches |

Branches 3, 4, 5, 6 run in parallel after Branch 1 + 2 complete.

### research-brief.md — Fuller output + Google Doc save

V1: synthesises research into a brief that feeds the Outline agent
V2: same synthesis + adds benchmark assessment section + "how to beat it" strategy + saves as Google Doc

New sections added to brief output:
- `benchmark` — named article, assessment, word count, structural notes, weaknesses
- `beatStrategy` — 3-5 specific ways the V2 content will exceed the benchmark
- `llmCitationGap` — whether the LLM citation landscape has an open opportunity
- `redditInsights` — top questions/pain points from Reddit threads
- `trendDirection` — growing / stable / declining + recommendation

### critique.md — Benchmark comparison field

V1: scores against abstract E-E-A-T criteria
V2: adds one explicit criterion:

> **Dimension 10 — Benchmark Comparison**
> Does this article demonstrably exceed the benchmark identified in the research brief?
> Evaluate: depth, source quality, originality of angle, structural completeness, answer quality.
> Score 1–10. If score < 7, Gap Research is mandatory — identify specifically what the benchmark does better.

### orchestrator.md — Updated stage flow

Add Stage 0.5: Research Brief save (Google Doc) after research phases complete, before Coverage Check.

---

## What Stays the Same

- Context Loader — unchanged
- RAG agent — unchanged
- GSC Research agent — unchanged
- Coverage Check — unchanged
- Outline — unchanged (PAA questions from SERP now feed in more explicitly)
- Draft — unchanged
- Gap Research — unchanged
- Rewrite — unchanged
- Deliverables — unchanged
- Fact Check — unchanged
- Output — unchanged (article Google Doc production)
- All prompts (eeat-criteria, seo-aeo-standards, system-base, voice-injection) — unchanged
- Database schema — unchanged
- Client-agnostic design — unchanged

---

## Open Questions / Decisions Needed

**1. Benchmark reading depth**
Parse top 1 result only (fast, clean) or top 3 (richer but heavier)?
Recommendation: top 1 to start. Can expand if outputs feel thin.

**2. Reddit signal quality**
Tavily's Reddit search via `include_domains` is reliable but gives snippets, not full threads. For topics with low Reddit volume, this may return nothing useful.
Option: fall back gracefully — if <2 Reddit results, note it in the brief and move on. Don't block the pipeline.

**3. LLM citation data availability**
DataForSEO's AI optimization tools are newer and may not have data for all keyword niches (especially niche AU topics).
Option: treat as best-effort. If no data returned, note "no AI citation data available" in brief.

**4. Research Brief Google Doc — separate or inline?**
Option A: Save as a separate Google Doc (clean, easy to share with Fitz)
Option B: Include research summary section at the top of the article Google Doc
Recommendation: Option A — separate doc keeps the article clean.

**5. Phasing**
Do all 7 branches at once, or phase the new branches in?
Recommendation: Phase 1 — add benchmark reading + Reddit (highest value, lowest risk). Phase 2 — add LLM citations + trend data. This lets us test and validate the new branches before layering in more complexity.

---

## Implementation Order

1. `agents/research.md` — add branches 4 (Reddit), 5 (benchmark reading), 6 (LLM citations), 2b (trend)
2. `agents/research-brief.md` — add benchmark + beatStrategy + llmCitationGap + redditInsights sections + Google Doc save step
3. `agents/critique.md` — add Dimension 10 (benchmark comparison)
4. `agents/orchestrator.md` — add Stage 0.5, update stage references for richer research output
5. Test on Client K / so-blog-post topic
