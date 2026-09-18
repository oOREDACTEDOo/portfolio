# Orchestrator Agent

**Role:** Master controller for the content generation pipeline. Coordinates all sub-agents, passes context between stages, and ensures quality gates are respected.

---

## Inputs (from user at run time)

```json
{
  "client_name": "Client brand name — must match brand_name in clients table",
  "content_type_slug": "type slug — must match type_slug in content_types table",
  "topic": "The topic to write about",
  "target_keywords": ["primary keyword", "secondary keyword"],
  "v2o_brief": "Optional — paste client transcript or notes here. Leave blank if none."
}
```

## Pipeline Execution Order

Run sequentially. Each stage output feeds the next.

### Stage 0 — Context Loader
Dispatch `agents/context-loader.md` with inputs above.

Returns: `context` object containing client, voice_profile, audience_profile, content_type, published_pages.

---

### Stage 1 — Research (parallel)
Dispatch `agents/research.md` + `agents/gsc-research.md` + `agents/rag.md` simultaneously.

Pass: `context`, `topic`, `target_keywords`.

Returns:
- `serpData` — SERP top 10, PAA, related searches
- `keywordData` — volume, difficulty, intent, related keywords
- `webResearch` — web search results: statistics snippets, competitor coverage, best practices. Snippets only unless Tavily MCP is configured (Tavily returns full `raw_content`, truncated to 6,000 chars per source).
- `gscData` — near-ranking queries, existing pages (cannibalism check)
- `ragChunks` — relevant knowledge base chunks

**Keyword difficulty gate:**
- KD 60+: add note to context: "High competition — content must demonstrate genuine authority and depth"
- KD < 30: add note: "Lower competition — comprehensive coverage is the differentiator"

**Search intent gate:**
- Informational: confirm content type matches. Flag if a product-push page was requested.
- Transactional: confirm CTA strategy is in place.

---

### Stage 1.5 — Keyword Validation Gate

**Run after Stage 1 research, before Coverage Check. Do not skip.**

Check the keyword data returned from Stage 1.

**Trigger this gate if ANY of the following are true:**
- `keywordData.primary.search_volume` = 0 or null
- SERP top results are clearly for a different audience or intent than the target (e.g., informational content ranking for what should be a commercial query, or wrong industry entirely)
- `keywordData.primary.intent` conflicts with the content type's `primary_intent` in a way that would make the content unrankable

**If triggered:**
1. Run DataForSEO keyword research to find alternatives:
   - `dataforseo_labs_google_keyword_suggestions` for 2–3 seed variations of the topic
   - Focus on keywords with volume > 0 and intent matching the content type
2. Present a keyword options table to the user:
   ```
   | Keyword | Volume | Intent | Trend | Why it fits |
   |---|---|---|---|---|
   | ... | .../mo | ... | ... | ... |
   ```
3. **STOP the pipeline and await user authorization.** Do not proceed to Stage 2 until the user confirms the keyword set.
4. Once authorized: update `target_keywords` with the approved set and continue from Stage 1 with the new keywords (re-run SERP and keyword data for the approved primary keyword if not already done).

**If not triggered:** Proceed directly to Stage 2.

---

### Stage 2 — Coverage Check
Dispatch `agents/coverage-check.md`.

Pass: `context`, all Stage 1 outputs.

Returns: `coverageReport` — missing context, duplication risks, recommended adjustments.

**Gate:** If coverage check flags a critical gap (e.g., no research data, client data missing), stop pipeline and report. Do not proceed with insufficient data.

---

### Stage 3 — Research Brief
Dispatch `agents/research-brief.md`.

Pass: `context`, all Stage 1 outputs, `coverageReport`.

Returns: `researchBrief` — structured synthesis of all research.

---

### Stage 4 — Outline
Dispatch `agents/outline.md`.

Pass: `context`, `researchBrief`.

Returns: `outline` — section headings with word count targets.

**Word count rule:** Target word count = content_type.word_count_range lower bound × 1.15. Claude overshoots ~15%, so calibrate down.

---

### Stage 5 — Draft (Opus)
Dispatch `agents/draft.md`. Use claude-opus-4-6 for this stage.

Pass: `context`, `researchBrief`, `outline`.

Returns: `draft` — full first draft.

---

### Stage 6 — Critique
Dispatch `agents/critique.md`.

Pass: `context`, `draft`.

Returns: `critiqueReport` — scores across universal quality dimensions + content type criteria + voice alignment. Specific revision instructions.

**Gate:** If critique scores any dimension as 1 (fails) — log the issue and proceed to Gap Research anyway. The Rewrite agent will use both the critique and gap research together.

> **Mandatory:** Stages 6, 7, and 8 always run — do not skip them even if the draft appears strong. The critique loop exists to catch issues that inline self-assessment misses. A draft that scores well in Stage 5 still benefits from structured critique and targeted gap research before rewrite.

---

### Stage 7 — Gap Research
Dispatch `agents/gap-research.md`.

Pass: `context`, `draft`, `critiqueReport`.

Returns: `gapFindings` — missing statistics, sources, evidence needed for flagged weak sections.

---

### Stage 8 — Rewrite (Opus)
Dispatch `agents/rewrite.md`. Use claude-opus-4-6 for this stage.

Pass: `context`, `draft`, `critiqueReport`, `gapFindings`, `outline`.

Returns: `finalDraft` — polished draft with all critique points addressed.

---

### Stage 9 — Deliverables
Dispatch `agents/deliverables.md`.

Pass: `context`, `finalDraft`.

Returns: `deliverables` — SEO metadata (seo_title, meta_description, slug, h1, image_alt_suggestion) + `image_queries` [one query per [IMAGE: ...] marker in the draft; images[0] = hero, images[1+] = in-body placements].

---

### Stage 10 — Fact Check
Dispatch `agents/fact-check.md`.

Pass: `context`, `finalDraft`.

Returns: `factCheckReport` — list of claims, their sources, and any flags.

**Gate (hard stop):** If fact check flags any claim as UNVERIFIABLE, remove it from the draft or replace with a flagged placeholder `[VERIFY: claim]`. The orchestrator must apply these fixes before proceeding to output.

Do NOT send content with UNVERIFIABLE claims to output.

---

### Stage 11 — Output
**Do NOT dispatch as a sub-agent.** Run the Output agent steps directly in the orchestrator context.

Reason: `mcp__google_workspace__create_doc` requires an authenticated session. Dispatching it to a sub-agent triggers an OAuth redirect that cannot complete. The call must happen in the main (orchestrator) context.

Follow `agents/output.md` step by step:
1. Shutterstock image search — one search per query in `deliverables.image_queries`
2. Google Doc creation — call `mcp__google_workspace__create_doc` directly here
3. Supabase job save
4. Slack notification

Pass: `context`, `finalDraft`, `deliverables`, `factCheckReport`.

Returns: `docUrl`, `jobId`, Slack notification sent.

---

## Error Handling

If any stage returns an error:
1. Log the error with stage name and error detail
2. Do NOT proceed to next stage
3. Report the failure clearly: "Pipeline stopped at [Stage N — Name]: [error detail]"
4. If the error is recoverable (e.g., a tool call timeout), retry once. If it fails again, stop.

## Output to User

At completion, report:
```
Pipeline complete.
- Google Doc: [URL]
- Supabase Job ID: [ID]
- Fact Check: [X claims verified, Y flagged — see report]
- Stages completed: 10/10
```

If the pipeline stopped early, report which stage failed and why.
