# Design Spec: Client G Content Brief

**Date:** 2026-04-02
**Type:** Operational content reference document
**Output:** Single-page HTML file (`Client G-content-brief.html`)
**Audience:** Webprofits colleagues making editorial and pipeline decisions for Client G
**Published via:** `github-upload` skill

---

## Purpose

A single-page internal reference document containing everything needed to make decisions about how content is generated for Client G through the RAG content production pipeline. Not a visual brand guide — a practical operational brief colleagues can open in a browser while working.

---

## Format & Layout

- Single-page scrollable HTML
- Clean, readable internal doc style — no client branding applied
- Card-based sections with numbered headings for easy navigation
- Sticky top nav with jump links to each section
- System fonts (no external font dependencies)
- Alternating white / light-grey section backgrounds for visual separation
- Minimum readable width: 1024px, optimised for 1280px+ (local file, desktop/laptop only — mobile not in scope)

---

## Sections

### 1. Client Overview
Source: `clients` table

- Brand name: Client G
- Industry: Home Improvement / Fly Screens / Window Furnishings
- Market: Australia
- Business type: B2C
- Website: clientg.example.com
- Location: Hornsby NSW 2077
- Phone: 1300 884 842
- ABN: 00000000000
- Writing language: Australian English
- Key facts: 30+ years in business, 100% Australian made, family-owned, 7-year warranty, 4.2/5 star rating, proprietary ALLEGRO™ brand

---

### 2. Products & Pricing
Source: `clients.key_facts` (same field as Section 1 — Section 1 draws identity/contact data, Section 2 draws product/pricing data)

- ALLEGRO™ pleated insect screens: $1,100–$9,500
- Retractable fly screens: $490–$2,000
- Frame colours: 100+ standard (no extra charge), 200+ premium (additional cost)
- Mesh types: stainless steel security mesh, fibreglass mesh
- Installation: professional only, free on-site consultation offered

---

### 3. Target Audience Persona
Source: `audience_profiles` table

**Who they are:**
Sydney and greater metro area homeowners, aged ~35–65, owning or renovating a property. Mix of house and apartment/unit owners in mid-to-premium suburbs. Primary decision-maker. Often in a renovation, new build, or home upgrade phase.

**Already knows:**
What fly screens are. That standard screens exist but are often unsightly or poor quality. Basic home improvement concepts. Terms: fly screen, retractable, pleated, bifold, mesh.

**Struggling with:**
- Wanting fresh air without insects
- Finding screens that match home aesthetics
- Intrusive floor tracks (trip hazard)
- Large, unusual, or corner openings standard screens can't cover
- Unprofessional or unresponsive trade suppliers
- Products that fade or break quickly

**Sceptical of:**
- Cheap imported materials
- Hard-sell salespeople
- Ugly or bulky solutions
- No warranty backing
- Generic solutions requiring floor tile cutting or visible tracks

**Responds to:**
- Australian made + family business trust signals
- 30 years heritage and industry authority
- 7-year warranty
- Free on-site consultation (low-pressure framing)
- Professional installation with seamless finish
- Aesthetics-first language: "barely noticeable", "seamless integration", "enhances your home"
- Specific testimonials naming the installer and suburb
- Implicit competitor comparison ("other companies" vs Client G)

---

### 4. Voice & Tone Profile
Source: `voice_profiles` table

**Tone:**
Friendly, accessible, and informative. Positions Client G as a knowledgeable guide for homeowners rather than a pushy sales brand. Consistently approachable — writes as if advising a friend on home improvement decisions.

**Sentence patterns:**
Medium-length sentences mixed with shorter declarative statements. Frequent use of "you" and "your home". Common pattern: state a benefit or point, then explain why it matters to the reader. Generally active voice.

**Vocabulary preferences:**
aesthetics, liveability, complement, versatile, sleek, sophisticated, stylish, practical, enhance, transform. Avoids technical jargon. Pairs functional benefits with aesthetic ones. "Not only… but also…" is a recurring construction.

**Opening style:**
Opens with a broad, relatable statement about a home improvement challenge or aspiration. Sets context before narrowing to the specific topic. Often acknowledges a common oversight or concern.

**Closing style:**
Ends with a soft invitation to contact Client G, framed as expert guidance rather than a sales pitch. Brief and non-pushy.

**Proof style:**
Company heritage and experience claims: "first company to bring the style to Australia", "30 years as Australia's leading supplier". Product capability claims. No external statistics or customer testimonials in blog format. Authority derived from longevity.

---

### 5. Content Type: Client G Blog Post
Source: `content_types` table

- **Slug:** Client G-blog-post
- **Word count:** 600–1,200
- **Primary intent:** Informational
- **Purpose:** Help Sydney homeowners solve a specific home improvement problem or make a better purchase decision — with Client G fly screens introduced as the natural conclusion, not the opening pitch.
- **Business context:** Drives organic traffic from homeowners researching home improvement decisions. Top-of-funnel entry point to product pages and quote requests.
- **Audience mindset:** Not yet ready to buy — gathering information, comparing options, or seeking reassurance.

**Structure template:**
1. Hook — relatable homeowner scenario or overlooked problem (1–2 paragraphs)
2. Context — what this post covers and why it matters (1 paragraph)
3. H2 main sections × 3–6 (150–250 words each) — types, options, tips, considerations
   - H3 sub-items within each main section where relevant
4. Optional: Practical application — how to choose / what to do next
5. Soft CTA — Client G product as logical conclusion + contact/quote prompt

---

### 6. Quality Criteria
Source: `content_types.quality_criteria`

Pass/fail standards applied during the Critique stage:

