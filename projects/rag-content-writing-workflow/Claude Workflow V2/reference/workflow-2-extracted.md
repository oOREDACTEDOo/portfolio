# Workflow 2: New Content Generation — Complete Extraction
**Workflow ID:** 73lMIBHKbWIWwuNP
**Name:** New Content Generation
**Active:** true
**Last updated:** 2026-03-17
**Total nodes:** 29

---

## Pipeline Flow (Connection Map)

```
On form submission
  └── Get Client
        ├── Get Content Type ──────────────┐
        ├── Get Audience Profile ───────────┤
        ├── Get Voice Profile ──────────────┤
        ├── Get Published Pages ────────────┤
        ├── Embed Keywords → RAG Search ────┤
        ├── SERP Search ───────────────────┤→ Merge (8 inputs) → Merge Context
        ├── Tavily Stats ──────────────────┤
        └── [self] ──────────────────────────┘

Merge Context
  └── Coverage Check
        └── token cost (side branch — estimates context window usage)
              └── Research Brief
                    └── Outline
                          └── Draft
                                └── Critique
                                      └── Gap Research
                                            └── Rewrite
                                                  └── Fact Check
                                                        └── Deliverables
                                                              ├── Save to content_jobs (terminal)
                                                              └── Parse Image Queries
                                                                    └── Shutterstock Search
                                                                          └── Collect Images
                                                                                └── Format for Google Docs
                                                                                      └── Create Google Doc
                                                                                            └── Send a message (Slack, terminal)
```

**Note on token cost node:** It sits between Coverage Check and Research Brief but does NOT block or gate the pipeline — it's a diagnostic side-branch that estimates token usage of the context object. The pipeline continues through it to Research Brief.

---

## NODE-BY-NODE DETAIL

---

### NODE 1: On form submission
**Type:** `n8n-nodes-base.formTrigger`
**Form title:** New content generator.
**Form description:** Add in details to generate content of the specific type.

**Form fields:**

| Field | Type | Options |
|---|---|---|
| Client | dropdown | Client D, Client K, Client I |
| Content Type Slug | dropdown | asset_class_page, im-article, so-blog-post, jmc-blog-post |
| Target Keywords | text | (free text) |
| Topic | text | (free text) |
| Content Brief (V2O) | text (optional) | "Optional. Tell us anything specific this article needs to include, avoid, or reference. Plain language is fine — quotes, key topics, specific data sources, exclusions. Example: 'Use the quote from Jane Smith about risk management. Make sure we cover SMSF considerations. Don't mention competitor X.'" |

**Output fields passed downstream:**
- `$('On form submission').first().json['Client']`
- `$('On form submission').first().json['Content Type Slug']`
- `$('On form submission').first().json['Target Keywords']`
- `$('On form submission').first().json['Topic']`
- `$('On form submission').first().json['Content Brief (V2O)']`

---

### NODE 2: Get Client
**Type:** `n8n-nodes-base.supabase`
**Operation:** get
**Table:** `clients`
**Filter:** `brand_name = $('On form submission').first().json['Client']`
**Returns:** Full client row. Key fields used downstream: `id`, `brand_name`, `business_type`, `industry`, `market`, `website_url`, `target_audience_summary`, `key_facts`

---

### NODE 3: Get Content Type
**Type:** `n8n-nodes-base.supabase`
**Operation:** getAll (limit 1)
**Table:** `content_types`
**Filter:** `type_slug = $('On form submission').first().json['Content Type Slug']` (eq, allFilters)
**Returns:** Full content type row. Fields used: `type_name`, `purpose`, `audience_mindset`, `structure_template`, `seo_requirements`, `proof_elements`, `cta_guidance`, `internal_linking_rules`, `quality_criteria`, `common_mistakes`, `word_count_range`, `primary_intent`

---

### NODE 4: Get Audience Profile
**Type:** `n8n-nodes-base.supabase`
**Operation:** getAll (limit 1)
**Table:** `audience_profiles`
**Filter:** `client_id = $('Get Client').first().json.id` (eq, allFilters)
**Returns:** Fields used: `audience_name`, `role_or_persona`, `already_knows`, `struggling_with`, `skeptical_of`, `responds_to`, `reading_level`, `content_preferences`

---

### NODE 5: Get Voice Profile
**Type:** `n8n-nodes-base.supabase`
**Operation:** getAll (limit 1)
**Table:** `voice_profiles`
**Filter:** `client_id = $('Get Client').first().json.id`
**Returns:** Fields used: `sentence_patterns`, `vocabulary_preferences`, `structure_patterns`, `tone_description`, `opening_style`, `closing_style`, `proof_style`, `sample_passages`

---

### NODE 6: Get Published Pages
**Type:** `n8n-nodes-base.supabase`
**Operation:** getAll (limit 100)
**Table:** `published_content_map`
**Filter:** `client_id = $('Get Client').first().json.id` (eq, allFilters)
**Returns:** Fields mapped: `page_title → title`, `page_url → url`, `primary_keyword → keyword`, `content_type → type`

---

### NODE 7: Embed Keywords
**Type:** `n8n-nodes-base.httpRequest`
**Method:** POST
**URL:** `https://api.openai.com/v1/embeddings`
**Auth:** OpenAI API (predefined credential)
**Body parameters:**
- `model`: `text-embedding-3-small`
- `input`: `$('On form submission').first().json['Target Keywords']`

**Output used downstream:** `$('Embed Keywords').first().json.data[0].embedding`

---

### NODE 8: RAG Search
**Type:** `n8n-nodes-base.httpRequest`
**Method:** POST
**URL:** `https://REDACTED_PROJECT.supabase.co/rest/v1/rpc/match_content_chunks`
**Auth:** Supabase API key in headers (apikey + Authorization Bearer)
**API Key in use:** `REDACTED_SUPABASE_SERVICE_ROLE_KEY`

**Body parameters:**
- `query_embedding`: `$('Embed Keywords').first().json.data[0].embedding`
- `match_client_id`: `$('Get Client').first().json.id`
- `match_threshold`: `0.5`
- `match_count`: `20`

**Returns:** Up to 20 RAG chunks. Fields mapped in Merge Context: `chunk_text → text`, `context_prefix → context`, `source_article_title → sourceTitle`, `source_url → source`, `source_date → sourceDate`, `topic_tags → tags`, `asset_tags → assetTags`, `similarity → similarity`

---

### NODE 9: SERP Search
**Type:** `n8n-nodes-base.httpRequest`
**Method:** POST
**URL:** `https://api.dataforseo.com/v3/serp/google/organic/live/advanced`
**Auth:** Basic Auth (DataForSEO credentials)
**Body (JSON literal):**
```json
[{
  "keyword": "{{ $('On form submission').first().json['Target Keywords'] }}",
  "location_code": 2036,
  "language_code": "en",
  "device": "desktop",
  "depth": 10
}]
```
**Note:** `location_code: 2036` = Australia.

