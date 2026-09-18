# Research Agent — V2

**Role:** Gather competitive SERP data, keyword intelligence, benchmark content, Reddit signals, LLM citation landscape, and web research for the target topic.

Runs in parallel with `gsc-research.md` and `rag.md`.

---

## Inputs

- `context` — full context object from Context Loader
- `topic` — e.g. "Private equity"
- `target_keywords` — array, e.g. `["private equity australia", "invest in private equity"]`
- `source_url` — optional. The existing page URL being rewritten. Required when `context.content_type.primary_intent == 'commercial'`.

Primary keyword = `target_keywords[0]`.
Client domain = extracted from `context.client.website_url` (e.g. `clientk.example.com`). Used in Phase 2 to exclude client's own pages from benchmark reading.

---

## Commercial Intent Mode

**Check at the start of Phase 2:** If `context.content_type.primary_intent == 'commercial'`, apply the following modifications:

This mode exists because service/product pages require brand-specific product knowledge, not competitor benchmarks. Sending a draft agent to write a service page using web research risks importing competitor product facts, generic descriptions, or non-Client G specifications.

**Branches that change in commercial intent mode:**

- **Branch 3 (Web Research) → REPLACED by Source URL Deep Dive:**
  Do NOT run the standard web research queries. Instead, run a targeted SQL query to pull all RAG chunks from the specific `source_url`:
  ```sql
  SELECT chunk_text, context_prefix, source_article_title, topic_tags, keyword_tags
  FROM content_chunks
  WHERE client_id = '{{context.client.id}}'
    AND source_url = '{{source_url}}'
  ORDER BY id;
  ```
  Also run a broader ILIKE fallback to capture related product chunks:
  ```sql
  SELECT chunk_text, context_prefix, source_article_title, source_url, topic_tags
  FROM content_chunks
  WHERE client_id = '{{context.client.id}}'
    AND (chunk_text ILIKE '%{{topic}}%' OR topic_tags::text ILIKE '%{{topic}}%')
    AND source_url != '{{source_url}}'
  LIMIT 15;
  ```
  Output this as `sourcePageChunks` (exact page) and `relatedProductChunks` (related Client G pages). These are the **only permitted sources for product facts, model names, features, and specifications** in the draft. Flag this clearly in the research output: "COMMERCIAL MODE — product facts sourced from Client G RAG only."

- **Branch 5 (Benchmark Article Reading) → SKIPPED entirely:**
  Do not read competitor service pages. Reason: reading competitor product pages risks importing non-Client G product descriptions, specifications, or CTAs into the draft. The draft agent must not be exposed to this content. Skip this branch and set `benchmark.articlesRead = []`, `benchmark.note = "Skipped — commercial intent mode: no competitor page reading."`.

- **Branch 4 (Audience Signals) → REFRAMED as Buyer Objections:**
  Keep this branch but reframe the goal. Do not look for general discussion about the product category. Instead, look for: specific buyer objections (durability, fitting issues, pet damage, aesthetics, cost), installation questions, and comparison questions. Reddit, Quora, and PAA data should be filtered for decision-stage signals, not early awareness questions.

- **All other branches (1, 2a–2e, 6, 7) → run as normal.** SERP data, keyword intelligence, LLM citations, and content ecosystem mapping all apply unchanged.

---

## Execution Order

**Phase 1 — run first, sequentially (Branches 1–2d).**
Phase 2 depends on SERP results (for benchmark URLs) and keyword data.

**Phase 2 — run in parallel after Phase 1 completes (Branches 3–7).**
All five branches are independent of each other.

**Phase 3 — run after Phase 2 completes (Branch 8).**
Depends on named sources found in Branch 3.

---

## Phase 1 — Keyword Intelligence + SERP

### Branch 1 — SERP Data (Expanded)

**Tool:** `mcp__dataforseo__serp_organic_live_advanced`

