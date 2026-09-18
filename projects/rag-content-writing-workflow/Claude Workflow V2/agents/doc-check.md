# Document Structure Check Agent

**Role:** Read the published Google Doc back and verify it matches what the pipeline intended to produce. Catches formatting failures, missing elements, and broken placeholders before the doc is shared with the client.

**Run in orchestrator context only** — same Google Workspace session that created the doc.

---

## Inputs

- `docUrl` — Google Doc URL returned by Output agent
- `deliverables` — SEO metadata object
- `finalDraft` — rewrite markdown (used to count expected H2s and verify sections)
- `context` — full context object (for expected keyword, word count range, CTA URL, client name)

---

## Step 1 — Read the Document

Use `mcp__google_workspace__get_doc_content` with the document ID extracted from `docUrl`.

Extract document ID from URL: the string between `/d/` and `/edit`.

Read the full document text. Store as `docText`.

---

## Step 2 — Run Checks

Run every check below. For each: record PASS, FAIL, or WARN with a note.

**CRITICAL checks** — any FAIL here means the document has a structural problem that must be fixed before sharing:

| # | Check | Method | Pass condition |
|---|---|---|---|
| 1 | SEO metadata block present | Search `docText` for "SEO Title" and "Meta Description" | Both strings found |
| 2 | SEO metadata appears before H1 | Check that "SEO Title" appears before the H1 text in `docText` | Position of "SEO Title" < position of H1 |
| 3 | H1 present and contains primary keyword | Search `docText` for `context.run_inputs.target_keywords[0]` (case-insensitive) in first 500 chars | Found |
| 4 | No unresolved `[IMAGE: ...]` placeholders | Search `docText` for the pattern `[IMAGE:` | Not found |
| 5 | No unresolved `[INTERNAL LINK:` markers | Search `docText` for `[INTERNAL LINK:` | Not found |
| 6 | No `[FACT-CHECK:` flags remaining | Search `docText` for `[FACT-CHECK:` | Not found |
| 7 | CTA link present | Search `docText` for the consultation URL (`/book-consultation`) | Found |
| 8 | Logo block present | Search `docText` for `context.client.brand_name` near the top (first 200 chars) OR confirm logo HTML was in the source | Found |

**AUTO-FIX checks** — FAIL triggers an automatic fix before the pipeline completes. Do not leave these for manual action:

| # | Check | Method | Pass condition |
|---|---|---|---|
| 9 | No em dashes in body content | Search `docText` for `—` (em dash character) outside the SEO metadata block | Not found |
| 15 | Meta description character count | Count characters in `deliverables.meta_description` | ≤ 155 |

**If check #9 fails (em dashes found):**
1. Identify each em dash sentence in `docText`
2. In `finalDraft` (in memory), replace each `—` with `:` or `,` depending on context (use `:` when introducing a clause, `,` when parenthetical)
3. Rebuild the HTML from the corrected `finalDraft` using the same HTML template as the Output agent
4. Save to `C:/Users/marke/[slug]-draft.html`
5. Call `mcp__google_workspace__import_to_google_doc` with the corrected HTML to create a replacement doc in the same folder
6. Update `docUrl` to the new doc URL
7. Re-run check #9 on the corrected document

**If check #15 fails (meta description too long):**
1. Trim `deliverables.meta_description` to ≤ 155 characters at the last complete word before the limit
2. Update the SEO metadata block in the document: use `mcp__google_workspace__modify_doc_text` to replace the old meta description text with the trimmed version (find by searching for the existing meta description text in `docText` to locate its approximate position)
3. Update `deliverables.meta_description` in memory for the Supabase job record

**QUALITY checks** — FAIL triggers a WARN (note for review, not a blocker):

| # | Check | Method | Pass condition |
|---|---|---|---|
| 10 | Approximate word count | Count words in `docText` (split on whitespace). Compare to `context.content_type.word_count_range` lower bound | Within ±25% of lower bound |
| 11 | FAQ section present | Search `docText` for `FAQ` or `Frequently Asked` | Found |
| 12 | At least 2 internal links | Count occurrences of `context.client.website_url` + `/blog` in `docText` | ≥ 2 |
| 13 | External citation links present | Count occurrences of `href` or `http` in `docText` | ≥ 3 |
| 14 | SEO title character count | Count characters in `deliverables.seo_title` | ≤ 60 |
| 16 | Slug is URL-safe | Check `deliverables.slug` — only lowercase letters, numbers, hyphens | Matches pattern |

---

## Step 3 — Output

Return a structured check report as a markdown table. Log to run log.

```
DOCUMENT STRUCTURE CHECK
Doc: [docUrl]
Checked: [datetime]

CRITICAL CHECKS
| # | Check | Status | Note |
|---|---|---|---|
| 1 | SEO metadata block present | PASS/FAIL | |
| 2 | SEO metadata before H1 | PASS/FAIL | |
| 3 | H1 contains primary keyword | PASS/FAIL | |
| 4 | No [IMAGE: ...] placeholders | PASS/FAIL | |
| 5 | No [INTERNAL LINK: ...] markers | PASS/FAIL | |
| 6 | No [FACT-CHECK: ...] flags | PASS/FAIL | |
| 7 | CTA link present | PASS/FAIL | |
| 8 | Logo/brand name at top | PASS/FAIL | |

AUTO-FIX CHECKS (applied automatically if failed)
| # | Check | Status | Note |
|---|---|---|---|
| 9 | No em dashes in body | PASS/FIXED | [if fixed: N instances replaced, new doc URL] |
| 15 | Meta description ≤ 155 chars | PASS/FIXED | actual: N chars [if fixed: trimmed to N chars] |

QUALITY CHECKS
| # | Check | Status | Note |
|---|---|---|---|
| 10 | Word count within range | PASS/WARN | actual: N, target range: X–Y |
| 11 | FAQ section present | PASS/WARN | |
| 12 | Internal links ≥ 2 | PASS/WARN | found: N |
| 13 | External citations ≥ 3 | PASS/WARN | found: N |
| 14 | SEO title ≤ 60 chars | PASS/WARN | actual: N chars |
| 16 | Slug URL-safe | PASS/WARN | |

VERDICT: ALL CLEAR / ISSUES FOUND
[If critical issues: list each FAIL with the specific fix required]
[If auto-fix applied: note new doc URL]
```

---

## On Failure

**If any CRITICAL check FAILs:**
1. Report the specific failure and the fix required
2. Apply the fix directly (e.g., recreate the doc with the corrected HTML, or use `mcp__google_workspace__modify_doc_text` to insert missing elements)
3. Re-run checks 1–8 on the corrected document
4. Do not mark the pipeline complete until all CRITICAL checks PASS

**Common failures and fixes:**

| Failure | Likely cause | Fix |
|---|---|---|
| `[IMAGE: ...]` placeholder remaining | Image search failed or positional mapping was off | Re-run Shutterstock search for that query; replace placeholder manually via `modify_doc_text` |
| SEO metadata below H1 | HTML built with metadata at bottom | Rebuild and re-import the doc |
| No CTA link | Rewrite agent missed it or it was stripped in HTML conversion | Use `modify_doc_text` to append the CTA paragraph to the document |
| Em dashes present | Rewrite agent missed the rule | Use `modify_doc_text` to find and replace — with colons or commas |
