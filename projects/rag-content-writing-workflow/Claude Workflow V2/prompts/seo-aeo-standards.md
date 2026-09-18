# SEO & AEO Standards

Universal on-page standards for every piece of content in the pipeline. Apply regardless of client, industry, or content type. Content-type-specific variations (schema type, TOC threshold, table placement) live in `content_types.seo_requirements` in the database.

Referenced by: Outline, Draft, Deliverables, Rewrite, Critique agents.

---

## The Governing Principle

Structure is the new keyword density. How content is organised now determines ranking, snippet eligibility, featured snippet wins, and AI citation probability as much as what it says. Every structural decision below exists because it directly affects one or more of those outcomes.

---

## 1. Title Tags

**Character target:** 51–60 characters. Google measures pixel width, not characters — avoid wide letters (W, M) stacking. Treat 55 characters as the safe midpoint.

**Keyword placement:** Primary keyword at or near the start. On mobile, titles truncate around character 40. The keyword signal and the CTR trigger both need to land before truncation.

**Format patterns that lift CTR:**
- Numbers: "7 Ways to..." or "11 Types of..." outperform generic titles consistently
- Year signals: "(2025)" or "Updated 2025" confirms freshness and boosts CTR
- Parentheses over brackets: Google drops brackets 40%+ more often than parentheses — use `(With Examples)` not `[With Examples]`
- Negative framing for cautionary queries: "X Mistakes to Avoid" often outperforms "How to Do X" when users are loss-averse, not aspirational
- Proposition over label: "What Are Asset Classes? 16 Types Explained" beats "Asset Class Guide"

**Separator:** Use `–` (en dash) not `|` (pipe). Google removes pipes 41% of the time; en dashes 19.7%.

**Brand:** Include at the end after a dash, only if space allows. Never in the middle.

**Rewrite prevention:** Google rewrites 61% of title tags. Primary cause: mismatch between title tag and H1. The H1 and title must be thematically consistent — not identical, but making the same argument. When they align closely, rewrite rates drop materially.

**Never:**
- Stuff keyword variants ("private equity investment australia investing")
- Produce a vague label ("Services Page", "Blog")
- Use clickbait that the content doesn't deliver on — Google will rewrite it and the page will underperform regardless

---

## 2. Meta Descriptions

**Character target:** 120–158 characters. Mobile truncates at ~120 — the value proposition must land within the first 120 characters. Treat everything after as reinforcement.

**Google rewrites ~70% of meta descriptions** for informational queries, pulling from whichever page section it thinks best answers the query. This means: the first 100 words of body copy are effectively the real meta description for most queries. Optimise both.

**Query keyword bolding:** Google bolds matched terms in snippets. Including the primary keyword (and close variants) in the meta description triggers this even when Google keeps your version — making the result visually stand out.

**Structure by intent:**

| Intent | Structure |
|---|---|
| Informational | [Confirm the answer exists] + [key differentiator or scope] + [softer CTA] |
| Commercial investigation | [What the page compares/covers] + [unique angle] + [action CTA] |
| Transactional | [Direct value proposition] + [trust signal] + [direct CTA] |

**CTA patterns by intent:**
- Informational: "Learn...", "Understand...", "See how...", "Find out..."
- Commercial: "Compare...", "See which...", "Explore..."
- Transactional: "Get started", "View options", "Apply today"

Never use the same CTA pattern across all pages. Mismatched intent CTAs reduce CTR.

**Never duplicate** meta descriptions across pages — Google treats duplicate metas as a quality signal issue.

---

## 3. Headings (H1 / H2 / H3)

### H1
- One per page, no exceptions
- Primary keyword included, ideally near the start
- 20–70 characters
- Thematically consistent with title tag (not identical — different vehicles, same destination)
- The H1 is the on-page heading; the title tag is the browser tab and SERP display — they can read differently while meaning the same thing

### H2 — the semantic architecture
- Each H2 must be a **standalone proposition**, not a label
- Test: read only the H2s. If they form a coherent argument or story, they're propositions. If they're a list of topics, they're labels.
- Include keyword variants and semantically related terms — not the exact primary keyword repeated on every H2 (over-optimisation signal)
- Phrase as the user's question where natural: "How Does Private Equity Work?" not "Private Equity Mechanics"
- Each H2 section must make sense extracted from context — AI systems pull sections independently

### H3
- Always nested under H2, never jump from H1 to H3
- More specific and granular than H2
- For FAQ sections: phrase H3s as literal questions — these become featured snippet sub-section candidates and AEO extraction targets
- Long-tail keyword variations and specific entity mentions belong at H3 level