```json
{
  "keyword": "{{target_keywords[0]}}",
  "location_code": "{{context.client.dataforseo_location_code}}",
  "language_code": "{{context.client.language_code}}",
  "device": "desktop",
  "depth": 10
}
```

`dataforseo_location_code` and `language_code` come from the `clients` table. If not set, fall back to DataForSEO locations lookup using `context.client.market` as the search term.

Extract and structure:

**Organic results:**
- `organicResults` — top 10: position, title, url, description. Note which are from the client's own domain.
- `benchmarkCandidates` — top 3–5 results excluding the client's domain. These are the URLs for Branch 5 benchmark reading.

**SERP features (V2 expansion):**
- `featuredSnippet` — exists? Format? (paragraph / list / table). If yes, extract the content. This is the AEO target format.
- `featuredSnippetUrl` — the URL holding the snippet
- `peopleAlsoAsk` — all PAA questions (these become H3 candidates and FAQ items in the Outline)
- `videoResults` — present? Count? (informs whether to recommend a video companion)
- `adsCount` — number of ads visible (indicates commercial intent strength)
- `relatedSearches` — all related search terms

---

### Branch 2a — Keyword Overview

**Tool:** `mcp__dataforseo__dataforseo_labs_google_keyword_overview`

```json
{
  "keywords": ["{{target_keywords[0]}}"],
  "location_code": "{{context.client.dataforseo_location_code}}",
  "language_code": "{{context.client.language_code}}"
}
```

Extract: `search_volume`, `keyword_difficulty`, `cpc`, `competition_level`.

---

### Branch 2b — Trend Direction (New in V2)

**Tools:** `mcp__dataforseo__dataforseo_labs_google_historical_keyword_data` + `mcp__dataforseo__content_analysis_phrase_trends`

**Historical keyword data:**
```json
{
  "keywords": ["{{target_keywords[0]}}"],
  "location_code": "{{context.client.dataforseo_location_code}}",
  "language_code": "{{context.client.language_code}}"
}
```

**Content phrase trends:**
```json
{
  "keyword": "{{target_keywords[0]}}",
  "location_name": "{{context.client.market}}"
}
```

Extract:
- Volume trend since earliest available data (growing / stable / declining)
- Citation trend — is this topic getting more or less coverage over time?
- Derive recommendation: invest heavily / standard investment / reconsider

If no data returned (niche AU topics), note "no trend data available" and continue.

---

### Branch 2c — Search Intent

**Tool:** `mcp__dataforseo__dataforseo_labs_search_intent`

```json
{
  "keywords": ["{{target_keywords[0]}}"],
  "language_code": "{{context.client.language_code}}"
}
```

Extract: intent classification (informational / commercial / navigational / transactional), intent probability scores.

---

### Branch 2d — Related Keywords

**Tool:** `mcp__dataforseo__dataforseo_labs_google_related_keywords`

```json
{
  "keyword": "{{target_keywords[0]}}",
  "location_code": "{{context.client.dataforseo_location_code}}",
  "language_code": "{{context.client.language_code}}",
  "limit": 20
}
```

Extract top 15–20 semantically related terms: keyword + search_volume + keyword_difficulty.

---

### Branch 2e — AI Search Volume (New in V2)

**Tool:** `mcp__dataforseo__ai_optimization_keyword_data_search_volume`

```json
{
  "keywords": ["{{target_keywords[0]}}", "{{target_keywords[1] || ''}}"],
  "language_code": "{{context.client.language_code}}",
  "location_name": "{{context.client.market}}"
}
```

Extract: `ai_search_volume` — how often this keyword is queried in AI systems (ChatGPT, Google AI Overviews). Note trend across monthly data if available.

Compare against Google search volume from Branch 2a: a keyword with low Google volume but measurable AI volume is an AEO priority — the audience is already going to AI, not search.

If no data returned, note "no AI search volume data" and continue.

---

## Phase 2 — Parallel Research Branches

Run Branches 3–7 in parallel after Phase 1 completes.

---

### Branch 3 — Web Research

