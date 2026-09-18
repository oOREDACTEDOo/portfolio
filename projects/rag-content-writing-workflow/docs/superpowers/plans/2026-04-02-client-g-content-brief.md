# Client G Content Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-page HTML operational content brief for Client G that Webprofits colleagues can open in a browser to make editorial and pipeline decisions.

**Architecture:** One self-contained HTML file with embedded CSS and no external dependencies. All content is hardcoded from Supabase data already captured in the spec. After local build, the file is uploaded to GitHub via the `github-upload` skill and served live at `https://webprofits.ai/jan-m/client-g/client-g-content-brief.html`.

**Tech Stack:** HTML5, embedded CSS (system fonts, no frameworks, no JS required), GitHub Pages via `webprofits/jan-m` repo.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/client-g-content-brief.html` | Create | Complete single-page brief — scaffold + all 11 sections |

No other files created or modified.

---

## Task 1: Build HTML scaffold with embedded CSS and navigation

**Files:**
- Create: `c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/client-g-content-brief.html`

- [ ] **Step 1: Write the scaffold**

Write the full HTML file with:
- `<!DOCTYPE html>` declaration, `<html lang="en">`, `<head>` with charset, viewport, title "Client G Content Brief"
- Embedded `<style>` block (see exact CSS below)
- Sticky top nav bar with jump links to all 11 sections
- 11 empty `<section>` containers with correct `id` attributes
- Footer with "Generated from Supabase — RAG Content Production System" and the current date

**Exact CSS to embed:**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: #1a1a1a;
  background: #f8f8f8;
  min-width: 1024px;
}

/* Sticky nav */
nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #1a1a1a;
  padding: 0 32px;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  min-height: 48px;
}
nav a {
  color: #ccc;
  text-decoration: none;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 4px;
  white-space: nowrap;
}
nav a:hover { color: #fff; background: #333; }
nav .brand {
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  margin-right: 12px;
  padding: 6px 0;
  white-space: nowrap;
}

/* Page wrapper */
.page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 40px 32px 80px;
}

/* Page header */
.page-header {
  margin-bottom: 40px;
  padding-bottom: 24px;
  border-bottom: 2px solid #e0e0e0;
}
.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 6px;
}
.page-header .meta {
  font-size: 13px;
  color: #666;
}

/* Section cards */
section {
  background: #fff;
  border-radius: 8px;
  padding: 32px;
  margin-bottom: 24px;
  border: 1px solid #e8e8e8;
}
section:nth-child(even) { background: #fafafa; }

.section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #999;
  margin-bottom: 8px;
}
.section-number {
  display: inline-block;
  background: #1a1a1a;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  text-align: center;
  line-height: 22px;
  margin-right: 8px;
  vertical-align: middle;
}
section h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}
section h3 {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #555;
  margin: 20px 0 8px;
}

/* Content elements */
p { margin-bottom: 12px; }
p:last-child { margin-bottom: 0; }

ul, ol {
  padding-left: 20px;
  margin-bottom: 12px;
}
li { margin-bottom: 4px; }

/* Fact grid for client overview */
.fact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  margin-top: 8px;
}
.fact-item {
  background: #f4f4f4;
  border-radius: 6px;
  padding: 12px 16px;
}
.fact-item .label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #888;
  margin-bottom: 2px;
}
.fact-item .value {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}

/* Two-column layout */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
@media (max-width: 1023px) {
  .two-col { grid-template-columns: 1fr; }
}

/* Audience cards */
.audience-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.audience-card {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 16px;
}
.audience-card h3 {
  font-size: 12px;
  margin-bottom: 10px;
  border: none;
  padding: 0;
}
.audience-card ul { margin-bottom: 0; }

/* Table */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  margin-top: 8px;
}
th {
  background: #f0f0f0;
  text-align: left;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #555;
  border-bottom: 2px solid #ddd;
}
td {
  padding: 10px 14px;
  border-bottom: 1px solid #eee;
  vertical-align: top;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fafafa; }

/* Structure template steps */
.structure-steps {
  counter-reset: step;
  list-style: none;
  padding-left: 0;
}
.structure-steps li {
  counter-increment: step;
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}
.structure-steps li:last-child { border-bottom: none; }
.structure-steps li::before {
  content: counter(step);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e8e8e8;
  font-size: 12px;
  font-weight: 700;
  color: #555;
  margin-top: 2px;
}

/* Quality / mistake items */
.criteria-list {
  list-style: none;
  padding-left: 0;
}
.criteria-list li {
  display: flex;
  gap: 10px;
  padding: 10px 14px;
  background: #f9f9f9;
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 14px;
}
.criteria-list.pass li::before {
  content: "✓";
  color: #2e7d32;
  font-weight: 700;
  min-width: 16px;
}
.criteria-list.fail li::before {
  content: "✗";
  color: #c62828;
  font-weight: 700;
  min-width: 16px;
}

/* Writing rules */
.rules-list {
  list-style: none;
  padding-left: 0;
}
.rules-list li {
  padding: 10px 14px;
  border-left: 3px solid #1a1a1a;
  margin-bottom: 8px;
  background: #f9f9f9;
  border-radius: 0 6px 6px 0;
  font-size: 14px;
}
.rules-list li strong { display: block; margin-bottom: 2px; }

/* Sample passages */
.sample {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}
.sample:last-child { margin-bottom: 0; }
.sample-label {
  background: #f0f0f0;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #555;
}
.sample blockquote {
  border-left: 4px solid #1a1a1a;
  margin: 0;
  padding: 16px 20px;
  background: #fff;
  font-style: italic;
  font-size: 15px;
  line-height: 1.65;
  color: #333;
}
.sample .annotation {
  padding: 12px 16px;
  background: #fffbf0;
  border-top: 1px solid #f0e8c8;
  font-size: 13px;
  color: #555;
}
.sample .annotation strong { color: #1a1a1a; }

/* Vocab tags */
.vocab-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.vocab-tag {
  background: #f0f0f0;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 13px;
  color: #444;
}

/* CTA avoid list */
.avoid-list {
  list-style: none;
  padding-left: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.avoid-list li {
  background: #fff0f0;
  border: 1px solid #fcc;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 13px;
  color: #c62828;
  margin-bottom: 0;
}

/* Footer */
footer {
  text-align: center;
  padding: 32px;
  font-size: 12px;
  color: #aaa;
}
```

