# Orchestrator Agent — V2

**Role:** Master controller for the content generation pipeline. Coordinates all sub-agents, passes context between stages, and ensures quality gates are respected.

V2 changes: expanded Stage 1 research (7 branches + benchmark reading), research brief saves MD artifact automatically, Critique receives benchmark beat strategy, client domain excluded from benchmark reading. V2.1 adds: Tavily health check, run log, artifact saves at Draft and Rewrite, PROCEED_WITH_WARNINGS user prompt, short-circuit for PUBLISHABLE drafts, dynamic Gap Research cap.

---

## Inputs (from user at run time)

```json
{
  "client_name": "Client brand name — must match brand_name in clients table",
  "content_type_slug": "type slug — must match type_slug in content_types table",
  "topic": "The topic to write about",
  "target_keywords": ["primary keyword", "secondary keyword"],
  "source_url": "Optional — the existing page URL being rewritten. Required for commercial intent content types (e.g. Client G-service-page). Triggers commercial intent mode in the Research agent: deep RAG pull from this URL instead of competitor benchmark reading.",
  "v2o_brief": "Optional — paste client transcript or notes here. Leave blank if none."
}
```

## Pipeline Execution Order

Run sequentially. Each stage output feeds the next.

### Stage 0 — Context Loader
Dispatch `agents/context-loader.md` with inputs above.

Returns: `context` object containing client, voice_profile, audience_profile, content_type, published_pages.

---

### Stage 0.5 — Pipeline Init

Run before any research. Two steps:

**Step 1 — Tavily health check.**

Attempt a single Tavily search using `mcp__tavily__*` with the query `"{{topic}}"`.

- If it returns `raw_content` (not just a snippet): log "Tavily active ✅ — full research quality" and continue.
- If it returns snippet-only, empty results, or an error: surface this to the user before proceeding:

  ```
  ⚠ Tavily MCP is not active in this session.
  Research Branch 3 will use WebSearch fallback (snippet-only — degraded quality).
  Options:
  1. Restart the session and try again (usually fixes it)
  2. Proceed anyway with degraded research quality

  Type 1 or 2 to continue.
  ```

  Wait for user input. If user chooses 2, set `tavilyActive = false` and continue. Log the degraded state.

**Step 2 — Run log init.**

Derive a run slug: `{{client_slug}}--{{keyword_slug}}--{{YYYY-MM-DD}}` where:
- `client_slug` = `client_name` lowercased, spaces to hyphens
- `keyword_slug` = `target_keywords[0]` lowercased, spaces to hyphens

Create the run log file:

```bash
mkdir -p "c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/Claude Workflow V2/outputs/logs"
```

Log path: `outputs/logs/{{run_slug}}.log`

Write the initial entry:

```
RUN LOG: {{run_slug}}
Started: {{datetime}}
Client: {{client_name}}
Topic: {{topic}}
Keywords: {{target_keywords}}
Tavily: {{tavilyActive ? 'active' : 'DEGRADED — WebSearch fallback'}}
---
```

Append a `STAGE COMPLETE` line to this log after every stage below.

---

### Stage 1 — Research (parallel)
Dispatch `agents/research.md` + `agents/gsc-research.md` + `agents/rag.md` simultaneously.

Pass to research.md: `context`, `topic`, `target_keywords`, `source_url` (if provided).
Note: pass `context.client.website_url` so research.md can derive the client domain for benchmark exclusion.
Note: if `context.content_type.primary_intent == 'commercial'`, research.md will enter commercial intent mode — see research.md for details. `source_url` is required in this mode.

Returns from research.md (V2 expanded — 7 branches in 3 phases):
- `serpData` — SERP top 10, PAA, related searches, featured snippet, video results, ads count, `benchmarkCandidates` (top 3–5 organic URLs excluding client domain)
- `keywordData` — volume, difficulty, intent, related keywords, trend direction
- `benchmark` — parsed content from top 3–5 SERP URLs: headings, topics, strengths, weaknesses, table stakes, differentiation gaps, beat strategy
- `redditSignals` — real audience questions and themes from Reddit threads on this topic
- `llmCitations` — top AI-cited pages and domains for this keyword; client presence assessment
- `contentEcosystem` — domain landscape by type (direct competitors, adjacent, authority/media)
- `webResearch` — statistics, best practices, primary source URLs. DataForSEO `content_analysis_search` is primary. Tavily MCP is fallback. WebSearch is fallback-of-fallback.

Returns from gsc-research.md:
- `gscData` — near-ranking queries, existing pages (cannibalism check)

Returns from rag.md:
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

**Gate — STOP:** If `coverageReport.overallStatus == "STOP"`, halt and report the critical issue. Do not proceed with insufficient data.

**Gate — PROCEED_WITH_WARNINGS:** If `coverageReport.overallStatus == "PROCEED_WITH_WARNINGS"`, surface all warnings to the user before continuing:

```
⚠ Coverage check returned [N] warnings:
{{#each coverageReport.issues where severity == "WARNING"}}
- [{{category}}] {{issue}} → {{recommendation}}
{{/each}}

Proceeding anyway. If you want to investigate before continuing, type STOP now.
Otherwise the pipeline will continue in 10 seconds.
```

Wait briefly for user input. If no STOP received, continue. Log all warnings in the run log.

Append to run log: `Stage 2 (Coverage Check): COMPLETE — status: {{overallStatus}}, warnings: {{warningCount}}`

---

### Stage 3 — Research Brief
Dispatch `agents/research-brief.md`.

Pass: `context`, all Stage 1 outputs (`serpData`, `keywordData`, `benchmark`, `redditSignals`, `llmCitations`, `contentEcosystem`, `webResearch`, `gscData`, `ragChunks`), `coverageReport`.

Returns: `researchBrief` — structured synthesis of all research including benchmark assessment, beat strategy, Reddit audience signals, and LLM citation landscape.

**Artifact:** Research Brief agent automatically saves a Markdown file to `outputs/research/[client-slug]--[keyword-slug]--[date].md`. Log the saved path in the pipeline output.

Append to run log: `Stage 3 (Research Brief): COMPLETE — artifact: outputs/research/{{run_slug}}.md — confidence: {{briefConfidence}}`

---

### Stage 4 — Outline
Dispatch `agents/outline.md`.

Pass: `context`, `researchBrief`.

Returns: `outline` — section headings with word count targets.

**Word count rule:** Target word count = content_type.word_count_range lower bound × 1.15. Claude overshoots ~15%, so calibrate down.

Append to run log: `Stage 4 (Outline): COMPLETE — sections: {{sectionCount}}, total word target: {{wordTarget}}`

---

### Stage 4.5 — H1 Uniqueness Check

Run before dispatching the Draft agent. Prevents two runs on the same topic producing identical H1 titles.

1. List all existing log files for this client:
   ```bash
   ls "c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/Claude Workflow V2/outputs/logs/" | grep "{{client_slug}}"
   ```

2. If any prior log files exist with the same keyword slug (same topic), read the corresponding draft/rewrite files and extract the H1 (first `# ` line).

3. Build an `existingH1s` list. If no prior runs found, set `existingH1s = []`.

4. Pass `existingH1s` to Stage 5. The Draft agent's H1 must not duplicate any entry in this list — not even partially (same main clause, different subtitle counts as a duplicate).

Append to run log: `Stage 4.5 (H1 Check): COMPLETE — prior H1s found: {{existingH1s.length}}`

---

### Stage 5 — Draft (Opus)
Dispatch `agents/draft.md`. Use claude-opus-4-6 for this stage.

Pass: `context`, `researchBrief`, `outline`.

Returns: `draft` — full first draft.

**Save draft to disk immediately before proceeding to Critique.** Do not wait until after the rewrite loop.

```bash
cat > "c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/Claude Workflow V2/outputs/drafts/{{run_slug}}-draft-v1.md"
```

Write the full `draft` content to this file.

Append to run log: `Stage 5 (Draft): COMPLETE — saved: outputs/drafts/{{run_slug}}-draft-v1.md — word count: {{draftWordCount}}`

---

### Stage 6 — Critique
Dispatch `agents/critique.md`.

Pass: `context`, `draft`, `researchBrief`.

The critique agent uses `researchBrief.beatStrategy` for Dimension 10 (Benchmark Comparison). Without the research brief, the benchmark comparison dimension cannot be scored.

Returns: `critiqueReport` — scores across 14 dimensions (including hook quality, H2 quality, B2B specificity, and benchmark comparison) + content type criteria + voice alignment. Specific revision instructions.

Append to run log: `Stage 6 (Critique): COMPLETE — overall: {{overallScore}} — critical issues: {{criticalCount}} — lowest dimension score: {{minScore}}`

---

### Stage 7 — Gap Research

**Short-circuit check:** Evaluate `critiqueReport` before dispatching:

- If `critiqueReport.overallScore == "PUBLISHABLE"` AND all dimension scores ≥ 2 AND `benchmarkComparison` ≥ 2:
  → **Skip Gap Research.** Set `gapFindings = []`.
  → Log: `Stage 7 (Gap Research): SKIPPED — critique PUBLISHABLE, all dims ≥ 2`
  → Proceed directly to Stage 8.

- Otherwise (any score = 1, any CRITICAL issue, NEEDS_REWRITE, MAJOR_REVISION, or benchmarkComparison < 2):
  → Dispatch `agents/gap-research.md`.

Pass: `context`, `draft`, `critiqueReport`.

Returns: `gapFindings` — missing statistics, sources, evidence needed for flagged weak sections.

**Note to gap-research agent:** Pass `criticalIssueCount = critiqueReport.criticalIssues.length` so the agent can calibrate its search budget. See `gap-research.md` for dynamic cap logic.

Append to run log: `Stage 7 (Gap Research): COMPLETE — searches run: {{searchCount}}, findings: {{foundCount}} of {{totalCount}}`

