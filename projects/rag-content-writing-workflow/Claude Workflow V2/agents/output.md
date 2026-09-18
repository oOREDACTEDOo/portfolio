# Output Agent

**Role:** Deliver the final content to Google Docs, save the job to Supabase, and notify via Slack.

> ⚠ **Run in orchestrator context only.** Do not dispatch as a sub-agent. Google Workspace MCP requires an authenticated session — sub-agent dispatch triggers an OAuth redirect that cannot complete. The orchestrator runs these steps directly.

---

## Inputs

- `context` — full context object
- `finalDraft` — rewritten and fact-checked draft (markdown)
- `deliverables` — SEO metadata + image query from Deliverables agent
- `factCheckReport` — summary of fact-check results

---

## Step 1 — Image Searches

Loop through **all** `deliverables.image_queries`. For each query, run one Shutterstock search and select the single best result. Store results as `images[]` array — `images[0]` is the hero, `images[1]`, `images[2]` etc. are in-body placements.

**Tool:** Bash — curl to Shutterstock API (one call per query)

URL-encode the query string, then run:

```bash
curl -s -u "REDACTED_SHUTTERSTOCK_CLIENT_ID:REDACTED_SHUTTERSTOCK_SECRET" \
  "https://api.shutterstock.com/v2/images/search?query=QUERY&per_page=10&orientation=horizontal&image_type=photo&safe=true"
```

Auth: Basic Auth — consumer key as username, consumer secret as password (1Password: "Claude Content Generation").

**Select the single best result** using this filter order:
1. Discard any result where description contains: "illustration", "vector", "infographic", "diagram", "3d render", "collage", "composite", "graph", "chart", "icon", "symbol", "concept"
2. From remaining results, prefer images showing real people in a real-world setting over objects/environments alone
3. Pick the top passing result

Extract from each selected image:
- `previewUrl` — `assets.preview_1000.url` taken directly from the API response object. NEVER construct this URL manually — the actual URL is on `image.shutterstock.com` with a slug path, not `preview.sdcdn.com`. Do NOT use `preview_1500` which uses `z/` format URLs that also fail to embed in Google Docs.
- `pageUrl` — use `url` field directly from the API response (e.g. `https://www.shutterstock.com/image-photo/...`) — do NOT construct manually
- `id` — image ID
- `description` — image description

**If no results pass:** use a simplified fallback query (core 2–3 word noun phrase) and retry once. If still no results, set that `images[n] = null`.

After all queries are processed, `heroImage = images[0]`.

---

## Step 2 — Google Doc Creation

**Tool:** `mcp__google_workspace__import_to_google_doc`

Do NOT use `create_doc` — it produces unstyled plain text. Always use `import_to_google_doc` with `source_format: 'html'`.

**Document title:** `{{deliverables.h1}} — {{today's date}}`

**Folder:** Use `context.client.google_drive_folder_id` if set. Otherwise search Drive for a folder named `{{context.client.brand_name}}`.

---

### Article Body Preparation

Before building the HTML, process `finalDraft` (markdown):

1. **Replace image placeholders** — for each `[IMAGE: ...]` line in the article body, replace it with the corresponding image from `images[]`. The mapping is positional: the first `[IMAGE: ...]` encountered in the body uses `images[1]`, the second uses `images[2]`, and so on (`images[0]` is always the hero placed after H1). If `images[n]` is null, replace the marker with the "image needed" placeholder block instead. See image HTML template in Block 3 below.

2. **Convert markdown to HTML** using this mapping:

| Markdown | HTML |
|---|---|
| `# Heading` | `<h1 style="font-family:'Poppins',Arial,sans-serif;font-size:24pt;font-weight:700;color:#1a1a1a;line-height:1.3;margin:0 0 16pt 0;">Heading</h1>` |
| `## Heading` | `<h2 style="font-family:'Poppins',Arial,sans-serif;font-size:15pt;font-weight:600;color:#1a1a1a;margin:20pt 0 8pt 0;">Heading</h2>` |
| `### Heading` | `<h3 style="font-family:'Poppins',Arial,sans-serif;font-size:12pt;font-weight:600;color:#333;margin:14pt 0 6pt 0;">Heading</h3>` |
| `> quote text` | `<blockquote style="margin:14pt 0;padding:10pt 16pt;border-left:4px solid #0057b8;background:#f4f7ff;font-style:italic;color:#444;"><p style="margin:0;">quote text</p></blockquote>` |
| `**text**` | `<strong>text</strong>` |
| `*text*` | `<em>text</em>` |
| `[anchor](url)` | `<a href="url" style="color:#0057b8;">anchor</a>` |
| `- item` | wrap all consecutive items in `<ul style="margin:0 0 11pt 0;padding-left:20pt;">` with `<li style="margin-bottom:5pt;font-family:'Poppins',Arial,sans-serif;">item</li>` |
| blank-line paragraph | `<p style="font-family:'Poppins',Arial,sans-serif;font-size:11pt;line-height:1.7;color:#2d2d2d;margin:0 0 11pt 0;">text</p>` |

Replace `[INTERNAL LINK: Title | URL | anchor text]` markers with `<a href="URL" style="color:#0057b8;">anchor text</a>`.

**Table column limit:** Google Docs renders at ~620px content width. Maximum 7 columns for readable tables — 8+ columns causes severe cell wrapping. If the draft contains a table with more than 7 columns, drop the least critical columns (e.g. intermediate return periods) and note them in adjacent body text instead.

---

### HTML Document Structure

Build the complete HTML string below, substituting all bracketed values. Pass as `content` to `import_to_google_doc`.

```html
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  body { font-family: 'Poppins', Arial, sans-serif; font-size: 11pt; line-height: 1.7; color: #2d2d2d; }
  h1, h2, h3 { font-family: 'Poppins', Arial, sans-serif; }
  p { margin: 0 0 11pt 0; }
  ul, ol { margin: 0 0 11pt 0; padding-left: 20pt; }
  li { margin-bottom: 5pt; }
  a { color: #0057b8; text-decoration: none; }
  img { display: block; }
  table { border-collapse: collapse; width: 96%; margin: 14pt auto; }
  td, th { border: 1px solid #ddd; padding: 7pt 10pt; vertical-align: top; }
  th { background: #f5f5f5; font-weight: 600; }
</style>
</head>
<body>
<!-- Margin wrapper — Google Docs strips body CSS; this div provides left/right page margins -->
<div style="padding: 0 48px;">
```

**Block 1 — Logo (show only if `context.client.logo_url` is set and non-null)**

```html
<div style="text-align:center;padding:20pt 0 16pt;border-bottom:2px solid #e8e8e8;margin-bottom:20pt;">
  <img src="[context.client.logo_url]" alt="[context.client.brand_name]"
       style="max-height:70px;max-width:280px;width:auto;height:auto;display:block;margin:0 auto;">
  <p style="font-family:'Poppins',Arial,sans-serif;font-size:10pt;font-weight:600;color:#555;margin:8pt 0 0;">[context.client.brand_name]</p>
</div>
```

If `logo_url` is null or empty, omit this block entirely.

---

**Block 2 — SEO Metadata (editorial reference)**