**Exact section IDs and nav links:**

```html
<!-- Nav links (inside <nav>) -->
<a href="#client-overview">1. Client</a>
<a href="#products">2. Products</a>
<a href="#audience">3. Audience</a>
<a href="#voice">4. Voice & Tone</a>
<a href="#content-type">5. Content Type</a>
<a href="#quality">6. Quality Criteria</a>
<a href="#mistakes">7. Common Mistakes</a>
<a href="#writing-rules">8. Writing Rules</a>
<a href="#proof">9. Proof Elements</a>
<a href="#cta">10. CTA Guidelines</a>
<a href="#samples">11. Sample Passages</a>

<!-- Section IDs -->
<section id="client-overview"> ... </section>
<section id="products"> ... </section>
<section id="audience"> ... </section>
<section id="voice"> ... </section>
<section id="content-type"> ... </section>
<section id="quality"> ... </section>
<section id="mistakes"> ... </section>
<section id="writing-rules"> ... </section>
<section id="proof"> ... </section>
<section id="cta"> ... </section>
<section id="samples"> ... </section>
```

- [ ] **Step 2: Verify scaffold renders**

Open `Client G-content-brief.html` in a browser (double-click the file or use `start Client G-content-brief.html` in Bash).

Expected: Nav bar visible and sticky on scroll. 11 empty section cards visible. No broken layout.

---

## Task 2: Populate all 11 content sections

**Files:**
- Modify: `c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/client-g-content-brief.html`

All content is sourced from the spec at `docs/superpowers/specs/2026-04-02-Client G-content-brief-design.md`. Do not invent or rephrase — copy exactly.

- [ ] **Step 1: Section 1 — Client Overview**

Use `.fact-grid` layout. Each piece of data is a `.fact-item` with `.label` and `.value`. Items:

```
Brand Name        → Client G
Industry          → Home Improvement / Fly Screens / Window Furnishings
Market            → Australia
Business Type     → B2C
Website           → clientg.example.com (linked)
Location          → Hornsby NSW 2077
Phone             → 1300 884 842
ABN               → 00000000000
Writing Language  → Australian English
Rating            → 4.2 / 5 stars
In Business       → 30+ years
Ownership         → Family-owned
Made in           → 100% Australian made
Warranty          → 7-year product warranty
Proprietary Brand → ALLEGRO™ pleated screens
```

- [ ] **Step 2: Section 2 — Products & Pricing**

Use a `<table>` with columns: Product | Price Range | Notes.

```
ALLEGRO™ Pleated Insect Screens  | $1,100–$9,500  | Proprietary brand. Trademark symbol always required.
Retractable Fly Screens          | $490–$2,000    | —
Frame colours (standard)         | No extra charge | 100+ colours — key differentiator
Frame colours (premium)          | Additional cost | 200+ colours
Mesh — stainless steel security  | —              | For apartments where security is priority
Mesh — fibreglass                | —              | For villas near water — rust/debris resistant
Installation                     | —              | Professional only. Free on-site consultation offered.
```

- [ ] **Step 3: Section 3 — Target Audience Persona**

Use `.audience-grid` (2×2 grid) with four `.audience-card` blocks:

- **Who they are** — prose paragraph
- **Already knows** — bullet list
- **Struggling with** — bullet list
- **Sceptical of** — bullet list

Then below the grid, a full-width block for **Responds to** as a bullet list. Use exact content from spec.

- [ ] **Step 4: Section 4 — Voice & Tone Profile**