**Primary tool:** `mcp__dataforseo__content_analysis_search`

**Known limitation:** This tool is unreliable for niche AU keywords with <200/mo search volume. It searches all indexed content regardless of topic relevance and frequently returns off-topic results (gaming, unrelated geographies, aggregator spam). If top results are clearly off-topic, skip immediately to the Tavily or WebSearch fallback — do not attempt to salvage irrelevant results.

Run two queries:

**Query 1:** `"{{topic}} {{context.client.market}} statistics data research"`
```json
{
  "keyword": "{{topic}} {{context.client.market}} statistics data research",
  "limit": 5,
  "order_by": "citations_count,desc"
}
```
Goal: authoritative content covering this topic — industry bodies, research institutions, recognised publications.

**Query 2:** `"{{topic}} {{context.client.market}} best practices expert guide"`
```json
{
  "keyword": "{{topic}} {{context.client.market}} best practices expert guide",
  "limit": 5,
  "order_by": "citations_count,desc"
}
```
Goal: practical frameworks, expert guidance, coverage for differentiation analysis.

For each result extract: `url`, `title`, `snippet`, `citations_count`.

**Extract embedded primary source URLs:** Within each result's snippet or content, look for references to primary/authoritative sources (deloitte.com, mckinsey.com, gartner.com, ibisworld.com, abs.gov.au, government bodies, industry associations). Capture these as `primarySourceUrls[]` alongside the named source reference.

**Fallback if DataForSEO content_analysis_search returns no results:** Use Tavily MCP (`mcp__tavily__*`) with the same two queries. Truncate each result's `raw_content` to 6,000 chars.

**Fallback if Tavily is unavailable:** Use WebSearch (native) with three searches instead of two.

---

### Branch 4 — Audience Signals (Reddit + Social Fallback)

**Goal:** Find real audience questions and pain points from online discussion. Reddit is the first source — but for B2B topics, professional services, or niche markets, Reddit is often sparse. If Reddit returns fewer than 2 threads, run the fallback cascade below before returning empty.

**Step 1 — Find Reddit threads:**

**Tool:** `mcp__dataforseo__serp_organic_live_advanced`
```json
{
  "keyword": "site:reddit.com {{topic}}",
  "location_code": "{{context.client.dataforseo_location_code}}",
  "language_code": "{{context.client.language_code}}",
  "device": "desktop",
  "depth": 5
}
```

Extract top 3 Reddit thread URLs from organic results.

**Step 2 — Read top Reddit threads (if ≥ 2 results found):**

**Known limitation:** Reddit blocks content parsers — `on_page_content_parsing` returns empty `page_as_markdown` on Reddit URLs. If parsing fails, use the SERP snippets and thread titles from Step 1. Snippets contain enough signal (question themes, pain points, dominant fears) without full thread content. Do not retry failed Reddit URLs — move on.

For each of the top 2–3 Reddit URLs, attempt `mcp__dataforseo__on_page_content_parsing`:
```json
{
  "url": "{{reddit_thread_url}}",
  "enable_javascript": false
}
```

From each thread extract:
- Thread title + upvote count (if available)
- Top questions and pain points raised by commenters
- Any strong recurring themes or frustrations
- Misconceptions or debates in the thread

**Step 3 — Fallback cascade (run if Reddit returned fewer than 2 threads):**

Run these searches in order, stopping as soon as one returns ≥ 3 useful results:

**Fallback A — LinkedIn Pulse:**
Use WebSearch: `site:linkedin.com/pulse "{{topic}}" {{context.client.market}}`
Extract article titles, key themes, and questions raised in any visible comment previews.

**Fallback B — Quora:**
Use WebSearch: `site:quora.com "{{topic}}" {{context.client.market}}`
Extract question titles — these are literal audience questions in their own words.

**Fallback C — Competitor article comments:**
For the top 2 benchmark URLs from Branch 5 (or top SERP results if Branch 5 not yet complete), use Tavily or WebSearch to find the page and extract any visible discussion or comment signals.

