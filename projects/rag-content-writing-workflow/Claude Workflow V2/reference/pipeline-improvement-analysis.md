# Pipeline Improvement Analysis
**Date:** 2026-03-26
**Scope:** V2 pipeline — efficiency, stability, content quality

---

## Summary

The V2 pipeline is architecturally sound and producing good content (Tests #6–#10). The improvements below address three categories of known fragility plus content quality gaps observed across the test runs. They're ordered within each category by impact-to-effort ratio — highest-value, lowest-cost changes first.

---

## 1. Stability

### 1.1 Draft artifact not saved before Critique [HIGH PRIORITY]

**Problem:** The draft only gets saved to disk after the full Critique → Gap → Rewrite loop completes. If context compacts during Critique or Gap Research, the draft is gone. Recovery requires manually parsing the `.jsonl` session transcript.

**Fix:** Add a draft-save step in the orchestrator immediately after the Draft agent returns, before dispatching to Critique:

```bash
# Save after Draft agent, before Critique
cat > "c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/Claude Workflow V2/outputs/drafts/{{client_slug}}--{{keyword_slug}}--{{YYYY-MM-DD}}-draft-v1.md"
```

Same pattern the Research Brief agent already uses. This costs nothing — it's one Bash write before continuing.

---

### 1.2 No Tavily health check at pipeline start [HIGH PRIORITY]

**Problem:** Tavily MCP doesn't reliably activate at session start. When it's inactive, research silently falls back to WebSearch (snippet-only, no raw_content). This degrades Branch 3 without any explicit warning. The Coverage Check evaluates "did Tavily return usable content?" without knowing whether Tavily or WebSearch actually ran.

**Fix:** Add an explicit health check at the very start of Stage 1 in the orchestrator, before dispatching any research agents:

```
Stage 0.5 — Tool Health Check
1. Attempt a single Tavily search on a simple query (e.g. the topic name)
2. If it returns raw_content: confirm "Tavily active ✅ — full research quality"
3. If it returns snippet-only or fails: warn the user "⚠ Tavily not active — research will use WebSearch fallback (degraded quality). Proceed?"
4. User can restart the session (usually fixes it) or authorize the degraded run
```

This prevents running an expensive 7-branch research phase on degraded tools without awareness.

---

### 1.3 No pipeline checkpoint/run log [MEDIUM PRIORITY]

**Problem:** When a long pipeline fails mid-run (context compaction, tool timeout, MCP error), there's no record of which stages completed and where their outputs are saved. Recovery is ad hoc.

**Fix:** Have the orchestrator write a lightweight run log at each stage completion:

```bash
# After each stage, append to run log
echo "Stage 3 (Research Brief): COMPLETE — outputs/research/{{slug}}.md" >> "outputs/logs/{{job_id}}.log"
```

File path: `outputs/logs/{{client_slug}}--{{keyword_slug}}--{{YYYY-MM-DD}}.log`

Content: job_id, inputs, stage completions with timestamps and output paths, any warnings encountered.

This also makes post-run review easier — one file shows the complete job history.

---

### 1.4 Fact Check getting cut off by context compaction [MEDIUM PRIORITY]

**Problem:** In Tests #7, #9, #10, the Fact Check stage may not have run as a formal agent pass because context was compacted before it. The [FACT-CHECK] flags in the rewrite served as a workaround but they're not the same thing.

**Fix:** Two changes:
1. After the Rewrite agent completes, save the rewritten draft to disk immediately (same pattern as above). This is now the recovery point.
2. Add a explicit checkpoint in the orchestrator before Stage 10 (Fact Check): "Rewrite complete — now running Fact Check on saved draft." This makes the stage boundary explicit and gives the user visibility if context is getting tight.

If context is clearly running out before Fact Check, the better path is to start a new session, load only the rewritten draft + context object, and run Fact Check in isolation rather than skipping it.

---

### 1.5 Google Workspace MCP constraint undocumented in orchestrator [LOW PRIORITY]

**Problem:** Google Workspace MCP can't run in a sub-agent context (OAuth redirect fails). The Output agent must run in the orchestrator context. This is documented in CLAUDE.md and `output.md` but not in the orchestrator's stage-by-stage notes, so it's easy to accidentally dispatch Output as a sub-agent.

**Fix:** Add a comment block to Stage 11 in `orchestrator.md`:

```
⚠ CONSTRAINT: Output agent MUST run in this orchestrator context, not as a sub-agent.
Google Workspace MCP (create_doc, import_to_google_doc) fails in sub-agent contexts.
Paste output.md instructions directly and execute here.
```

---

## 2. Efficiency

### 2.1 No short-circuit for strong drafts [MEDIUM PRIORITY]

**Problem:** Every draft always goes through full Critique → Gap Research → Rewrite regardless of quality. The loop was added because early drafts needed it. But as the Draft agent's instructions mature, some drafts may be strong enough to skip Gap Research entirely.

**Fix:** Add a conditional in the orchestrator after Critique:

```
If critiqueReport.overallScore == "PUBLISHABLE" AND no dimension < 2:
  → Skip Gap Research
  → Dispatch Rewrite with gapFindings = []
  → Note: "Critique PUBLISHABLE — Gap Research skipped"

If critiqueReport.overallScore == "NEEDS_REWRITE" OR any dimension == 1:
  → Run Gap Research (mandatory)
  → Then Rewrite
```

Gap Research is expensive (5 web searches + agent context). Skipping it on strong drafts saves meaningful time per run.

---

### 2.2 Coverage Check doesn't surface warnings to user [MEDIUM PRIORITY]

**Problem:** Coverage Check has three outcomes: PROCEED, PROCEED_WITH_WARNINGS, STOP. STOP escalates to the user. But PROCEED_WITH_WARNINGS currently just continues silently — the user only sees warnings if they read the coverage report. Multiple warnings (zero RAG chunks + Tavily blocked + intent mismatch) can accumulate without user awareness.

**Fix:** The orchestrator should surface PROCEED_WITH_WARNINGS to the user before continuing:

```
If coverageReport.overallStatus == "PROCEED_WITH_WARNINGS":
  → Print warning summary to user: "Research has [N] warnings: [list issues].
     Proceed anyway, or investigate before continuing?"
  → Default: proceed (non-blocking)
  → But user can stop and fix the data quality issue
```

This costs nothing computationally and prevents the pipeline from producing a weak article on degraded inputs without anyone knowing.

---

### 2.3 Gap Research capped at 5 searches regardless of critique depth [LOW PRIORITY]

**Problem:** Gap Research is limited to 5 searches. A heavily flagged draft (8 critical issues) gets the same 5-search budget as a lightly flagged one (2 issues). The cap was set to prevent re-running full research, which is correct — but it should scale with the number of critical issues.

**Fix:** Make the cap dynamic:

```
Max searches = min(criticalIssues.length + 2, 8)
```

Still bounded to prevent runaway searches, but proportional to actual need.

---

### 2.4 Rewrite receives full original draft even when only small sections need work [LOW PRIORITY]

**Problem:** The Rewrite agent receives the complete first draft plus the full critique report and must process all of it even if only 2-3 sections need significant changes. This inflates context usage per run.

**Fix:** The critique report already marks severity (CRITICAL / IMPROVEMENT). In the orchestrator dispatch to Rewrite, annotate which sections are unchanged and which need rewriting:

```
Sections with no CRITICAL or IMPROVEMENT items: treat as locked — do not rewrite, carry forward verbatim.
Sections with items: rewrite these sections only.
```

This keeps the full draft in context but focuses rewriting effort. On a 2,500-word article where only the intro and two sections need work, this can halve effective rewrite time.

---

### 2.5 Research Branch 6 (ChatGPT scraper) is slow and expensive for every run [LOW PRIORITY]

**Problem:** Branch 6 hits the DataForSEO `ai_optimization_chat_gpt_scraper` tool every run. This is the most expensive and slowest branch. For repeat topics (e.g., running the same content type for multiple keywords), LLM citation landscapes change slowly — the data from a week ago is still largely valid.

**Fix:** Cache LLM citation results by topic cluster. Before running Branch 6, check if a recent result exists for a closely related keyword:

```
outputs/research/llm-citations/{{client_slug}}--{{topic_cluster}}.json
```

If cached within 14 days: skip Branch 6, use cached data, note "LLM citations from cache ({{date}})".
If no cache or stale: run Branch 6 and update cache.

---

## 3. Content Quality

### 3.1 Draft agent has no self-check before output [HIGH PRIORITY]

**Problem:** The Draft agent has extensive writing rules but no closing self-check. Em dashes, American spellings, and missing BLUF blocks get caught by the Critique agent instead of being caught by the drafter. This means the critique wastes capacity on mechanical issues rather than genuine quality problems.

**Fix:** Add a mandatory self-check block to `draft.md` before the Output Format section:

```markdown
## Pre-Submission Self-Check (mandatory)

Before returning the draft, run this check and fix every ❌:

| Check | Status |
|---|---|
| Zero em dashes (—) anywhere in draft | ✅ / ❌ |
| Every H2 section opens with a 40–60 word BLUF paragraph | ✅ / ❌ |
| All statistics have named sources (Source, Year) format | ✅ / ❌ |
| No URLs present that weren't in the research brief | ✅ / ❌ |
| Primary keyword in H1 and within first 100 words | ✅ / ❌ |
| {{client.writing_language}} spelling (not American English) | ✅ / ❌ |
| No paragraph exceeds 5 sentences | ✅ / ❌ |
| Allocation/breakdown data in tables, not prose sentences | ✅ / ❌ |

Do not submit the draft with any ❌ items. Fix them first.
```

This moves mechanical compliance upstream, making the Critique agent's job what it's supposed to be: content strategy, not spellcheck.

---

### 3.2 Research brief source quality isn't tagged by data type [MEDIUM PRIORITY]

**Problem:** The External Sources Found table in the research brief doesn't distinguish how a source was found. A URL from Tavily raw_content (high confidence — actually fetched the page) is different from a URL embedded in a search snippet (medium confidence) which is different from a source name mentioned in body text (low confidence, no URL). The Draft agent treats all of them the same.

**Fix:** Add a `data_source` column to the External Sources Found table:

| Claim / Topic | Source name | URL | Quality tier | **Data source** | Notes |
|---|---|---|---|---|---|
| RBA cash rate | RBA, March 2026 | rba.gov.au/... | Primary | **Tavily raw_content** | Confirmed 4.10% |
| SMSF count | ATO, 2024 | (no URL) | Primary | **Search snippet only** | No URL available |

This signals to the Draft agent (and human reviewer) how much to trust each source. Tavily raw_content = high confidence. Search snippet = cite but flag for fact-check.

---

### 3.3 Reddit/social signals fallback is underdefined [MEDIUM PRIORITY]

**Problem:** For B2B topics (offshore staffing, financial products, professional services), Reddit threads are sparse or nonexistent. When Branch 4 returns nothing, the research brief just says "Low volume topic — limited Reddit discussion found" and the audience intelligence section is effectively empty.

**Fix:** When Reddit returns fewer than 2 threads, automatically pivot the query:
1. Try LinkedIn professional discussions (via Tavily `site:linkedin.com/pulse`)
2. Try Quora (via Tavily `site:quora.com`)
3. Try industry-specific forums relevant to the client's sector
4. Fall back to comment sections on high-ranking competitor articles (found in Branch 5)

Document this fallback cascade in `research.md` Branch 4 so it runs automatically rather than returning empty.

---

### 3.4 Featured snippet format not being actively targeted [MEDIUM PRIORITY]

**Problem:** The research brief notes whether a featured snippet exists and its format (paragraph / list / table). But neither the Outline nor Draft agent has a specific instruction to *match that format* in the relevant section. The BLUF block is always a paragraph, even when the featured snippet is a list or table.

**Fix:** Add a featured-snippet targeting note to the Outline agent:

```
If serpData.featuredSnippet.exists:
  - Note: current snippet is [format] format at [URL]
  - The section most relevant to the snippet query must use the same format for its answer block
  - If snippet is a list: the BLUF block should be a short intro + bullet list (not paragraph)
  - If snippet is a table: the BLUF block should be a short intro + a 2-3 row table
  - Annotate the relevant section with: **Snippet target: use [list/table] format for BLUF**
```

Matching the format signals to Google that the content is a direct candidate for the position.

---

### 3.5 V2O compliance tracking is unstructured [MEDIUM PRIORITY]

**Problem:** The V2O brief is injected into every agent as a raw text block with a "⚠ MANDATORY" header. But there's no structured tracking of which V2O requirements were addressed and which weren't. At the end of the run, a user who provided a V2O brief has no quick way to confirm their requirements were met.

**Fix:** Add a V2O compliance checklist to the Rewrite agent output:

```json
"v2oCompliance": {
  "requirementsFound": 4,
  "requirementsMet": [
    { "requirement": "Include client's SMSF stat", "section": "SMSF section", "status": "MET" },
    { "requirement": "Mention XYZ product", "section": "Product comparison table", "status": "MET" }
  ],
  "requirementsPartial": [],
  "requirementsMissed": []
}
```

The Critique agent already checks V2O compliance as the first dimension. The Rewrite agent should confirm in its output that all V2O items were addressed, not just that it tried.

---

### 3.6 Fact Check agent has no verification pathway [LOW PRIORITY]

**Problem:** The Fact Check agent deliberately doesn't follow URLs (to avoid hallucinating whether a page exists). It can only flag URLs not found in the research data. This means a fabricated URL that happens to look like a real one (e.g., `rba.gov.au/statistics/cash-rate`) will pass unchallenged if the source name (RBA) was in the research data.

**Fix:** Two lightweight changes:
1. Add WebSearch verification for any URL the agent is uncertain about: "If a URL in the draft looks like it could be fabricated, run a single WebSearch for the URL's page title to confirm the page exists."
2. For any claim the agent marks UNVERIFIABLE, the orchestrator should automatically remove the claim from the final draft rather than just flagging it. Currently the agent instructs removal but the orchestrator has to execute it manually.

---

### 3.7 Outline word count distribution isn't quality-aware [LOW PRIORITY]

**Problem:** The outline distributes word counts mechanically (most sections: 150–400 words). But sections with a beat strategy requirement, a featured snippet target, or a comparison table need more words than a standard informational section. The distribution doesn't reflect the content's strategic priorities.

**Fix:** In the outline agent, after distributing the baseline word budget, apply a priority adjustment:

```
Sections with a Beat annotation: +10% word allocation
Sections with a Table requirement: +50 words (tables eat word count)
Sections targeting a featured snippet: 40–60 word BLUF + 120–160 words body = fixed allocation
Introduction: fixed 100–150 words
```

Sum of adjusted allocations should still hit the draft target (±5%).

---

## 4. Architecture / Future Proofing

### 4.1 All 15 agents run in one session context [LONG TERM]

**Problem:** A full pipeline run (15 agents, 7 research branches, 3 writing stages) pushes into context compaction territory for long-form content. Context compaction is the root cause of most stability issues (lost drafts, skipped fact-checks).

**Options (in order of implementation complexity):**
1. **Aggressive artifact saving** (low effort, immediate): save every major output to disk as it's produced. Already done for research brief and drafts (after this analysis's fixes). Extend to: outline, draft, rewrite. If compaction happens, the last saved artifact is the recovery point.
2. **Session handoff** (medium effort): split the pipeline into two sessions at a natural boundary — Research + Research Brief in Session 1, save all outputs to disk, then Outline → Output in Session 2. The orchestrator loads artifacts from disk at Session 2 start. Context stays manageable.
3. **True agent isolation** (high effort, future): each sub-agent runs in its own context via the Agent tool with minimal data passed in. Already partially the design — but orchestrator currently holds everything in its own context window.