**Output processing in Merge Context:**
- Filters items by type `organic` → top 10 → `{title, url, description}`
- Filters items by type `people_also_ask` → `.title` array
- Filters items by type `related_searches` → `.items` flatmap

---

### NODE 10: Tavily Stats
**Type:** `n8n-nodes-base.httpRequest`
**Method:** POST
**URL:** `https://api.tavily.com/search`
**Body (JSON literal):**
```json
{
  "api_key": "REDACTED_TAVILY_API_KEY",
  "query": "{{ $('On form submission').first().json['Target Keywords'] }} Australia statistics data research",
  "search_depth": "advanced",
  "max_results": 3,
  "include_raw_content": true
}
```
**Output processing in Merge Context:** `raw_content` or `content` sliced to 6000 chars per result.

---

### NODE 11: Merge
**Type:** `n8n-nodes-base.merge`
**Number of inputs:** 8
**Inputs (by index):**
- 0: Get Client (self-loop)
- 1: Get Content Type
- 2: Get Audience Profile
- 3: Get Voice Profile
- 4: Get Published Pages
- 5: RAG Search
- 6: SERP Search
- 7: Tavily Stats

**Purpose:** Waits for all 8 parallel branches to complete before proceeding.

---

### NODE 12: Merge Context
**Type:** `n8n-nodes-base.code` (JavaScript)
**Purpose:** Assembles the unified context object passed to all downstream AI nodes.

**Full JS Code:**
```javascript
const client = $('Get Client').first().json;
const contentType = $('Get Content Type').first().json;
const audienceProfile = $('Get Audience Profile').first().json;
const voiceProfile = $('Get Voice Profile').first().json;
const formData = $('On form submission').first().json;

const publishedPages = $('Get Published Pages').all().map(item => ({
  title: item.json.page_title,
  url: item.json.page_url,
  keyword: item.json.primary_keyword,
  type: item.json.content_type
}));

const ragChunks = $('RAG Search').all().map(item => ({
  text: item.json.chunk_text,
  context: item.json.context_prefix,
  sourceTitle: item.json.source_article_title,
  source: item.json.source_url,
  sourceDate: item.json.source_date,
  tags: item.json.topic_tags,
  assetTags: item.json.asset_tags,
  similarity: item.json.similarity
}));

let serpData = {};
try {
  const serpItems = $('SERP Search').first().json.tasks?.[0]?.result?.[0]?.items || [];
  serpData = {
    organicResults: serpItems.filter(i => i.type === 'organic').slice(0, 10).map(i => ({
      title: i.title, url: i.url, description: i.description
    })),
    peopleAlsoAsk: serpItems.filter(i => i.type === 'people_also_ask').map(i => i.title),
    relatedSearches: serpItems.filter(i => i.type === 'related_searches').flatMap(i => i.items || [])
  };
} catch(e) {
  serpData = { organicResults: [], peopleAlsoAsk: [], relatedSearches: [] };
}

let tavilyData = [];
try {
  tavilyData = ($('Tavily Stats').first().json.results || []).map(r => ({
    title: r.title,
    url: r.url,
    content: (r.raw_content || r.content || '').slice(0, 6000)
  }));
} catch(e) { tavilyData = []; }

return [{
  json: {
    topic: formData['Topic'],
    targetKeywords: formData['Target Keywords'],
    v2o: formData['Content Brief (V2O)'] || '',
    client: {
      name: client.brand_name, type: client.business_type,
      industry: client.industry, market: client.market,
      website: client.website_url, audienceSummary: client.target_audience_summary,
      keyFacts: client.key_facts || ''
    },
    contentType: {
      name: contentType.type_name, purpose: contentType.purpose,
      audienceMindset: contentType.audience_mindset, structureTemplate: contentType.structure_template,
      seoRequirements: contentType.seo_requirements, proofElements: contentType.proof_elements,
      ctaGuidance: contentType.cta_guidance, internalLinkingRules: contentType.internal_linking_rules,
      qualityCriteria: contentType.quality_criteria, commonMistakes: contentType.common_mistakes,
      wordCountRange: contentType.word_count_range, primaryIntent: contentType.primary_intent
    },
    audience: {
      name: audienceProfile.audience_name, persona: audienceProfile.role_or_persona,
      alreadyKnows: audienceProfile.already_knows, strugglingWith: audienceProfile.struggling_with,
      skepticalOf: audienceProfile.skeptical_of, respondsTo: audienceProfile.responds_to,
      readingLevel: audienceProfile.reading_level, contentPreferences: audienceProfile.content_preferences
    },
    voice: {
      sentencePatterns: voiceProfile.sentence_patterns, vocabulary: voiceProfile.vocabulary_preferences,
      structure: voiceProfile.structure_patterns, tone: voiceProfile.tone_description,
      openingStyle: voiceProfile.opening_style, closingStyle: voiceProfile.closing_style,
      proofStyle: voiceProfile.proof_style, samplePassages: voiceProfile.sample_passages
    },
    ragChunks,
    serpData,
    tavilyData,
    publishedPages
  }
}];
```

**Output shape (`$('Merge Context').first().json`):**
```
{
  topic, targetKeywords, v2o,
  client: { name, type, industry, market, website, audienceSummary, keyFacts },
  contentType: { name, purpose, audienceMindset, structureTemplate, seoRequirements,
                 proofElements, ctaGuidance, internalLinkingRules, qualityCriteria,
                 commonMistakes, wordCountRange, primaryIntent },
  audience: { name, persona, alreadyKnows, strugglingWith, skepticalOf, respondsTo,
              readingLevel, contentPreferences },
  voice: { sentencePatterns, vocabulary, structure, tone, openingStyle, closingStyle,
           proofStyle, samplePassages },
  ragChunks: [{ text, context, sourceTitle, source, sourceDate, tags, assetTags, similarity }],
  serpData: { organicResults: [{title, url, description}], peopleAlsoAsk: [], relatedSearches: [] },
  tavilyData: [{ title, url, content }],
  publishedPages: [{ title, url, keyword, type }]
}
```

---

### NODE 13: Coverage Check
**Type:** `@n8n/n8n-nodes-langchain.anthropic`
**Model:** `claude-sonnet-4-6`
**Max tokens:** 1000

**System prompt:**
> You are a senior content strategist at a digital marketing agency. You write in Australian English. Assess how well an existing knowledge base covers a given topic before creating new content. Be concise and accurate. Return only valid JSON with no extra commentary.