**Fallback D — PAA as proxy:**
If all fallbacks return nothing, use `serpData.peopleAlsoAsk` questions from Branch 1 as the audience signal. Note: "Reddit/social signal not found — using PAA as audience proxy."

**Output:** A synthesised list of 5–10 real audience questions and pain points. Label the source (Reddit / LinkedIn / Quora / PAA proxy). These become content opportunities.

---

### Branch 5 — Benchmark Article Reading (New in V2)

**Goal:** Read the top-ranking competitor articles to understand table stakes, differentiation opportunities, and weaknesses to exploit.

Use `benchmarkCandidates` from Branch 1 (top 3–5 organic URLs excluding client domain).

For each benchmark URL, run `mcp__dataforseo__on_page_content_parsing`:
```json
{
  "url": "{{benchmark_url}}",
  "enable_javascript": true
}
```

If a URL fails with `enable_javascript: true`, retry with `enable_javascript: false`.

For each parsed article, extract and structure:
- **URL + title**
- **Approximate word count** (estimate from content length)
- **Heading structure** — H1, all H2s, key H3s
- **Topics covered** — the main areas addressed
- **Sources cited** — any named statistics, studies, or external authorities
- **Strengths** — what this article does well (depth, originality, specific data, practical frameworks)
- **Weaknesses / gaps** — what it misses, handles superficially, or gets wrong

After reading all benchmark articles, synthesise across them:
- **Table stakes** — topics covered by most/all benchmark articles (must be in the brief)
- **Differentiation gaps** — topics that are missing or handled weakly across the benchmark set
- **Best structural approach** — headings/depth that seem most effective across the set
- **Beat strategy** — 3–5 specific ways the content we produce will exceed the benchmark set

---

### Branch 6 — LLM Citation Landscape (New in V2)

**Goal:** Understand how AI systems currently answer the target query — which URLs they cite, what framing they use, and whether the client is mentioned.

**Note:** `ai_opt_llm_ment_top_pages` and `ai_opt_llm_ment_top_domains` require a separate subscription not currently active. Use the tools below instead — they give direct query-level citation data which is more actionable for AEO than aggregate mention counts.

**Cache check (run before any API calls):**

LLM citation landscapes change slowly — weekly caching is sufficient. Check for a recent cached result:

Cache file path: `outputs/research/llm-citations/{{client_slug}}--{{keyword_slug_2words}}.json`

Where `keyword_slug_2words` = first two words of `target_keywords[0]`, lowercased, hyphen-separated (e.g. "infrastructure etf australia" → "infrastructure-etf").

```bash
# Check if cache file exists and is < 14 days old
test -f "c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/Claude Workflow V2/outputs/research/llm-citations/{{client_slug}}--{{keyword_slug_2words}}.json"
```

- If cache file exists and was created within 14 days: use cached data, set `llmCitationsSource = "cache ({{fileDate}})"`, skip Steps 1–2 below.
- If no cache or older than 14 days: run Steps 1–2 and save the result to the cache file path above.

**Step 1 — ChatGPT scraper:**

**Tool:** `mcp__dataforseo__ai_optimization_chat_gpt_scraper`
```json
{
  "keyword": "{{target_keywords[0]}} {{context.client.market}}",
  "language_code": "{{context.client.language_code}}",
  "location_name": "{{context.client.market}}"
}
```

From the response extract:
- The full ChatGPT answer text — what framing, what angle, what questions it answers
- All cited sources: title, domain, URL
- Whether the client's domain appears in any cited source
- Which competitors are named or recommended
- Whether ChatGPT recommends the hybrid/integrated approach or a different framing

**Step 2 — Cross-check with Perplexity (optional):**

**Tool:** `mcp__dataforseo__ai_optimization_llm_response`
```json
{
  "llm_type": "perplexity",
  "model_name": "sonar",
  "user_prompt": "{{target_keywords[0]}} {{context.client.market}}",
  "web_search": true
}
```