---

### Stage 8 — Rewrite (Opus)
Dispatch `agents/rewrite.md`. Use claude-opus-4-6 for this stage.

Pass: `context`, `draft`, `critiqueReport`, `gapFindings`, `outline`.

Returns: `finalDraft` — polished draft with all critique points addressed.

**Save finalDraft to disk immediately before proceeding to Fact Check.**

```bash
cat > "c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/Claude Workflow V2/outputs/drafts/{{run_slug}}-rewrite-v1.md"
```

Write the full `finalDraft` content to this file.

Append to run log: `Stage 8 (Rewrite): COMPLETE — saved: outputs/drafts/{{run_slug}}-rewrite-v1.md — word count: {{rewriteWordCount}} — critique items addressed: {{critAddressed}}`

---

### Stage 9 — Deliverables
Dispatch `agents/deliverables.md`.

Pass: `context`, `finalDraft`.

Returns: `deliverables` — SEO metadata (seo_title, meta_description, slug, h1, image_alt_suggestion) + `image_queries` [one query per [IMAGE: ...] marker in the draft; images[0] = hero, images[1+] = in-body placements].

Append to run log: `Stage 9 (Deliverables): COMPLETE — images queued: {{imageCount}}`

---

### Stage 10 — Fact Check

**Note:** If context window is approaching limits before this stage, do not skip. Instead:
1. The `finalDraft` is already saved to disk at `outputs/drafts/{{run_slug}}-rewrite-v1.md`
2. Start a new session, load only that file + the context object, and run Fact Check in isolation
3. Log: `Stage 10 (Fact Check): DEFERRED — run in new session from saved rewrite artifact`

Dispatch `agents/fact-check.md`.

Pass: `context`, `finalDraft`.

Returns: `factCheckReport` — list of claims, their sources, and any flags.

**Gate (hard stop):** If fact check flags any claim as UNVERIFIABLE, remove it from the draft or replace with a flagged placeholder `[VERIFY: claim]`. Apply all `factCheckReport.requiredChanges` to `finalDraft` before proceeding to output.

Do NOT send content with UNVERIFIABLE claims to output.

Append to run log: `Stage 10 (Fact Check): COMPLETE — verdict: {{overallVerdict}} — verified: {{verifiedCount}}, flagged: {{flaggedCount}}, unverifiable: {{unverifiableCount}}`

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

Append to run log: `Stage 11 (Output): COMPLETE — doc: {{docUrl}} — job: {{jobId}}`

---

### Stage 12 — Document Structure Check
**Run in orchestrator context.** Do not dispatch as a sub-agent.

Follow `agents/doc-check.md` step by step. Pass: `docUrl`, `deliverables`, `finalDraft`, `context`.

This stage reads the published Google Doc back and verifies structural integrity before the pipeline is marked complete. It catches formatting failures (broken placeholders, missing elements, metadata in wrong position) that cannot be detected from the draft alone.

If any CRITICAL check FAILs: apply the fix (rebuild doc or patch via `modify_doc_text`) and re-verify before proceeding.

Append to run log: `Stage 12 (Doc Check): COMPLETE — verdict: {{ALL CLEAR | ISSUES FOUND}} — critical: {{N pass, N fail}} — quality: {{N pass, N warn}}`

Write run log closing entry:
```
---
RUN COMPLETE: {{datetime}}
Stages: 12/12
Google Doc: {{docUrl}}
Supabase Job: {{jobId}}
Doc Check: {{ALL CLEAR | N issues fixed}}
Research Brief: outputs/research/{{run_slug}}.md
Draft v1: outputs/drafts/{{run_slug}}-draft-v1.md
Final Rewrite: outputs/drafts/{{run_slug}}-rewrite-v1.md
```

---

## Error Handling

If any stage returns an error:
1. Append to run log: `Stage N (Name): FAILED — {{error detail}}`
2. Do NOT proceed to next stage
3. Report the failure clearly: "Pipeline stopped at [Stage N — Name]: [error detail]"
4. If the error is recoverable (e.g., a tool call timeout), retry once. If it fails again, stop.
5. Note recovery path: any stages already logged as COMPLETE have saved artifacts and can be resumed from.

## Output to User

At completion, report:
```
Pipeline complete.
- Google Doc: [URL]
- Research Brief: outputs/research/[filename].md
- Rewrite saved: outputs/drafts/[filename]-rewrite-v1.md
- Run log: outputs/logs/[filename].log
- Supabase Job ID: [ID]
- Fact Check: [X claims verified, Y flagged — see report]
- Benchmark: [Beats / Comparable / Falls short] — [one sentence summary]
- Gap Research: [skipped (PUBLISHABLE) / N findings from M searches]
- Tavily: [active / DEGRADED — WebSearch fallback]
- Doc Check: [ALL CLEAR / N issues fixed]
- Stages completed: 12/12
```

If the pipeline stopped early, report which stage failed and why, and which artifacts are saved for recovery.