**User prompt:**
```
TOPIC: {{ $json.topic }}
TARGET KEYWORDS: {{ $json.targetKeywords }}
CLIENT: {{ $json.client.name }} ({{ $json.client.industry }}, {{ $json.client.market }})
CONTENT TYPE: {{ $json.contentType.name }}
NOTES: {{ $json.notes || 'None' }}

EXISTING CONTENT FROM KNOWLEDGE BASE:
{{ $json.ragChunks.map(c => '- [' + c.source + ']\n' + c.text).join('\n\n') }}

PUBLISHED PAGES FOR THIS CLIENT:
{{ $json.publishedPages.map(p => '- ' + p.page_title + ' (' + p.primary_keyword + ') — ' + p.page_url).join('\n') }}

Based on the above, assess coverage and respond as JSON only — no commentary, no markdown:
{
  "coverage_score": <0-10>,
  "covered_subtopics": ["..."],
  "content_gaps": ["..."],
  "duplicate_risk": { "exists": <true/false>, "url": "<url or null>" },
  "proceed_recommendation": "<proceed | review | duplicate>"
}
```

**Output:** `$('Coverage Check').first().json.content[0].text` — JSON string with coverage assessment.

**Note:** `$json.notes` is not populated by Merge Context (no `notes` field exists there) — this will always render as 'None'. Likely a leftover from an earlier version.

---

### NODE 14: Research Brief
**Type:** `@n8n/n8n-nodes-langchain.anthropic`
**Model:** `claude-sonnet-4-6`
**Max tokens:** 2000

**System prompt:**
> You are a research analyst at a digital marketing agency. You write in Australian English. Your job is to synthesise web research, competitor data, and internal knowledge into a structured research brief that a content writer can use to produce an authoritative article.

**User prompt:**
```
[IF v2o exists]:
⚠ CONTENT BRIEF — MANDATORY EDITORIAL REQUIREMENTS (these take priority over all research and standard guidelines):
{v2o content}

---

TOPIC: {{ $('Merge Context').first().json.topic }}
TARGET KEYWORDS: {{ $('Merge Context').first().json.targetKeywords }}
CLIENT: {{ $('Merge Context').first().json.client.name }} ({{ $('Merge Context').first().json.client.industry }}, {{ $('Merge Context').first().json.client.market }})
CONTENT TYPE: {{ $('Merge Context').first().json.contentType.name }}

COVERAGE ASSESSMENT:
{{ $('Coverage Check').first().json.content[0].text }}

SERP COMPETITOR DATA:
{{ ($('Merge Context').first().json.serpData.organicResults || []).map(r => '- ' + r.title + ': ' + r.url + '\n  ' + r.description).join('\n') }}

RELATED SEARCH QUERIES (use as FAQ angles and subtopic signals):
{{ ($('Merge Context').first().json.serpData.relatedSearches || []).join('\n') }}

WEB RESEARCH (Tavily):
{{ $('Merge Context').first().json.tavilyData.map(r => '- ' + r.title + '\n  ' + r.content).join('\n\n') }}

EXISTING KNOWLEDGE BASE:
{{ $('Merge Context').first().json.ragChunks.map(c => c.text).join('\n\n') }}

Produce a research brief with these sections:
1. Key facts and statistics to include (with sources)
2. Main subtopics to cover and why
3. Competitor angles (what top-ranking pages focus on)
4. Gaps to address (from the coverage assessment)
5. Recommended data sources to cite
6. Investor questions to address (drawn from the related search queries above)
7. Market-specific considerations relevant to {{ $('Merge Context').first().json.client.market }} in the {{ $('Merge Context').first().json.client.industry }} industry
```

**Note:** The prompt body is duplicated verbatim in the n8n node (appears twice). This is a bug — likely caused by copy-paste when editing. Only the first instance executes.

**Output:** `$('Research Brief').first().json.content[0].text` — freeform research brief text.

---

### NODE 15: Outline
**Type:** `@n8n/n8n-nodes-langchain.anthropic`
**Model:** `claude-opus-4-6`
**Max tokens:** 2000

**System prompt:**
> You are a senior content strategist at a digital marketing agency. You write in Australian English. Your job is to produce detailed content outlines that are strategically sound, audience-focused, and optimised for organic search.

**User prompt:**
```
[IF v2o exists]:
⚠ CONTENT BRIEF — MANDATORY REQUIREMENTS (plan sections and structure to fulfil all of these before anything else):
{v2o content}

---

TOPIC: {{ $('Merge Context').first().json.topic }}
TARGET KEYWORDS: {{ $('Merge Context').first().json.targetKeywords }}
CLIENT: {{ $('Merge Context').first().json.client.name }}
CONTENT TYPE: {{ $('Merge Context').first().json.contentType.name }}
WORD COUNT PLANNING: The final article must be {{ $('Merge Context').first().json.contentType.wordCountRange }} words. Plan your outline accordingly. Assign approximate word counts to each section. Do not plan more sections or tables than can be completed within this budget. Fewer well-developed sections are better than many sections that cannot be completed.

CONTENT PURPOSE: {{ $('Merge Context').first().json.contentType.purpose }}

AUDIENCE:
{{ $('Merge Context').first().json.audience.persona }} — already knows: {{ $('Merge Context').first().json.audience.alreadyKnows }}. Struggling with: {{ $('Merge Context').first().json.audience.strugglingWith }}

CONTENT STRUCTURE TEMPLATE:
{{ $('Merge Context').first().json.contentType.structureTemplate }}

RESEARCH BRIEF:
{{ $('Research Brief').first().json.content[0].text }}

SEARCH INTENT SIGNALS — use these as FAQ questions and section heading angles:
{{ ($('Merge Context').first().json.serpData.relatedSearches || []).join('\n') }}

PUBLISHED PAGES (for internal linking opportunities):
{{ $('Merge Context').first().json.publishedPages.map(p => '- ' + p.page_title + ' — ' + p.page_url).join('\n') }}

Produce a detailed section-by-section outline following the structure template. For each section include:
- Section heading
- Key points to cover (3-5 bullet points)
- Specific data or statistics to include
- Internal linking opportunity (if relevant)

For the FAQ section, draw questions directly from the SEARCH INTENT SIGNALS above, supplementing with any additional investor questions identified in the research brief.
```

**Output:** `$('Outline').first().json.content[0].text` — structured outline.

---

### NODE 16: Draft
**Type:** `@n8n/n8n-nodes-langchain.anthropic`
**Model:** `claude-opus-4-6`
**Max tokens:** 8000