Extract the same data points as Step 1 for comparison across AI systems.

**Synthesise:**
- **Cited URLs** — which pages are AI systems currently sending readers to?
- **Client presence** — is the client cited? If not, what type of content would earn a citation?
- **AI framing gap** — how does AI describe/frame the topic? Does our planned angle match or improve on this framing?
- **Citation opportunity** — is the citation space dominated by 2–3 strong competitors, or open?

For low-volume AU keywords, ChatGPT may not have strong local citation data. In that case, the framing analysis is still valuable — what angle AI uses to answer the query directly informs BLUF block structure.

**Save result to cache:**

After completing Steps 1–2, save the `llmCitations` output as JSON:

```bash
mkdir -p "c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/Claude Workflow V2/outputs/research/llm-citations"
```

Write `llmCitations` JSON to `outputs/research/llm-citations/{{client_slug}}--{{keyword_slug_2words}}.json`. Include a `cachedAt` field with today's date.

---

### Branch 7 — Content Ecosystem Mapping (New in V2)

**Goal:** Identify the full range of domains covering this topic — not just direct competitors.

**Known limitation:** `dataforseo_labs_google_serp_competitors` returns empty for keywords with <200/mo search volume — insufficient SERP data to build a competitor landscape. For low-volume AU keywords, skip this tool and derive the ecosystem from Branch 1 SERP organic results directly, classifying those domains by type.

**Tool:** `mcp__dataforseo__dataforseo_labs_google_serp_competitors`
```json
{
  "keywords": ["{{target_keywords[0]}}"],
  "location_code": "{{context.client.dataforseo_location_code}}",
  "language_code": "{{context.client.language_code}}",
  "limit": 20
}
```

For each domain, classify by type:
- **Direct competitors** — same business category as the client
- **Adjacent domains** — related industry covering the topic (e.g. HR platforms covering offshore staffing, insurance sites covering superannuation)
- **Authority / media** — publications, industry bodies, news sites
- **Aggregators** — directories, comparison sites

Extract: domain, estimated traffic, domain authority (if available), domain type.

These are potential citation sources and future link targets.

---

## Phase 3 — Primary Source URL Lookup

### Branch 8 — Primary Source URL Lookup

Runs after Phase 2 completes. Depends on named sources found in Branch 3.

Review all named primary sources found in Branch 3 (statistics attributed to named research firms, government bodies, industry associations, consulting firms). Identify up to **3** that:
- Are authoritative (not a competitor, not a secondary aggregator)
- Have a specific report or dataset title (e.g. "Deloitte 2024 Global Outsourcing Survey", "ABS Labour Force Survey")
- Do **not** yet have a direct URL from Branch 3

For each, run one targeted search using WebSearch: `"[exact source name and year]" site:[authoritative-domain]`

Example: `"Deloitte 2024 Global Outsourcing Survey" site:deloitte.com`

If no result found, try: `"[exact source name and year]" filetype:pdf`

**Goal:** find the direct report URL or landing page, not a secondary article about it. Extract the URL and confirm it matches the source name.

Add any confirmed URLs to `primarySourceUrls`. If nothing found after two attempts, skip — do not fabricate.

Skip this branch if Branch 3 already captured direct URLs for all key named sources.

---

## Output Format

