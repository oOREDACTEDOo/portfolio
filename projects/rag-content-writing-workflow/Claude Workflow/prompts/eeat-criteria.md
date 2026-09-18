# Universal Content Quality Standards

These standards apply to all content regardless of client, content type, or topic. They define the baseline for what constitutes publishable quality. Client-specific criteria (loaded from `content_types.quality_criteria`) layer on top of these.

---

## The Core Test

Before anything else, ask: **does this content make the reader genuinely better informed than they were before they read it?**

If the answer is "they already knew most of this" — it fails. If the answer is "they now understand something they didn't" — it passes.

---

## 1. Specificity Over Vagueness

Every claim must be specific. Vague claims waste words and erode trust.

**Fails:**
- "Returns can be significant"
- "Many businesses choose this option"
- "The market has grown significantly in recent years"
- "Studies show..."
- "Costs are lower than traditional approaches"

**Passes:**
- "Average annual returns of 7.2% over the past decade ([source name], [year])"
- "38% of [client market] businesses report [specific outcome] ([industry body], [year])"
- "The [market] [sector] market grew from $X to $Y between [years] ([named research firm])"
- "A [year] [named institution] study of [N] [subject] found..."

If a claim cannot be made specific, either find the data or remove the claim.

---

## 2. Evidence Standards

**Every factual claim requires one of:**
- A named source with year (e.g. "ATO 2023 statistics")
- A named institution (e.g. "Reserve Bank of Australia")
- A cited client case study with attribution
- Explicit flagging as opinion (e.g. "In our view..." or "Some analysts argue...")

Unattributed statistics are a red flag for AI-generated filler. When in doubt, flag for fact-check rather than include.

---

## 3. No Filler

Every paragraph must either advance the reader's understanding or advance the argument. Cut anything that doesn't.

**Filler patterns to eliminate:**
- Summary paragraphs that restate what was just said
- Transition paragraphs that bridge sections without adding content
- "In conclusion, as we have seen..." openings to conclusions
- Generic introductions: "In today's rapidly changing world...", "Now more than ever..."
- Rhetorical questions that aren't answered: "But what does this mean for you?"
- Hedge stacks: "It's worth noting that it may be possible that in some cases..."

**Test:** Remove the paragraph. Does the reader lose anything? If no, cut it.

---

## 4. Originality — Add Something Competitors Don't Have

Content that only aggregates what's already online has no reason to exist. Every piece must include at least one of:

- A comparison framework that makes a complex decision easier (table, matrix, decision tree)
- An angle or framing that competitors haven't used
- A counterintuitive point or common misconception addressed directly
- Client-specific insight, case study, or proprietary data
- Synthesis that connects two ideas others treat separately

If the entire piece could be assembled by scraping the top 5 search results — it's not good enough.

---

## 5. Reader-First Structure

Structure serves the reader's journey, not a content map. The reader's most important question gets answered first. Supporting detail follows.

**Structural rules:**
- Lead with the most important thing — not the background, history, or "what is X" definition
- Headings should be meaningful propositions, not just labels. "Why private equity underperforms in year 1" beats "Year 1 Performance"
- FAQ sections target real questions (sourced from PAA data and GSC queries), not invented ones
- Word count serves depth, not padding. A 1,500-word piece that's tight beats 2,500 words of filler

---

## 6. E-E-A-T Signals

Google's Quality Rater Guidelines assess Experience, Expertise, Authoritativeness, and Trustworthiness. Every piece should demonstrate:

**Experience:** Written as if by someone who has dealt with this topic in practice, not just researched it. Use of specific scenarios, real-world caveats, practitioner language.

**Expertise:** Correct use of technical terminology. Acknowledges nuance. Doesn't oversimplify. Demonstrates awareness of edge cases.

**Authoritativeness:** Cites authoritative sources. Links to primary research. Doesn't rely on other content aggregators as sources.

**Trustworthiness:** Balanced treatment of risks and benefits. Discloses limitations. Does not overclaim. Distinguishes general information from personalised advice where legally required.

---

## 7. Narrative Craft

Good content reads like it was written by a thinking human, not assembled from components.

**Principles:**
- Vary sentence length. Short sentences land. Longer sentences build context and connect ideas that belong together.
- Use concrete nouns and active verbs. Avoid noun-heavy abstractions ("the optimisation of capital allocation" → "investing capital better")
- Each section should have one controlling idea. If a section covers two ideas, split it.
- Write the way the audience thinks, not the way the topic is categorised. A CFO thinks about risk before opportunity. A first-time investor thinks about "do I lose my money" before returns.

---

## 8. Depth Calibration

Content depth should match keyword difficulty and audience expertise:

| KD Range | Audience | Required Depth |
|---|---|---|
| KD 0–30 | General / beginner | Comprehensive but accessible. Cover full topic. No assumed knowledge. |
| KD 30–60 | Informed / researching | Assume basic familiarity. Add nuance, comparisons, edge cases. |
| KD 60+ | Expert / competitor-ranked | Demonstrate genuine expertise. Original analysis. Primary sources. High information density. |

When search intent is informational: educate first, commercialise last.
When intent is commercial: the value proposition must be demonstrable, not asserted.

---

## 9. Critique Scoring Rubric

When evaluating content against these standards, score each dimension:

| Dimension | 1 — Fails | 2 — Acceptable | 3 — Strong |
|---|---|---|---|
| Specificity | Vague claims throughout | Some specifics, some vague | All claims specific and sourced |
| Evidence | No sources cited | Some sources, some unattributed | All factual claims sourced |
| No filler | Multiple filler paragraphs | Occasional filler | Tight throughout |
| Originality | Aggregates existing content | One original element | Clear differentiation from SERP |
| Structure | Reader has to hunt for answers | Logical but could be tighter | Reader's journey is effortless |
| E-E-A-T | Reads like AI aggregation | Some expertise signals | Demonstrates genuine authority |
| Narrative craft | Robotic or stilted | Readable but flat | Engaging and distinct |
| Depth | Superficial | Matches intent | Exceeds competitor depth |

**Minimum to pass:** No 1s. Average 2+. At least two 3s.

Content that scores any 1 must go back through rewrite — not just light editing.

---

## What These Standards Don't Cover

These are universal. They don't cover:
- **Client voice** — loaded from `voice_profiles` (tone, vocabulary, sentence patterns, proof style)
- **Content type requirements** — loaded from `content_types` (structure template, SEO requirements, CTA guidance, quality criteria, common mistakes)
- **Topic-specific requirements** — covered by research brief and outline agents

The complete quality picture for any piece = these universal standards + content_type.quality_criteria + voice_profiles fields.