### The standalone heading test
Strip the body copy. Read H1 → all H2s → all H3s in sequence. Ask: does this communicate the page's complete argument? If yes, the heading structure is sound for both UX and AI extraction. Run this check before finalising any outline.

---

## 4. Content Structure & Scannability

### BLUF — Bottom Line Up Front
Lead with the answer. Every H2 section opens with its conclusion, not its preamble.

**The pattern (non-negotiable for every major section):**
1. H2 or H3 heading as a proposition or question
2. **40–60 word direct answer paragraph** — complete, standalone, no assumed context
3. Explanation, evidence, nuance below

This 40-60 word block is your featured snippet candidate, your AI citation block, and your user retention hook. Do not start sections with "In this section we'll cover...", "When it comes to X...", or "There are many factors...". These burn the citation window.

Research signal: pages with sections of 120-180 words between headings receive 70% more AI citations than fragmented pages. This is the structural density target — enough depth to be substantive, enough segmentation to be parseable.

### Paragraph length
- Body paragraphs: 3–5 sentences, 2–4 lines on screen maximum
- Answer blocks (BLUF paragraphs): 40–60 words exactly
- No wall-of-text paragraphs — if a concept needs more than 5 sentences, use a sub-heading or list

### Tables
Use tables for any data that involves comparison, specification, or side-by-side evaluation. Comparison data in prose is almost always worse than the same data in a table. Tables also win **table featured snippets**.

Format rules:
- Clear column headers in the first row
- No merged cells — extraction needs clean HTML
- 2-column tables (label | value) and multi-column comparison tables both work
- Include tables early in relevant sections — not buried at the end