**System prompt:**
> You are an expert content writer at a digital marketing agency. You write in Australian English. You produce authoritative, well-researched long-form content optimised for organic search. Style rules (apply universally): - No em-dashes. Use commas, colons, or rewrite the sentence instead. - No filler phrases: never use "it's important to note", "furthermore", "it's worth mentioning", "in conclusion", or similar padding. - Every sentence must add new information. No repeating a point already made. - Sentences: 15-30 words. Active voice. Strong verbs. Minimal adverbs. - Write from a position of E-E-A-T: experience, expertise, authority, and trust. - You never fabricate statistics or links. You only cite sources provided to you.

**User prompt:**
```
[IF v2o exists]:
CONTENT BRIEF — NON-NEGOTIABLE REQUIREMENTS. These override your own judgement about structure, emphasis, and tone. Fulfil every point below before applying any standard guidelines:
{v2o content}

---

TOPIC: {{ $('Merge Context').first().json.topic }}
TARGET KEYWORDS: {{ $('Merge Context').first().json.targetKeywords }}
CLIENT: {{ $('Merge Context').first().json.client.name }}
WORD COUNT: Write between {{ $('Merge Context').first().json.contentType.wordCountRange }} words. Do not exceed the upper limit. If approaching the limit, wrap up remaining sections concisely rather than cutting off mid-sentence.

AUDIENCE:
Persona: {{ $('Merge Context').first().json.audience.persona }}
What they already know: {{ $('Merge Context').first().json.audience.alreadyKnows }}
What they're struggling with: {{ $('Merge Context').first().json.audience.strugglingWith }}
What they're skeptical of: {{ $('Merge Context').first().json.audience.skepticalOf }}
What they respond to: {{ $('Merge Context').first().json.audience.respondsTo }}

QUALITY CRITERIA: {{ $('Merge Context').first().json.contentType.qualityCriteria }}
COMMON MISTAKES TO AVOID: {{ $('Merge Context').first().json.contentType.commonMistakes }}

VOICE PROFILE:
Tone: {{ $('Merge Context').first().json.voice.tone }}
Sentence patterns: {{ $('Merge Context').first().json.voice.sentencePatterns }}
Vocabulary: {{ $('Merge Context').first().json.voice.vocabulary }}
Structure patterns: {{ $('Merge Context').first().json.voice.structure }}
Opening style: {{ $('Merge Context').first().json.voice.openingStyle }}
Closing style: {{ $('Merge Context').first().json.voice.closingStyle }}
Proof and citation style: {{ $('Merge Context').first().json.voice.proofStyle }}
[IF samplePassages]: SAMPLE PASSAGES — mirror this writing style closely:
{samplePassages}

[IF client.keyFacts]: CLIENT FACTS — incorporate these where naturally relevant, do not force them into every section:
{keyFacts}

OUTLINE TO FOLLOW:
{{ $('Outline').first().json.content[0].text }}

RESEARCH BRIEF (facts, stats and context to draw from):
{{ $('Research Brief').first().json.content[0].text }}

INTERNAL LINKING RULES: {{ $('Merge Context').first().json.contentType.internalLinkingRules }}
INTERNAL LINKS — select 2-3 that are most relevant to this topic. Only use URLs from this list:
{{ $('Merge Context').first().json.publishedPages.map(p => '- ' + p.title + ' — ' + p.url).join('\n') }}

APPROVED EXTERNAL SOURCES (only use these URLs for citations — do not link to any other URLs):
{{ $('Merge Context').first().json.tavilyData.map(r => '- ' + r.title + ' — ' + r.url).join('\n') }}

CTA GUIDANCE: {{ $('Merge Context').first().json.contentType.ctaGuidance }}

Write the full article following the outline. Format in markdown. Use [anchor text](url) for all links — internal and external. Never fabricate a URL.
```

**Output:** `$('Draft').first().json.content[0].text` — full markdown article draft.

---

### NODE 17: Critique
**Type:** `@n8n/n8n-nodes-langchain.anthropic`
**Model:** `claude-opus-4-6`
**Max tokens:** 3000

**System prompt:**
> You are a senior editor at a digital marketing agency. You write in Australian English. You provide honest, specific, and actionable critique of content drafts. You do not rewrite — you identify problems and gaps so a writer can fix them.

**User prompt:**
```
[IF v2o exists]:
CONTENT BRIEF COMPLIANCE CHECK — Before your standard critique, verify the draft has fulfilled every requirement below. List each requirement and mark it ✅ (met), ⚠️ (partially met), or ❌ (missing). Any ❌ or ⚠️ must be called out in your critique with specific instructions for the Rewrite stage.

CONTENT BRIEF:
{v2o content}

---

TOPIC: {{ $('Merge Context').first().json.topic }}
TARGET KEYWORDS: {{ $('Merge Context').first().json.targetKeywords }}
CLIENT: {{ $('Merge Context').first().json.client.name }}
CONTENT TYPE: {{ $('Merge Context').first().json.contentType.name }}
QUALITY CRITERIA: {{ $('Merge Context').first().json.contentType.qualityCriteria }}
COMMON MISTAKES: {{ $('Merge Context').first().json.contentType.commonMistakes }}
AUDIENCE: {{ $('Merge Context').first().json.audience.persona }}
AUDIENCE STRUGGLES WITH: {{ $('Merge Context').first().json.audience.strugglingWith }}
AUDIENCE IS SKEPTICAL OF: {{ $('Merge Context').first().json.audience.skepticalOf }}

DRAFT TO CRITIQUE:
{{ $('Draft').first().json.content[0].text }}

Critique the draft against the quality criteria. Be specific — reference actual sections or sentences. Cover:
1. Accuracy and credibility (claims without evidence, missing citations)
2. Gaps — important subtopics or questions the audience would have that are not addressed
3. Voice and tone issues (too promotional, too generic, wrong register)
4. SEO weaknesses (keyword usage, heading structure, missing FAQ opportunities)
5. Structural issues (sections that are too thin, redundant, or out of order)
6. Any links that appear fabricated or point to competitors

For each issue: state the problem, where it occurs, and what is needed to fix it.
```

**Output:** `$('Critique').first().json.content[0].text` — editorial critique.

---

### NODE 18: Gap Research
**Type:** `@n8n/n8n-nodes-langchain.anthropic`
**Model:** `claude-sonnet-4-6`
**Max tokens:** 3000

**System prompt:**
> You are a research analyst at a digital marketing agency. You write in Australian English. Your job is to identify specific facts, statistics, and evidence needed to address gaps identified in a content critique, using only the research sources provided.

