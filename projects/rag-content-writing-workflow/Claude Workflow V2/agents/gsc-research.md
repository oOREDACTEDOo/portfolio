# GSC Research Agent

**Role:** Pull the client's own Google Search Console data for the target topic. Identifies near-ranking opportunities, existing content (cannibalism risk), and query gaps.

Runs in parallel with `research.md` and `rag.md`.

---

## Inputs

- `context` — full context object (needs `context.client.gsc_property_id`)
- `topic` — e.g. "Private equity"
- `target_keywords` — array

GSC property: `{{context.client.gsc_property_id}}`

---

## Query 1 — Near-Ranking Queries on This Topic

**Tool:** `mcp__gsc-local__get_search_analytics`

Pull queries related to the topic where the client is in positions 6–20 (visible but not converting).

```json
{
  "siteUrl": "{{context.client.gsc_property_id}}",
  "startDate": "{{90_days_ago}}",
  "endDate": "{{today}}",
  "dimensions": ["query"],
  "dimensionFilterGroups": [{
    "filters": [{
      "dimension": "query",
      "operator": "contains",
      "expression": "{{topic_keyword}}"
    }]
  }],
  "rowLimit": 50
}
```

Filter results to positions 6–20 with impressions > 50. Sort by impressions descending.

These are keywords where new content could quickly rank if targeted properly.

---

## Query 2 — Existing Pages Ranking on This Topic

**Tool:** `mcp__gsc-local__get_search_by_page_query`

Find if the client already has a page ranking for the target keyword — cannibalism risk.

```json
{
  "siteUrl": "{{context.client.gsc_property_id}}",
  "startDate": "{{90_days_ago}}",
  "endDate": "{{today}}",
  "dimensions": ["page", "query"],
  "dimensionFilterGroups": [{
    "filters": [{
      "dimension": "query",
      "operator": "contains",
      "expression": "{{target_keywords[0]}}"
    }]
  }],
  "rowLimit": 20
}
```

If any existing page ranks for the primary keyword:
- Flag as CANNIBALISM_RISK: true
- Include the URL and its position
- Note: new content should be differentiated enough to avoid splitting ranking signals, or the existing page should be updated instead

---

## Query 3 — Top Performing Content (Format Signals)

**Tool:** `mcp__gsc-local__get_performance_overview`

Pull top 10 pages by clicks for the client over 90 days.

```json
{
  "siteUrl": "{{context.client.gsc_property_id}}",
  "startDate": "{{90_days_ago}}",
  "endDate": "{{today}}",
  "dimensions": ["page"],
  "rowLimit": 10
}
```

This reveals which content types are performing best for this client. If long-form guides dominate — that format works for this client's audience.

---

## Output Format

```json
{
  "gscData": {
    "property": "{{context.client.gsc_property_id}}",
    "dateRange": "90 days to today",
    "nearRankingQueries": [
      {
        "query": "near-ranking query related to topic",
        "position": 11.2,
        "impressions": 320,
        "clicks": 4,
        "ctr": 0.012
      }
    ],
    "cannibalismRisk": {
      "flagged": false,
      "existingPages": []
    },
    "topPerformingPages": [
      { "page": "{{context.client.website_url}}/top-page", "clicks": 840, "position": 4.2 }
    ],
    "summary": "Narrative summary of near-ranking opportunities, cannibalism status, and top content format signals."
  }
}
```

---

## Notes for Downstream Agents

The `summary` field is the most important output — include it in the Research Brief. The near-ranking queries should inform:
- Outline agent: add sections or subsections that target these queries
- Draft agent: ensure semantic coverage of near-ranking query terms
- The cannibalism flag should be surfaced in the Coverage Check report