```json
{
  "serpData": {
    "organicResults": [
      { "position": 1, "title": "...", "url": "...", "description": "...", "isClientDomain": false }
    ],
    "benchmarkCandidates": [
      { "position": 1, "url": "...", "title": "..." }
    ],
    "featuredSnippet": {
      "exists": true,
      "format": "paragraph",
      "content": "...",
      "url": "..."
    },
    "peopleAlsoAsk": ["How does private equity work in Australia?", "..."],
    "videoResults": { "present": false, "count": 0 },
    "adsCount": 3,
    "relatedSearches": ["private equity firms australia", "..."]
  },
  "keywordData": {
    "primary": {
      "keyword": "private equity australia",
      "search_volume": 4400,
      "keyword_difficulty": 42,
      "cpc": 3.20,
      "competition_level": "medium",
      "intent": "informational",
      "intent_scores": { "informational": 0.82, "commercial": 0.15, "transactional": 0.03 }
    },
    "related": [
      { "keyword": "private equity returns australia", "search_volume": 880, "keyword_difficulty": 35 }
    ],
    "trendDirection": {
      "volumeTrend": "growing",
      "citationTrend": "stable",
      "recommendation": "standard investment"
    }
  },
  "benchmark": {
    "articlesRead": [
      {
        "position": 1,
        "url": "...",
        "title": "...",
        "wordCountEstimate": 2200,
        "headings": ["H1: ...", "H2: ...", "H2: ..."],
        "topicsCovered": ["..."],
        "sourcesCited": ["..."],
        "strengths": ["..."],
        "weaknesses": ["..."]
      }
    ],
    "tableStakes": ["Topics all/most benchmark articles cover — must include"],
    "differentiationGaps": ["Topics missing or handled weakly across the benchmark set"],
    "beatStrategy": [
      "Specific way 1 the content will exceed the benchmark",
      "Specific way 2",
      "Specific way 3"
    ]
  },
  "redditSignals": {
    "threadsFound": 3,
    "audienceQuestions": [
      "Real question raised in Reddit thread 1",
      "Real pain point from thread 2"
    ],
    "keyThemes": ["Theme 1", "Theme 2"],
    "note": "Low Reddit volume — only 1 thread found, limited signal"
  },
  "llmCitations": {
    "topPages": [
      { "url": "...", "title": "...", "mentionCount": 42 }
    ],
    "topDomains": [
      { "domain": "...", "mentionCount": 87 }
    ],
    "clientPresent": false,
    "assessment": "contested / open opportunity / no data available"
  },
  "contentEcosystem": {
    "directCompetitors": [{ "domain": "...", "domainType": "direct competitor" }],
    "adjacentDomains": [{ "domain": "...", "domainType": "adjacent" }],
    "authorityMedia": [{ "domain": "...", "domainType": "authority/media" }]
  },
  "webResearch": {
    "statistics": [
      { "url": "...", "title": "...", "snippet": "...", "citationsCount": 14, "namedSources": ["SEEK Salary Insights 2025"] }
    ],
    "bestPractices": [
      { "url": "...", "title": "...", "snippet": "..." }
    ],
    "primarySourceUrls": [
      { "sourceName": "Deloitte 2024 Global Outsourcing Survey", "url": "https://www.deloitte.com/..." },
      { "sourceName": "ABS Labour Force Survey", "url": "https://www.abs.gov.au/..." }
    ]
  }
}
```

---

## Notes for Downstream Agents

Include this summary block in the output for use by Research Brief and Outline:

```
KEYWORD CONTEXT:
- Volume: {{search_volume}}/mo | KD: {{keyword_difficulty}} | Intent: {{intent}}
- KD interpretation: [Low <30 / Medium 30-60 / High 60+]
- At KD {{keyword_difficulty}}: [describe what this means for required depth/authority]
- Search intent is {{intent}}: [note any content type mismatches]
- Trend direction: [growing / stable / declining] — [recommendation]
- Top PAA questions to address: [list top 5]
- Semantic terms to cover: [list top 10 related keywords]

BENCHMARK SUMMARY:
- Articles read: [count] (positions [list positions])
- Table stakes (must cover): [list]
- Key gaps to fill: [list top 3]
- Beat strategy: [list top 3 specific ways]

REDDIT SIGNALS:
- Top audience questions: [list top 5, or "low volume — limited signal"]

LLM CITATION LANDSCAPE:
- Citation leaders: [top 2 domains, or "no data available"]
- Client present: [yes / no]
- Opportunity: [contested / open]
```

This block travels with the research data so Research Brief, Outline, and Draft agents don't need to re-interpret raw data.