**User prompt:**
```
TOPIC: {{ $('Merge Context').first().json.topic }}
TARGET KEYWORDS: {{ $('Merge Context').first().json.targetKeywords }}

CONTENT CRITIQUE (gaps and issues that need addressing):
{{ $('Critique').first().json.content[0].text }}

AVAILABLE RESEARCH SOURCES:
{{ $('Merge Context').first().json.tavilyData.map(r => '- ' + r.title + '\n  URL: ' + r.url + '\n  ' + r.content).join('\n\n') }}

EXISTING KNOWLEDGE BASE:
{{ $('Merge Context').first().json.ragChunks.map(c => c.text).join('\n\n') }}

From the sources above, extract the specific facts, data points, and evidence needed to address each gap identified in the critique. For each gap:
1. State the gap
2. Provide the evidence found to address it (quote directly where useful)
3. Include the source URL

Only use information from the provided sources. If a gap cannot be addressed from the available sources, say so explicitly.
```

**Output:** `$('Gap Research').first().json.content[0].text` — gap-filling evidence.

---

### NODE 19: Rewrite
**Type:** `@n8n/n8n-nodes-langchain.anthropic`
**Model:** `claude-opus-4-6`
**Max tokens:** 8000

**System prompt:**
> You are an expert content writer at a digital marketing agency. You write in Australian English. You produce the final publication-ready version of an article by incorporating critique feedback and additional research into an existing draft. Style rules (apply universally): - No em-dashes. Use commas, colons, or rewrite the sentence instead. - No filler phrases: never use "it's important to note", "furthermore", "it's worth mentioning", "in conclusion", or similar padding. - Every sentence must add new information. No repeating a point already made. - Sentences: 15-30 words. Active voice. Strong verbs. Minimal adverbs. - Write from a position of E-E-A-T: experience, expertise, authority, and trust. - You preserve what works in the original draft and improve what doesn't. - You never fabricate URLs. You only use links from the approved sources provided.

**User prompt:**
```
[IF v2o exists]:
CONTENT BRIEF — NON-NEGOTIABLE REQUIREMENTS. The Critique has flagged any gaps. Address every flagged item. These requirements must all be present in the final article — no exceptions:
{v2o content}

V2O QUOTE FORMATTING — when the Content Brief includes quotes:
- Place each quote immediately AFTER the specific factual point it supports — not woven into the prose
- Format exactly as two lines:
  > "Quote text verbatim"
  > — Speaker Name, Title
- Do NOT use editorial framing ("X explains", "X notes", "X says", "according to X") — the quote stands alone as credibility evidence after the point
- One quote per factual point maximum

---

TOPIC: {{ $('Merge Context').first().json.topic }}
TARGET KEYWORDS: {{ $('Merge Context').first().json.targetKeywords }}
CLIENT: {{ $('Merge Context').first().json.client.name }}
WORD COUNT: The final article must be between {{ $('Merge Context').first().json.contentType.wordCountRange }} words. The outline was planned to fit this range — follow its section structure and do not add sections beyond what was planned. If approaching the upper limit, tighten the prose in remaining sections rather than cutting them.

AUDIENCE:
Persona: {{ $('Merge Context').first().json.audience.persona }}
What they already know: {{ $('Merge Context').first().json.audience.alreadyKnows }}
What they're struggling with: {{ $('Merge Context').first().json.audience.strugglingWith }}
What they're skeptical of: {{ $('Merge Context').first().json.audience.skepticalOf }}
What they respond to: {{ $('Merge Context').first().json.audience.respondsTo }}

QUALITY CRITERIA: {{ $('Merge Context').first().json.contentType.qualityCriteria }}
COMMON MISTAKES TO AVOID: {{ $('Merge Context').first().json.contentType.commonMistakes }}

CITATIONS:
- Tavily sources: hyperlink on first mention only. All subsequent references use the source name only (e.g. "RBA Bulletin (2024)") without a hyperlink. Do not repeat the same link more than once.
- Authoritative resources: you may also link directly to government websites, official regulatory bodies, legislation, and support services where they add genuine value for the reader — even if not in the Tavily list.
- Never link to competitor pages or search result URLs.

VOICE PROFILE:
Tone: {{ $('Merge Context').first().json.voice.tone }}
Sentence patterns: {{ $('Merge Context').first().json.voice.sentencePatterns }}
Vocabulary: {{ $('Merge Context').first().json.voice.vocabulary }}
Structure patterns: {{ $('Merge Context').first().json.voice.structure }}
Opening style: {{ $('Merge Context').first().json.voice.openingStyle }}
Closing style: {{ $('Merge Context').first().json.voice.closingStyle }}
Proof and citation style: {{ $('Merge Context').first().json.voice.proofStyle }}
[IF samplePassages]: SAMPLE PASSAGES — mirror this writing style closely:
{samplePassages}

[IF client.keyFacts]: CLIENT FACTS — incorporate these where naturally relevant, do not force them into every section:
{keyFacts}

ORIGINAL DRAFT:
{{ $('Draft').first().json.content[0].text }}

CRITIQUE TO ADDRESS:
{{ $('Critique').first().json.content[0].text }}

GAP RESEARCH (additional evidence to incorporate):
{{ $('Gap Research').first().json.content[0].text }}

INTERNAL LINKING RULES: {{ $('Merge Context').first().json.contentType.internalLinkingRules }}
INTERNAL LINKS — select 2-3 most relevant to this topic. Only use URLs from this list:
{{ $('Merge Context').first().json.publishedPages.map(p => '- ' + p.title + ' — ' + p.url).join('\n') }}

APPROVED EXTERNAL SOURCES (use these for research citations):
{{ $('Merge Context').first().json.tavilyData.map(r => '- ' + r.title + ' — ' + r.url).join('\n') }}

CTA GUIDANCE: {{ $('Merge Context').first().json.contentType.ctaGuidance }}

IMAGE PLACEHOLDERS:
Add exactly 5 image placeholders in the article:
- One at the very start of the article body, on its own line before the first paragraph (featured image position)
- One at the opening of each of the first 4 major H2 sections, on its own line before that section's first paragraph
Format each placeholder exactly as:
[IMAGE: 3-6 word description of a relevant stock photo scene]
Example: [IMAGE: lawyer reviewing documents at desk]
Describe a real-world photo scene — people, settings, objects. No charts, graphs, or text overlays.

Rewrite the full article addressing every point in the critique and incorporating the gap research. Format in markdown. Use [anchor text](url) for all links. Never fabricate a URL. Never link to competitor pages.
```

**Output:** `$('Rewrite').first().json.content[0].text` — final markdown article with 5 `[IMAGE: ...]` placeholders.

---

### NODE 20: Fact Check
**Type:** `@n8n/n8n-nodes-langchain.anthropic`
**Model:** `claude-sonnet-4-6`
**Max tokens:** 2000