1. Opens with a homeowner scenario — reader sees their own problem before Client G appears.
2. Client G introduced as logical solution after the category is established — never in the first two paragraphs.
3. Specific credentials used (ALLEGRO™, 30 years, Australian made) rather than vague quality claims.
4. Each H2 covers a distinct angle — not rephrasing the same point.
5. Post is genuinely useful regardless of purchase decision.
6. CTA connects the specific post topic to the specific Client G product that solves it.

---

### 7. Common Mistakes
Source: `content_types.common_mistakes`

Failure patterns to watch for in AI-generated output:

1. Client G mentions too early or too frequent — reads as advertorial.
2. Generic home improvement content with no Client G angle — could appear on any décor blog.
3. Flat heading structure (all H2, no H3) — thin and hard to scan.
4. CTA mid-content or repeated — feels pushy for an informational post.
5. Opening starts with product/brand not reader problem — loses the reader immediately.

---

### 8. Writing Rules
Source: `voice_profiles` + pipeline standards (`system-base.md`)

- **Australian English** — spellings: colour, liveability, recognise, organisation, etc.
- **No em dashes** — rephrase or use a comma instead
- **Active voice** throughout — avoid passive constructions
- **Second-person address** — "you" and "your home", not "homeowners" or "one"
- **"Not only… but also…"** is an approved recurring construction for pairing functional + aesthetic benefits
- **No statistics from unnamed sources** — only use verifiable claims or company-owned facts
- **No jargon** — accessible home improvement vocabulary only
- **Soft CTA at close only** — one CTA, at the end, framed as expert guidance not sales pitch
- **Blockquote format** for any direct quotes (e.g. from Jorge Henao, owner)

---

### 9. Proof & Authority Elements
Source: `voice_profiles.proof_style` + `clients.key_facts`

Approved credentials and how to use them:

| Credential | Usage note |
|---|---|
| "30+ years in business" | Use to establish authority before introducing the product. Not a throwaway line. |
| "Australia's leading supplier" | Acceptable as a heritage claim — not as a current ranking assertion without source. |
| "First company to bring [product] to Australia" | Use for ALLEGRO™ pleated screens specifically. |
| "100% Australian made" | Use when differentiating from cheap imports — connects directly to audience scepticism. |
| "Family-owned" | Use as a trust signal alongside heritage. Pairs well with low-pressure framing. |
| "7-year warranty" | Use to address durability concerns. Strongest proof point for the sceptical buyer. |
| ALLEGRO™ | Always use the trademark symbol. Specific product name — not a generic term. |
| "4.2/5 star rating" | Use sparingly and with context — not as a lead claim. |

---

### 10. CTA Guidelines
Source: `voice_profiles.closing_style` + `content_types.quality_criteria` (criterion 6) + `content_types.common_mistakes` (mistake 4)

- **One CTA per post, at the close only** — no mid-content interruptions
- **Frame as expert guidance**, not a sales push: "As industry professionals, we can help you choose the right fly screen based on both your personal needs and preferences."
- **Connect the CTA to the post topic** — e.g. a post about ventilation ends with screens as the natural ventilation solution, not a generic "contact us"
- **Offer the free on-site consultation** as the low-pressure entry point
- **Avoid:** "Buy now", "Shop our range", "Don't miss out", urgency language, repeated CTAs

---

### 11. Sample Passages
Source: `voice_profiles.sample_passages` + `content_chunks`

Annotated examples of correct Client G voice from real published content:

**Example 1 — Benefit + aesthetic pairing (the "not only… but also…" pattern)**
> "By making the right choice, your fly screens will not only keep insects out but also enhance your home's aesthetics."

*What's correct:* Functional benefit (pest control) paired with aesthetic benefit using the "not only… but also…" construction. Direct second-person address ("your fly screens"). No brand mention required — product speaks for itself.

---

**Example 2 — Problem → product authority statement**
> "There is no better deterrent for unwanted pests than a retractable fly screen. These screens have a proven track record of keeping creepy crawlies out of your home. The added bonus is that their sleek and sophisticated design makes retractable fly screens not only a great way to control pests, but an eye pleasing aesthetic for your home."

*What's correct:* Leads with the problem solution, adds aesthetic benefit second. "Not only… but also…" construction used naturally. Vocabulary: sleek, sophisticated — matches approved word list.

---

**Example 3 — Small space / liveability framing**
> "One of the best ways to transform small spaces is by opting to install fly screens. Offering both functional and aesthetic benefits, these simple additions can drastically improve liveability."

*What's correct:* Opens on the reader's problem (small spaces), not the product name. "Liveability" is a key vocabulary word — use it. Functional and aesthetic benefits paired in a single sentence. Product introduced as the solution only after the problem category is established.

---

**Example 4 — Heritage authority + soft close**
> "Form and function are critical parts of our design process. For the last 30 years, Client G has been Australia's leading supplier of high-quality retractable fly screens."

*What's correct:* Heritage claim ("30 years") used to establish authority, not as a sales opener. "Form and function" pairs the two Client G brand pillars in a single phrase. First-person "our" is appropriate here because the brand has already been established in the post. Suitable for a closing or transition paragraph — not an opener.

---

## File Output

- **Filename:** `Client G-content-brief.html`
- **Local location:** `c:/Users/marke/OneDrive/Documents/Claude VS/NEw Model/client-g-content-brief.html`
- **GitHub repo:** `webprofits/jan-m`
- **Repo path:** `public/client-g/client-g-content-brief.html`
- **Live URL:** `https://webprofits.ai/jan-m/client-g/client-g-content-brief.html`
- **Published via:** `github-upload` skill after build

---

## Out of Scope

- Visual brand guide (colours, logo rules, typography system)
- Competitor analysis
- SEO keyword strategy
- Paid advertising guidelines
- Content calendar or topic planning
