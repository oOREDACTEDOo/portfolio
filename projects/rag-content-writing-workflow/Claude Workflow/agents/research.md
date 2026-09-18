# Research Agent

**Role:** Gather competitive SERP data, keyword intelligence, and web research for the target topic.

Runs in parallel with `gsc-research.md` and `rag.md`.

---

## Inputs

- `context` — full context object from Context Loader
- `topic` — e.g. "Private equity"
- `target_keywords` — array, e.g. `["private equity australia", "invest in private equity"]`

Primary keyword = `target_keywords[0]`.

---

## Branch 1 — SERP Data

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
- `organicResults` — top 10: title, url, description, position
- `peopleAlsoAsk` — all PAA questions
- `relatedSearches` — all related search terms

---

## Branch 2a — Keyword Overview

**Tool:** `mcp__dataforseo__dataforseo_labs_google_keyword_overview`

```json
{
  "keywords": ["{{target_keywords[0]}}"],
  "location_code": 2036,
  "language_code": "en"
}
```

Extract: `search_volume`, `keyword_difficulty`, `cpc`, `competition_level`.

---

## Branch 2b — Search Intent

**Tool:** `mcp__dataforseo__dataforseo_labs_search_intent`

```json
{
  "keywords": ["{{target_keywords[0]}}"],
  "language_code": "en"
}
```

Extract: intent classification (informational / commercial / navigational / transactional), intent probability scores.

---

## Branch 2c — Related Keywords

**Tool:** `mcp__dataforseo__dataforseo_labs_google_related_keywords`

```json
{
  "keyword": "{{target_keywords[0]}}",
  "location_code": 2036,
  "language_code": "en",
  "limit": 20
}
```

Extract top 15–20 semantically related terms: keyword + search_volume + keyword_difficulty.

---

## Branch 3 — Web Research

**Tool:** Tavily MCP (`mcp__tavily__*`)

Tavily returns full page `raw_content` — truncate each result to 6,000 chars to avoid token bloat. This is significantly richer than snippets and is the preferred research source.

> **Fallback:** If Tavily MCP is unavailable, use WebSearch (Claude's native web search) with three searches instead of two to compensate for snippet-only results.

Run two searches:

**Search 1:** `"{{topic}} {{context.client.market}} statistics data research"`
- Goal: find specific statistics and data from authoritative, primary sources — industry bodies, research institutions, recognised publications.
- Extract: specific figures, percentages, named studies, source URLs.

**Search 2:** `"{{topic}} {{context.client.market}} best practices expert guide"`
- Goal: practical frameworks, expert guidance, competitor coverage for differentiation analysis, and named organisations or consultancies covering this topic.
- Extract: key arguments, frameworks, named sources, any statistics not found in Search 1.

For each result extract: `url`, `title`, `raw_content` (truncated to 6,000 chars). Flag any result containing a named statistic or primary source reference.

**Extract embedded primary source URLs:** Within each result's raw_content, look for hyperlinks or explicit URLs pointing to primary/authoritative sources (e.g. deloitte.com, mckinsey.com, gartner.com, ibisworld.com, abs.gov.au, government bodies, industry associations). Capture these as `primarySourceUrls[]` alongside the named source reference. These are the direct source URLs — not the URL of the page you fetched.

Return top 3–5 results from each search.

---

## Branch 4 — Primary Source URL Lookup

After Branch 3, review all named primary sources found (statistics attributed to named research firms, government bodies, industry associations, consulting firms). Identify up to **3** that:
- Are authoritative (not a competitor, not a secondary aggregator)
- Have a specific report or dataset title (e.g. "Deloitte 2024 Global Outsourcing Survey", "ABS Labour Force Survey")
- Do **not** yet have a direct URL from Branch 3

For each, run one targeted Tavily search: `"[exact source name and year]" site:[authoritative-domain]`

Example: `"Deloitte 2024 Global Outsourcing Survey" site:deloitte.com`

If no result found via site search, try: `"[exact source name and year]" filetype:pdf OR press release`

**Goal:** find the direct report URL or landing page, not a secondary article about it. Extract the URL and confirm it matches the source name.

Add any confirmed URLs to `primarySourceUrls` in the output. If nothing found after two attempts, skip — do not fabricate.

Skip this branch entirely if Branch 3 already captured direct URLs for all key named sources.

---

## Output Format

```json
{
  "serpData": {
    "organicResults": [
      { "position": 1, "title": "...", "url": "...", "description": "..." }
    ],
    "peopleAlsoAsk": ["How does private equity work in Australia?", "..."],
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
    ]
  },
  "webResearch": {
    "statistics": [
      { "url": "...", "title": "...", "snippet": "...", "namedSources": ["e.g. SEEK Salary Insights 2025"] }
    ],
    "competitors": [
      { "url": "...", "title": "...", "snippet": "..." }
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
- Top PAA questions to address: [list top 5]
- Semantic terms to cover: [list top 10 related keywords]
```

This block travels with the research data so Outline and Draft agents don't need to re-interpret raw numbers.