**System prompt:**
> You are a fact-checking editor at a digital marketing agency. You write in Australian English. Your job is to verify that all claims, statistics, and links in an article are supported by the provided source material. You do not rewrite — you flag issues clearly and concisely.

**User prompt:**
```
TOPIC: {{ $('Merge Context').first().json.topic }}
CLIENT: {{ $('Merge Context').first().json.client.name }}

FINAL ARTICLE:
{{ $('Rewrite').first().json.content[0].text }}

APPROVED SOURCES:
{{ $('Merge Context').first().json.tavilyData.map(r => '- ' + r.title + '\n  URL: ' + r.url + '\n  ' + r.content).join('\n\n') }}

APPROVED INTERNAL PAGES:
{{ $('Merge Context').first().json.publishedPages.map(p => '- ' + p.page_title + ' — ' + p.page_url).join('\n') }}

Check the article for:
1. Any statistic or claim not supported by the approved sources
2. Any URL that does not appear in the approved sources or internal pages list
3. Any factual statement that contradicts the source material
4. Any Australian English errors (spelling, terminology)

Respond as JSON:
{
  "passed": <true/false>,
  "issues": [
    { "type": "<unsupported_claim | bad_link | contradiction | language>", "location": "<quote from article>", "detail": "<what the problem is>" }
  ],
  "summary": "<one sentence overall assessment>"
}
```

**Output:** `$('Fact Check').first().json.content[0].text` — JSON string with pass/fail and issues list.

**Note:** The fact check result is NOT used to gate or loop the pipeline. It proceeds to Deliverables regardless of `passed: true/false`. The result is saved to `content_jobs` implicitly (via the Deliverables path) but the `passed` value is not stored.

---

### NODE 21: Deliverables
**Type:** `@n8n/n8n-nodes-langchain.anthropic`
**Model:** `claude-sonnet-4-6`
**Max tokens:** 500

**System prompt:**
> You are an SEO specialist at a digital marketing agency. You write in Australian English. You produce concise, optimised SEO metadata based on finished article content. You output raw JSON only — no markdown, no code fences, no backticks, no explanation. Your entire response must be valid JSON that can be passed directly to JSON.parse(). Never wrap output in ```json or ``` blocks.

**User prompt:**
```
TOPIC: {{ $('Merge Context').first().json.topic }}
TARGET KEYWORDS: {{ $('Merge Context').first().json.targetKeywords }}
CLIENT WEBSITE: {{ $('Merge Context').first().json.client.website }}

FINISHED ARTICLE:
{{ $('Rewrite').first().json.content[0].text }}

Produce the following as JSON only, no commentary:
{
  "seo_title": "<max 60 chars, includes primary keyword>",
  "meta_description": "<max 155 chars, includes primary keyword, compelling>",
  "slug": "<url-friendly, hyphenated, no stop words>",
  "h1": "<matches intent, includes primary keyword>",
  "image_alt_suggestion": "<descriptive alt text for hero image>",
  "image_queries": [
    "<featured hero image: 3-6 words describing a professional photo scene relevant to the overall article topic>",
    "<section 2 image: 3-6 words describing a photo scene relevant to that section>",
    "<section 3 image: 3-6 words describing a photo scene relevant to that section>",
    "<section 4 image: 3-6 words describing a photo scene relevant to that section>",
    "<section 5 image: 3-6 words describing a photo scene relevant to that section>"
  ]
}

image_queries rules:
- Exactly 5 queries, matching the order images appear in the article
- Each query describes a real-world photo scene (people, settings, objects) — no charts, graphs, text overlays, or illustrations
- Professional stock photo style — specific enough to find a relevant image on Shutterstock
- Examples of good queries: "lawyer reviewing documents at desk", "woman stressed looking at phone at night", "offshore team video call meeting"
```

**Output:** `$('Deliverables').first().json.content[0].text` — raw JSON string (no fences).
**Output shape:**
```json
{
  "seo_title": "...",
  "meta_description": "...",
  "slug": "...",
  "h1": "...",
  "image_alt_suggestion": "...",
  "image_queries": ["...", "...", "...", "...", "..."]
}
```

---

### NODE 22: Save to content_jobs
**Type:** `n8n-nodes-base.supabase`
**Operation:** insert (default)
**Table:** `content_jobs`

**Fields written:**

| Field | Value |
|---|---|
| `client_id` | `$('Get Client').first().json.id` |
| `content_type` | `$('On form submission').first().json['Content Type Slug']` |
| `target_keywords` | `$('Merge Context').first().json.targetKeywords` |
| `topic` | `$('Merge Context').first().json.topic` |
| `mode` | `"new"` (hardcoded) |
| `status` | `"draft"` (hardcoded) |
| `outline` | `$('Outline').first().json.content[0].text` |
| `research_brief` | `$('Research Brief').first().json.content[0].text` |
| `critique` | `$('Critique').first().json.content[0].text` |
| `final_output` | `$('Rewrite').first().json.content[0].text` |
| `model_used` | `"claude-opus-4-6"` (hardcoded) |
| `gap_research` | `$('Gap Research').first().json.content[0].text` |

**Note:** `fact_check` output is NOT saved. `deliverables` JSON is NOT saved. `coverage_check` output is NOT saved.

---

### NODE 23: Format for Google Docs
**Type:** `n8n-nodes-base.code` (JavaScript)
**Purpose:** Converts markdown article to HTML, builds Google Drive multipart upload body.

**Full JS Code:**
```javascript
// ── inputs ────────────────────────────────────────────────────────────────
const mergeCtx    = $('Merge Context').first().json;
const rewriteText = $('Rewrite').first().json.content[0].text;

let rawDel = $('Deliverables').first().json.content[0].text;
rawDel = rawDel.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```\s*$/i, '').trim();
const start = rawDel.indexOf('{');
const end = rawDel.lastIndexOf('}');
if (start !== -1 && end !== -1) { rawDel = rawDel.slice(start, end + 1); }
const deliverables = JSON.parse(rawDel);

const imageUrls   = $('Collect Images').first().json.imageUrls || [];
const client      = mergeCtx.client || {};
const topic       = mergeCtx.topic  || '';
const pageTitle   = deliverables.page_title        || '';
const metaDesc    = deliverables.meta_description  || '';
const targetUrl   = deliverables.target_url        || '';