```html
<div style="background:#f8f9fa;border-left:4px solid #adb5bd;padding:12pt 16pt;margin-bottom:20pt;border-radius:0 4px 4px 0;">
  <p style="margin:0 0 8pt 0;font-family:'Poppins',Arial,sans-serif;font-weight:600;color:#666;font-size:9pt;text-transform:uppercase;letter-spacing:0.8px;">SEO Metadata — Editorial reference only. Do not publish.</p>
  <table style="border-collapse:collapse;width:100%;font-size:10pt;font-family:'Poppins',Arial,sans-serif;">
    <tr><td style="border:1px solid #dee2e6;padding:6pt 10pt;width:140px;font-weight:600;background:#fff;color:#555;">SEO Title</td><td style="border:1px solid #dee2e6;padding:6pt 10pt;background:#fff;">[deliverables.seo_title]</td></tr>
    <tr><td style="border:1px solid #dee2e6;padding:6pt 10pt;font-weight:600;background:#f8f9fa;color:#555;">Meta Description</td><td style="border:1px solid #dee2e6;padding:6pt 10pt;background:#f8f9fa;">[deliverables.meta_description]</td></tr>
    <tr><td style="border:1px solid #dee2e6;padding:6pt 10pt;font-weight:600;background:#fff;color:#555;">Slug</td><td style="border:1px solid #dee2e6;padding:6pt 10pt;background:#fff;">[deliverables.slug]</td></tr>
    <tr><td style="border:1px solid #dee2e6;padding:6pt 10pt;font-weight:600;background:#f8f9fa;color:#555;">H1</td><td style="border:1px solid #dee2e6;padding:6pt 10pt;background:#f8f9fa;">[deliverables.h1]</td></tr>
    <tr><td style="border:1px solid #dee2e6;padding:6pt 10pt;font-weight:600;background:#fff;color:#555;">Image Alt</td><td style="border:1px solid #dee2e6;padding:6pt 10pt;background:#fff;">[deliverables.image_alt_suggestion]</td></tr>
  </table>
</div>
```

If fact-check flagged any LIKELY_ACCURATE or OUTDATED items, add:

```html
<div style="background:#fff8e1;border-left:4px solid #ffc107;padding:10pt 14pt;margin-bottom:16pt;border-radius:0 4px 4px 0;">
  <p style="margin:0 0 6pt 0;font-family:'Poppins',Arial,sans-serif;font-weight:600;font-size:10pt;color:#856404;">⚠ Editorial Review Required Before Publishing</p>
  <p style="margin:0;font-family:'Poppins',Arial,sans-serif;font-size:10pt;color:#856404;">[list each flagged claim]</p>
</div>
```

```html
<hr style="border:none;border-top:2px solid #e8e8e8;margin:20pt 0;">
```

---

**Block 3 — Article content**

```html
<!-- H1 -->
[converted h1 from article]

<!-- Hero image — insert immediately after H1 -->
```

If `heroImage` is not null:

```html
<div style="margin:16pt 0 24pt;text-align:center;">
  <img src="[heroImage.previewUrl]" alt="[deliverables.image_alt_suggestion]"
       width="560"
       style="width:560px;height:auto;display:block;margin:0 auto;border-radius:6px;">
  <p style="font-family:'Poppins',Arial,sans-serif;font-size:9pt;color:#999;margin:6pt 0 0;text-align:center;">
    Image: <a href="[heroImage.pageUrl]" style="color:#999;">[heroImage.description]</a> — Shutterstock (license before publishing)
  </p>
</div>
<br clear="all">
```

> **Critical:** The `<br clear="all">` after every image div is mandatory. Google Docs HTML import does not respect `display:block` on images — without `<br clear="all">`, the following heading or paragraph renders inline to the right of the image.

If `heroImage` is null:

```html
<div style="background:#f8d7da;border-left:4px solid #dc3545;padding:10pt 14pt;margin:16pt 0 24pt;">
  <p style="font-family:'Poppins',Arial,sans-serif;font-size:10pt;color:#721c24;margin:0;">⚠ Hero image needed — select manually from Shutterstock.</p>
</div>
```

**In-body image placements:** Each `[IMAGE: ...]` marker in the body is replaced with the following HTML (use `images[n]` for each in order):

If `images[n]` is not null:

```html
<div style="margin:16pt 0 20pt;text-align:center;">
  <img src="[images[n].previewUrl]" alt="[images[n].description]"
       width="560"
       style="width:560px;height:auto;display:block;margin:0 auto;border-radius:6px;">
  <p style="font-family:'Poppins',Arial,sans-serif;font-size:9pt;color:#999;margin:6pt 0 0;text-align:center;">
    Image: <a href="[images[n].pageUrl]" style="color:#999;">[images[n].description]</a> — Shutterstock (license before publishing)
  </p>
</div>
<br clear="all">
```

If `images[n]` is null:

```html
<div style="background:#f8d7da;border-left:4px solid #dc3545;padding:10pt 14pt;margin:16pt 0 20pt;">
  <p style="font-family:'Poppins',Arial,sans-serif;font-size:10pt;color:#721c24;margin:0;">⚠ Image needed here — select manually from Shutterstock.</p>
</div>
```

```html
<!-- Rest of article body (paragraphs, h2s, h3s, lists, blockquotes, tables) -->
[converted article body — [IMAGE: ...] markers replaced with image blocks as above]

</div><!-- end margin wrapper -->
</body>
</html>
```

---

### HTML File Save + Tool Call

> ⚠ **Temp file location constraint:** The Google Workspace MCP's `ALLOWED_FILE_DIRS` is restricted to `C:\Users\marke\`. Do NOT write the HTML to `c:/tmp/` — the import will fail with a permission error. Write the HTML file to `C:\Users\marke\[slug]-draft.html`, call `import_to_google_doc` with `file://c:/Users/marke/[slug]-draft.html`, then delete the temp file after the doc is created.

```json
{
  "user_google_email": "jan.m@webprofits.com.au",
  "file_name": "{{deliverables.h1}} — {{today's date}}",
  "content": "{{full_html_string}}",
  "source_format": "html",
  "folder_id": "{{context.client.google_drive_folder_id || searched_folder_id}}"
}
```

Return: `docUrl`.

---

## Step 3 — Supabase Job Save

**Tool:** `mcp__supabase__execute_sql`

```sql
INSERT INTO content_jobs (
  client_id,
  content_type,
  topic,
  target_keywords,
  mode,
  status,
  outline,
  research_brief,
  critique,
  gap_research,
  final_output,
  output_url,
  model_used,
  created_at,
  completed_at
) VALUES (
  '{{context.client.id}}',
  '{{context.content_type.type_slug}}',
  '{{context.run_inputs.topic}}',
  '{{context.run_inputs.target_keywords}}',
  'new',
  'draft',
  '{{outline}}',
  '{{researchBrief}}',
  '{{critiqueReport}}',
  '{{gapFindings}}',
  '{{finalDraft}}',
  '{{docUrl}}',
  'claude-opus-4-6',
  NOW(),
  NOW()
)
RETURNING id;
```

Return: `jobId`.

---

## Step 4 — Slack Notification

**Tool:** `mcp__slack__slack_post_message`

**Channel:** Use `context.client.slack_channel_id` if set. Fall back to `#wp-content` (channel ID: `C84T52EPM`). Note: `#content-automation` does not exist in this workspace.

> ⚠ Slack posting requires `chat:write:bot` scope. The "claude content" Slack app (A0ANM1CM708) is pending workspace admin approval — ping Fitz to approve in Slack Apps > Manage > Pending. Until approved, Step 4 will fail with `missing_scope` error. Treat as PARTIAL (non-blocking) — still deliver the doc.

**Message:**
```
✅ Content draft ready for review

*Client:* {{context.client.brand_name}}
*Type:* {{context.content_type.type_name}}
*Topic:* {{topic}}
*Keyword:* {{target_keywords[0]}}

*Google Doc:* {{docUrl}}
*Word count:* {{word_count}} words
*Fact check:* {{factCheckReport.overallVerdict}} ({{factCheckReport.verdictSummary.VERIFIED}} verified, {{factCheckReport.verdictSummary.LIKELY_ACCURATE}} for review)

{{#if factCheckReport.requiredChanges.length > 0}}
⚠ *Editorial actions taken before delivery:*
{{factCheckReport.requiredChanges.join('\n')}}
{{/if}}

_Job ID: {{jobId}}_
```

---

## Output Format

```json
{
  "output": {
    "status": "SUCCESS | PARTIAL | FAILED",
    "docUrl": "https://docs.google.com/document/d/...",
    "jobId": "uuid",
    "slackNotified": true,
    "wordCount": 2284,
    "heroImageUsed": true,
    "imagesPlaced": 3,
    "errors": []
  }
}
```

**PARTIAL** = Google Doc created but Slack failed, or Supabase save failed (non-blocking — still deliver the doc)
**FAILED** = Google Doc creation failed (the one hard failure — report and stop)