Use `.two-col` layout:
- Left column: Tone, Sentence Patterns, Vocabulary (use `.vocab-tags` for the word list), Opening Style
- Right column: Closing Style, Proof Style

Each sub-item uses an `<h3>` label followed by `<p>` or tag list.

- [ ] **Step 5: Section 5 — Content Type: Client G Blog Post**

Two parts:
1. Metadata row using `.fact-grid`: Slug, Word Count, Primary Intent, Business Context, Audience Mindset
2. Structure template using `.structure-steps` ordered list with the 5 steps from the spec

- [ ] **Step 6: Section 6 — Quality Criteria**

Use `.criteria-list.pass` (green checkmark prefix). 6 items from spec. Intro line: "Pass/fail standards applied at the Critique stage of the content pipeline."

- [ ] **Step 7: Section 7 — Common Mistakes**

Use `.criteria-list.fail` (red ✗ prefix). 5 items from spec. Intro line: "Failure patterns to watch for in AI-generated output for this client."

- [ ] **Step 8: Section 8 — Writing Rules**

Use `.rules-list`. Each `<li>` has a `<strong>` rule name followed by the explanation on the next line. 9 rules from spec (includes the blockquote rule for direct quotes).

- [ ] **Step 9: Section 9 — Proof & Authority Elements**

Use `<table>` with columns: Credential | Usage Note. 8 rows from spec. Intro line: "Approved credentials and how to deploy them in content."

- [ ] **Step 10: Section 10 — CTA Guidelines**

Two parts:
1. Bullet list of 4 positive rules (One CTA, frame as guidance, connect to topic, offer free consultation)
2. **Avoid** section using `.avoid-list` pill tags: "Buy now", "Shop our range", "Don't miss out", "urgency language", "repeated CTAs"

Include the exact example CTA from spec as a `<blockquote>`: "As industry professionals, we can help you choose the right fly screen based on both your personal needs and preferences."

- [ ] **Step 11: Section 11 — Sample Passages**

4 `.sample` blocks. Each has:
- `.sample-label` — e.g. "Example 1 — Benefit + aesthetic pairing"
- `<blockquote>` — exact passage text from spec
- `.annotation` — `<strong>What's correct:</strong>` followed by annotation text from spec

- [ ] **Step 12: Commit**

```bash
git add "c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/client-g-content-brief.html"
git commit -m "feat: add Client G content brief HTML"
```

Note: This directory is not a git repo. Skip the commit step — proceed directly to Task 3.

---

## Task 3: Visual verification

**Files:**
- Read: `c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/client-g-content-brief.html` (browser)

- [ ] **Step 1: Open in browser**

```bash
start "c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/client-g-content-brief.html"
```

- [ ] **Step 2: Check nav**

Expected: All 11 nav links visible. Clicking each link scrolls to the correct section. Nav stays sticky on scroll.

- [ ] **Step 3: Check each section**

Walk through sections 1–11 and confirm:
- Section numbers and headings display correctly
- `.fact-grid` items render as cards (Section 1, 2 metadata)
- Tables have correct columns and all rows present (Sections 2, 9)
- Audience grid is 2×2 on 1280px (Section 3)
- Vocab tags render as pills (Section 4)
- Structure steps show numbered circles (Section 5)
- Quality criteria show green ✓ (Section 6)
- Common mistakes show red ✗ (Section 7)
- Writing rules show left-border bars (Section 8)
- CTA avoid items render as red pills (Section 10)
- Sample passages show blockquote + yellow annotation panel (Section 11)

- [ ] **Step 4: Fix any layout issues found**

If any section is malformed — missing content, broken layout, truncated text — fix in the HTML file and recheck.

---

## Task 4: Upload to GitHub

**Files:**
- Read: `c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/client-g-content-brief.html`

- [ ] **Step 1: Invoke `github-upload` skill**

Use the `github-upload` skill with these resolved arguments:
- **File:** `c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/client-g-content-brief.html`
- **Repo:** `webprofits/jan-m`
- **Client folder:** `Client G`
- **Repo path:** `public/client-g/client-g-content-brief.html`
- **Commit message:** `Add Client G content brief v1`

Follow all steps in the skill: check if `public/client-g/` exists, check for existing file SHA, upload via PowerShell REST API.

- [ ] **Step 2: Confirm live URL**

Expected output from skill:
```
✅ Uploaded to GitHub: https://github.com/webprofits/jan-m/blob/main/public/client-g/client-g-content-brief.html
🌐 Live URL: https://webprofits.ai/jan-m/client-g/client-g-content-brief.html
```

Open the live URL in a browser and confirm the page loads correctly from GitHub Pages.

---

## Reference

- **Spec:** `docs/superpowers/specs/2026-04-02-Client G-content-brief-design.md`
- **Supabase project:** `REDACTED_PROJECT` (Content RAG, ap-southeast-2)
- **Client ID:** `171ad3d9-9e21-4514-b18d-724c8802ed76`
- **GitHub skill:** `github-upload` — uses `gh auth token`, account `janm-WP`