// ── helpers ───────────────────────────────────────────────────────────────
function esc(str) {
  return String(str || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function inline(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    .replace(/`(.+?)`/g,       '<code>$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
}

function flushTable(rows) {
  if (!rows.length) return '';
  let t = '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;margin:12pt 0;">\n';
  rows.forEach((row, i) => {
    const cells = row.split('|').filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
    const tag = i === 0 ? 'th' : 'td';
    t += '<tr>' + cells.map(c => `<${tag} style="padding:6pt 10pt;">${inline(c.trim())}</${tag}>`).join('') + '</tr>\n';
  });
  return t + '</table>\n\n';
}

function mdToHtml(text) {
  let imgIdx = 0, inUl = false, inOl = false, inTable = false;
  let tableRows = [], html = '';

  const closeAll = () => {
    if (inUl)    { html += '</ul>\n'; inUl = false; }
    if (inOl)    { html += '</ol>\n'; inOl = false; }
    if (inTable) { html += flushTable(tableRows); tableRows = []; inTable = false; }
  };

  for (const raw of text.split('\n')) {
    const line = raw.trim();

    // IMAGE placeholder — replaces [IMAGE: ...] with Shutterstock URL link
    const imgM = line.match(/^\[IMAGE:\s*(.+?)\]$/i);
    if (imgM) {
      closeAll();
      const imgData = imageUrls[imgIdx++] || {};
      const url = imgData.url || '';
      html += url
        ? `<p><strong>🖼 IMAGE:</strong><br/><a href="${url}">${url}</a></p>\n\n`
        : `<p><strong>🖼 IMAGE:</strong> ${esc(imgM[1])}</p>\n\n`;
      continue;
    }

    // Blockquote — plain indented, no box
    if (line.startsWith('> ')) {
      closeAll();
      const inner = line.slice(2).trim();
      const qm = inner.match(/^[""](.+?)[""][\s\u2014\-]+(.+)$/) ||
                 inner.match(/^(.+?)\s+\u2014\s+(.+)$/);
      const quoteText   = qm ? qm[1].trim() : inner.replace(/^[""]|[""]$/g, '').trim();
      const attribution = qm ? qm[2].trim() : '';
      html += `<blockquote style="margin:12pt 0 12pt 36pt;padding:0;border:none;background:none;">` +
              `<p style="font-style:italic;color:#333;margin:0;">\u201c${esc(quoteText)}\u201d</p>` +
              (attribution ? `<p style="font-style:normal;color:#555;font-size:11pt;margin:4pt 0 0;">\u2014 ${esc(attribution)}</p>` : '') +
              `</blockquote>\n\n`;
      continue;
    }

    // Table rows, headings, UL, OL, paragraphs...
    // [full table/heading/list handling — see raw code above]
  }
  return html;
}

// ── metadata header ───────────────────────────────────────────────────────
// Builds a 4-row HTML table: CLIENT, URL, PAGE TITLE, META DESCRIPTION

// ── Google Drive multipart upload ─────────────────────────────────────────
const boundary = 'boundary_' + Date.now();
const today    = new Date().toISOString().slice(0, 10);
const docTitle = (pageTitle || (topic + ' — ' + (client.name || 'Article'))) + ' — ' + today;

// Upload target folder ID: 1tWup1S3S7GGFing1CS9-iKPUBzd6qKOf

return [{
  json: {
    body:        multipartBody,   // multipart/related body for Drive API
    contentType: `multipart/related; boundary="${boundary}"`,
    pageTitle:   docTitle,
    metaDesc
  }
}];
```

**Note:** `deliverables.page_title` and `deliverables.target_url` are referenced but NOT fields the Deliverables node outputs (it outputs `seo_title`, `h1`, `slug` — not `page_title` or `target_url`). These will be empty strings. This is a bug — the doc title falls back to `topic + ' — ' + client.name + ' — ' + today`.

---

### NODE 24: Parse Image Queries
**Type:** `n8n-nodes-base.code` (JavaScript)
**Purpose:** Parses Deliverables JSON and emits one item per image query (for parallel Shutterstock search).

**Full JS Code:**
```javascript
let rawDel = $('Deliverables').first().json.content[0].text;
rawDel = rawDel.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```\s*$/i, '').trim();

const start = rawDel.indexOf('{');
const end = rawDel.lastIndexOf('}');
if (start !== -1 && end !== -1) {
  rawDel = rawDel.slice(start, end + 1);
}

const deliverables = JSON.parse(rawDel);
const queries = deliverables.image_queries || [];

return queries.slice(0, 5).map(query => ({ json: { query } }));
```

**Output:** 5 items, each `{ json: { query: "..." } }` — feeds Shutterstock Search.

---

### NODE 25: Shutterstock Search
**Type:** `n8n-nodes-base.httpRequest`
**Method:** GET
**URL:** `https://api.shutterstock.com/v2/images/search`
**Auth:** Basic Auth (Shutterstock client_id `REDACTED_SHUTTERSTOCK_CLIENT_ID` + secret)

**Query parameters:**
- `query`: `$json.query` (from Parse Image Queries)
- `per_page`: 5
- `orientation`: horizontal
- `image_type`: photo
- `safe`: true

**Runs 5 times** (once per image query, because Parse Image Queries emits 5 items).

---

### NODE 26: Collect Images
**Type:** `n8n-nodes-base.code` (JavaScript)
**Purpose:** Takes first result from each Shutterstock search, builds Shutterstock URLs.

**Full JS Code:**
```javascript
const items = $input.all();

const imageUrls = items.map(item => {
  const img = item.json.data?.[0];
  if (img) {
    const id = img.id;
    const descSlug = (img.description || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 60);
    return {
      url: `https://www.shutterstock.com/image-photo/${descSlug}-${id}`,
      id: id
    };
  }
  return { url: '', id: '' };
});

return [{ json: { imageUrls } }];
```

**Output:** `{ json: { imageUrls: [{url, id}, ...] } }` — 5 Shutterstock URLs.

---

### NODE 27: token cost
**Type:** `n8n-nodes-base.code` (JavaScript)
**Purpose:** Diagnostic node — estimates token usage of context object. Does not affect pipeline output.

**Full JS Code:**
```javascript
const ctx = $('Merge Context').first().json;

const sizes = {
  ragChunks:      JSON.stringify(ctx.ragChunks).length,
  tavilyData:     JSON.stringify(ctx.tavilyData).length,
  serpData:       JSON.stringify(ctx.serpData).length,
  v2o:            (ctx.v2o || '').length,
  publishedPages: JSON.stringify(ctx.publishedPages).length,
  voice:          JSON.stringify(ctx.voice).length,
  audience:       JSON.stringify(ctx.audience).length,
  contentType:    JSON.stringify(ctx.contentType).length,
  client:         JSON.stringify(ctx.client).length,
};

// Rough token estimate (1 token ≈ 4 chars)
const tokens = {};
for (const [k, v] of Object.entries(sizes)) {
  tokens[k] = Math.round(v / 4);
}