### Lists
Use bullet or numbered lists for:
- Steps (numbered, starts with imperative verb)
- Features or attributes (3+ items that don't require narrative flow)
- Examples (when the connection between items is parallel, not sequential)

Do not use lists for concepts that need explanation — prose sentences communicate causality and nuance that bullets strip out.

### Scannability rules — when to break out of prose

**Parenthetical trap:** If a sentence contains two or more parenthetical explanations — e.g. `NextEra Energy (US renewable electricity), Transurban (ASX:TCL, toll roads), American Tower (US telecom towers)` — restructure as a bullet list. The parenthetical becomes the descriptor on the same line:
```
- **NextEra Energy** — US renewable and conventional electricity
- **Transurban Group (ASX:TCL)** — Australian toll roads including CityLink and WestConnex
- **American Tower Corp** — US telecom tower infrastructure
```

**Allocation / breakdown data:** Percentage splits and allocations always go in a table or formatted list — never in a sentence. "50% utilities, 25% transport, 25% energy" becomes:

| Sector | Allocation | What it includes |
|---|---|---|
| Utilities | ~50% | Electricity, water, gas networks |
| Transportation | ~25% | Toll roads, airports, railroads |
| Energy infrastructure | ~25% | Pipelines and storage |

**Named items rule:** Three or more named items that each need a brief explanation → bullet list, not comma-separated prose.

**Sentence parenthetical limit:** Maximum one parenthetical per sentence. If a second is needed, either start a new sentence or restructure as a list.

### Bolding
Legitimate for: genuinely critical terms on first mention, key figures that readers scan for, call-outs that stand alone as takeaways.

Maximum 2–3 bold instances per section. More than that and nothing stands out.

### Table of Contents
For content over ~1,500 words: include a TOC with anchor jump links near the top of the page. Generates sitelinks-style anchor links in SERP for some queries. Improves time-on-page. Signals structured content to Google. TOC jump links also appear as navigation in AI Overviews.

---

## 5. AEO — Answer Engine Optimisation

AI Overviews appear in ~25% of searches. When shown, CTR on traditional results drops ~50%. Ranking in the top 10 no longer guarantees AI citation — pages ranked 11–100+ are now cited at near-equal rates to positions 1–10. Structure and entity signals determine citation probability more than rank.

### The answer block (most important single change)
Every major section needs a 40–60 word standalone answer at the top (covered in §4 above). This is the primary citation extraction pattern for all major AI systems — Google AI Overviews, ChatGPT, Perplexity.

### Entity density
Pages with 15+ recognised named entities show 4.8x higher AI citation probability.

Named entities include: people (named experts, founders, researchers), organisations (named companies, institutions, regulatory bodies), products (named products, tools, services), places (cities, countries, regions), concepts with defined identities (named frameworks, standards, legislation).

The Research Brief must surface named entities from research data. The Draft must use them — not paraphrase them away.

### Factual specificity
Concrete numbers with named sources outperform vague claims for AI citation. The pattern:
> "In 2024, [named institution] found that [specific number] of [specific group] [specific outcome]"

beats:
> "Research shows that many businesses experience significant benefits"

Perplexity specifically: content in callout or highlighted sections has 2.3x higher citation rate. Significant statistics should be formatted as callout blocks or bold pull quotes where the content type allows.

### FAQPage schema
FAQPage schema no longer produces rich results in SERPs for general content (Google restricted this in 2023). However, pages with FAQPage schema are 3.2x more likely to appear in Google AI Overviews. Implement it on all FAQ sections for AEO benefit.

Minimum FAQ per article: 3 questions. Questions should mirror People Also Ask data from the SERP research. Answers: 40–60 words each, standalone, directly answering the question.

### Article/content freshness signals
`dateModified` in Article schema must be accurate. AI systems check content freshness. Do not inflate modification dates — inaccurate dates are a trust signal against the content.

### Author entity signals
For Article schema: author must be a `Person` type with `name` and `url` (linking to the author's bio or profile page). Author entity recognition contributes to E-E-A-T signals for AI systems. Generic "Editorial Team" authors are a weaker signal than named individuals.

---

## 6. Internal Linking

- 2–3 contextual internal links per 1,000 words
- Anchor text: descriptive, includes the target page's primary keyword naturally
- Link to related content that genuinely extends the topic — not just to hub pages
- Never use: "click here", "read more", "learn more", "this article" as anchor text
- Internal link targets come from `context.published_pages` — use only URLs from this list
- Place links where they appear contextually relevant, not forced at the end of paragraphs

---

## 7. URL / Slug

- Lowercase, hyphens, no special characters
- Contains the primary keyword
- 3–5 words is ideal — shorter slugs outperform long descriptive ones
- No stop words (a, the, and, or, of, in, to)
- Match the H1 intent — same topic, same keyword
- Stable: once published, don't change slugs without 301 redirects

---

## 8. Schema Markup (Guidance — implementation varies by content type)

Content-type-specific schema is specified in `content_types.seo_requirements`. Universal guidance:

| Schema type | When to use | Priority |
|---|---|---|
| Article / BlogPosting | All editorial content | High |
| FAQPage | Any page with a FAQ section | High (AEO) |
| BreadcrumbList | All pages | High |
| HowTo | Step-by-step guides | Medium |
| Organization / WebSite | Sitewide (once) | High |

Article schema must include: `headline`, `datePublished`, `dateModified`, `author` (Person with name + url), `image`.

JSON-LD format only (not Microdata). Place in `<script type="application/ld+json">` tags.

---

## 9. SEO/AEO Critique Checklist

When the Critique agent evaluates a draft, it checks these dimensions in addition to content quality:

| Check | Pass | Fail |
|---|---|---|
| H1 present, primary keyword included, thematically matches title intent | ✓ | H1 is a label, missing keyword, or identical to title tag |
| Every major section opens with a 40-60 word BLUF block | ✓ | Sections open with preamble |
| H2s are benefit-focused propositions with a verb, 5-8 words, specific (number/outcome/named concept) | ✓ | H2s are labels, lack a verb, are too vague, or exceed 8 words |
| H2s read as a coherent argument when extracted from body copy | ✓ | H2s are a disconnected list of topic labels |
| No paragraph exceeds 5 sentences | ✓ | Wall-of-text paragraphs present |
| Comparison data in tables, not prose | ✓ | Comparison buried in paragraph |
| Allocation/breakdown data (%, splits) in table or list, not sentence | ✓ | "50% utilities, 25% transport..." in a sentence |
| 3+ named items with descriptors in a bullet list, not prose | ✓ | Named items comma-separated in a paragraph |
| Max one parenthetical per sentence | ✓ | Sentences with 2+ parenthetical explanations |
| FAQs phrased as literal questions | ✓ | FAQs phrased as labels |
| Named entities present (people, orgs, data sources) | ✓ | Generic or vague sourcing throughout |
| No fabricated URLs | ✓ | URLs not in research brief appear |
| Internal links use descriptive anchor text | ✓ | Generic anchor text ("click here") |
| Title is 51-60 chars with keyword near start | ✓ | Title too long / keyword buried |
| Meta is 120-158 chars with keyword in first 120 | ✓ | Meta too long / keyword missing |
