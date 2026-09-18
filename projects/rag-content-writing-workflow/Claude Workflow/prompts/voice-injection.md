# Voice Profile Injection Template

How to inject `voice_profiles` data into agent prompts. Used by Draft, Rewrite, and Critique agents.

---

## Template Block

Add this block to the Draft and Rewrite agent prompts, populated from the `voice_profiles` table:

```
## Client Voice Profile

{{#if voice_profile}}
Write in the client's established voice. Do not default to a generic professional tone.

**Tone:** {{voice_profile.tone_description}}

**Sentence patterns:** {{voice_profile.sentence_patterns}}

**Vocabulary preferences:** {{voice_profile.vocabulary_preferences}}

**Opening style:** {{voice_profile.opening_style}}

**Closing style:** {{voice_profile.closing_style}}

**How to use proof/evidence:** {{voice_profile.proof_style}}

**Sample passages to calibrate from:**
{{voice_profile.sample_passages}}
{{else}}
No voice profile exists for this client. Write in a clear, direct, professional tone. Avoid corporate jargon. Prefer active voice and specific language over passive and vague.
{{/if}}
```

---

## How It Interacts With Other Standards

The voice profile controls **how** content is written, not **what** it contains or **how it is evaluated**.

| Layer | Controls | Source |
|---|---|---|
| Universal quality standards | Evidence, specificity, E-E-A-T, no filler | `prompts/eeat-criteria.md` |
| Content type criteria | Structure, SEO requirements, CTA, quality_criteria, common_mistakes | `content_types` table |
| Voice profile | Tone, vocabulary, sentence patterns, proof style | `voice_profiles` table |
| V2O override | Any specific requirements from client transcripts/notes | User input at run time |

If V2O instructions conflict with the voice profile, V2O wins.
If voice profile instructions conflict with universal quality standards, the universal standards win on factual accuracy (e.g., even if the client voice is "informal," all claims still need sources). Voice controls style, not accuracy.

---

## For the Critique Agent

The Critique agent evaluates voice alignment separately from content quality:

```
## Voice Alignment Check

Does the draft match the client's voice profile?

- Tone: [matches / partially matches / doesn't match] — explain
- Sentence patterns: [matches / partially matches / doesn't match] — explain
- Vocabulary: [matches / partially matches / doesn't match] — explain
- Proof style: [matches / partially matches / doesn't match] — explain

Overall voice alignment: [Strong / Acceptable / Needs Rewrite]

If "Needs Rewrite": identify the 2–3 specific passages most out of voice and explain what's wrong.
```