Recommendation: implement option 1 now, plan option 2 when context compaction becomes a regular problem.

---

### 4.2 No structured way to resume a failed run [MEDIUM TERM]

**Problem:** If a run fails at Stage 8 (Rewrite), there's no "resume from Stage 7" option. The user has to either restart fully or manually reconstruct the state from saved artifacts.

**Fix:** The run log (from fix 1.3) enables a resume path. The orchestrator should accept a `resume_from` input:

```json
{
  "client_name": "Client D",
  "content_type_slug": "asset_class_page",
  "topic": "Infrastructure ETFs",
  "target_keywords": ["infrastructure etf australia"],
  "resume_from": "rewrite",
  "job_id": "4c26bc51-..."
}
```

When `resume_from` is set: load the saved artifacts for that job (outline, draft, research brief, critique), skip completed stages, resume from the specified stage. This requires all artifacts to be consistently named by `job_id` — which they currently aren't (they use client_slug + keyword_slug + date, which can collide across runs).

---

## Priority Order for Implementation

| Priority | Fix | Category | Effort |
|---|---|---|---|
| 1 | Save draft to disk immediately after Draft agent | Stability | 5 min |
| 2 | Add draft self-check to draft.md | Content Quality | 15 min |
| 3 | Add Tavily health check at pipeline start | Stability | 20 min |
| 4 | Add run log/checkpoint system | Stability | 30 min |
| 5 | Surface PROCEED_WITH_WARNINGS to user | Efficiency | 15 min |
| 6 | Short-circuit Critique loop for PUBLISHABLE drafts | Efficiency | 15 min |
| 7 | V2O compliance checklist in Rewrite output | Content Quality | 20 min |
| 8 | Featured snippet format targeting in Outline | Content Quality | 20 min |
| 9 | Reddit signals fallback cascade | Content Quality | 30 min |
| 10 | Source quality data_source column in research brief | Content Quality | 20 min |
| 11 | Save rewrite to disk immediately after Rewrite | Stability | 5 min |
| 12 | Document Google Workspace constraint in orchestrator | Stability | 5 min |
| 13 | Dynamic Gap Research search cap | Efficiency | 10 min |
| 14 | LLM citation caching | Efficiency | 30 min |
| 15 | Fact Check URL verification via WebSearch | Content Quality | 20 min |

---

## What Not to Fix

These are known issues that either have an acceptable workaround or aren't worth the complexity:

- **Slack missing_scope** — pending Fitz approving the app. Not a pipeline issue.
- **Client D logo_url** — manual lookup needed. Not a pipeline issue.
- **Shutterstock image quality** — addressed with better search terms per run. No structural fix needed.
- **Word count overshoot** — the 1.15× multiplier in the outline handles this adequately. Don't add another layer.
- **em dash rule** — already in draft.md ABSOLUTE RULES and critique Dimension 9. Adding more enforcement would be redundant. The draft self-check (fix above) covers it.