return [{ json: { charSizes: sizes, estimatedTokens: tokens } }];
```

---

### NODE 28: Send a message
**Type:** `n8n-nodes-base.slack`
**Auth:** OAuth2
**Channel ID:** `C098Q328EFR` (channel name: `aeo-automation`)

**Message text:**
```
New article ready 📄
{{ $('Format for Google Docs').first().json.pageTitle }}
https://docs.google.com/document/d/{{ $('Create Google Doc').first().json.id }}/edit
```

---

### NODE 29: Create Google Doc
**Type:** `n8n-nodes-base.httpRequest`
**Method:** POST
**URL:** `https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart`
**Auth:** Google Drive OAuth2 (predefined credential: `googleDriveOAuth2Api`)
**Content-Type:** `multipart/related; boundary="..."` (dynamic, from Format for Google Docs)
**Body:** Raw multipart body from `$json.body`
**Upload target folder:** `1tWup1S3S7GGFing1CS9-iKPUBzd6qKOf` (hardcoded in multipart metadata)

**Output:** Google Drive file object with `.id` — used in Slack message to construct the doc URL.

---

## DATA FLOW SUMMARY

```
FORM INPUT
  Client, Content Type Slug, Target Keywords, Topic, Content Brief (V2O)

PARALLEL CONTEXT LOADING (all reference form inputs + client.id)
  Supabase: clients → client object
  Supabase: content_types → contentType object
  Supabase: audience_profiles → audience object
  Supabase: voice_profiles → voice object
  Supabase: published_content_map → publishedPages array
  OpenAI embeddings → RAG Search (Supabase RPC) → ragChunks array
  DataForSEO SERP → serpData { organicResults, peopleAlsoAsk, relatedSearches }
  Tavily search → tavilyData array (raw_content sliced to 6000 chars each)

MERGE CONTEXT (unified JSON object)
  All above assembled into single $json object for downstream nodes

AI PIPELINE (sequential, each reads $('Merge Context').first().json + prior node outputs)
  Coverage Check   → coverage JSON {score, gaps, duplicate_risk, recommendation}
    [token cost side branch — diagnostic only]
  Research Brief   → freeform research document
  Outline          → section-by-section outline with word count targets
  Draft            → full markdown article (~8000 token budget)
  Critique         → editorial critique with v2o compliance check
  Gap Research     → evidence to address critique gaps from Tavily + RAG sources
  Rewrite          → final markdown article + 5 [IMAGE: ...] placeholders (~8000 tokens)
  Fact Check       → JSON {passed, issues, summary} — NOT gating
  Deliverables     → JSON {seo_title, meta_description, slug, h1, image_alt_suggestion, image_queries[5]}

PARALLEL OUTPUT (from Deliverables)
  Branch A: Save to content_jobs (Supabase insert — stores pipeline artifacts)
  Branch B: Image pipeline
    Parse Image Queries → 5 items
    Shutterstock Search (×5) → image results
    Collect Images → 5 Shutterstock URLs
    Format for Google Docs → HTML + multipart body
    Create Google Doc (Google Drive API) → doc ID
    Send a message (Slack: #aeo-automation) → link to new doc
```

---

## MODEL USAGE SUMMARY

| Node | Model | Max Tokens | Purpose |
|---|---|---|---|
| Coverage Check | claude-sonnet-4-6 | 1,000 | JSON output — lightweight |
| Research Brief | claude-sonnet-4-6 | 2,000 | Research synthesis |
| Outline | claude-opus-4-6 | 2,000 | Strategic planning |
| Draft | claude-opus-4-6 | 8,000 | Full article write |
| Critique | claude-opus-4-6 | 3,000 | Editorial review |
| Gap Research | claude-sonnet-4-6 | 3,000 | Evidence extraction |
| Rewrite | claude-opus-4-6 | 8,000 | Final article write |
| Fact Check | claude-sonnet-4-6 | 2,000 | JSON output — verification |
| Deliverables | claude-sonnet-4-6 | 500 | JSON output — SEO metadata |

---

## BUGS AND ISSUES NOTED

1. **Research Brief prompt duplicated** — the entire user prompt body appears twice in the node. Only the first executes. Should be cleaned up.

2. **`$json.notes` in Coverage Check** — references `$json.notes` which is not a field in the Merge Context output. Always renders as 'None'. Leftover from an earlier version.

3. **`deliverables.page_title` / `deliverables.target_url` in Format for Google Docs** — these fields don't exist in the Deliverables output schema (`seo_title` and `slug` do, but not `page_title` or `target_url`). Both will be empty strings. Doc title falls back to `topic + ' — ' + client.name + ' — ' + date`.

4. **Fact Check result not gating** — the pipeline proceeds to Deliverables regardless of `passed: true/false`. No loop or halt logic exists.

5. **Fact Check result not saved** — the `content_jobs` insert does not include `fact_check` as a field, so the verification result is discarded.

6. **Coverage Check output not saved** — the coverage assessment is passed to Research Brief but not persisted to `content_jobs`.

7. **`publishedPages` field name inconsistency** — Merge Context maps `page_title → title` and `page_url → url`, but Coverage Check prompt references `p.page_title` and `p.page_url` (the raw DB names). This means Coverage Check sees `undefined` for those fields. The Draft and Rewrite nodes correctly use `p.title` and `p.url`.

8. **RAG chunks potentially returning empty** — noted in project memory as an outstanding issue. The `match_content_chunks` RPC uses 0.5 threshold with `text-embedding-3-small`. If no chunks are above threshold, the RAG array is empty and all AI nodes receive an empty knowledge base.

9. **Slack channel named `aeo-automation`** — this appears to be the wrong channel for a content generation notification. Likely should be a content-specific channel.

---

## KEY API CREDENTIALS IN USE (from workflow)

| Service | Credential type | Note |
|---|---|---|
| OpenAI | predefined (openAiApi) | Embeddings only (text-embedding-3-small) |
| Supabase (RAG Search) | Hardcoded API key in headers | Key visible in node: `REDACTED_SUPABASE_SERVICE_ROLE_KEY` |
| DataForSEO | genericCredentialType / httpBasicAuth | Stored in n8n credential store |
| Tavily | Hardcoded API key in JSON body | Key visible: `REDACTED_TAVILY_API_KEY` |
| Shutterstock | genericCredentialType / httpBasicAuth | client_id `REDACTED_SHUTTERSTOCK_CLIENT_ID` in memory |
| Google Drive | predefinedCredentialType (googleDriveOAuth2Api) | OAuth2 stored in n8n |
| Slack | oAuth2 | Stored in n8n |
| Anthropic/Claude | Stored in n8n credential store | Not exposed in node params |
