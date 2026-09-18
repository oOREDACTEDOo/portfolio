# Context Loader Agent

**Role:** Load all client and content-type context from Supabase. Returns a structured context object used by all downstream agents.

---

## Inputs

```json
{
  "client_name": "{{run_inputs.client_name}}",
  "content_type_slug": "{{run_inputs.content_type_slug}}",
  "target_keywords": ["{{run_inputs.target_keywords}}"],
  "topic": "{{run_inputs.topic}}",
  "v2o_brief": "{{run_inputs.v2o_brief}}"
}
```

Use `client_name` to look up the client. Match against `clients.brand_name` (case-insensitive).

---

## Supabase Queries

### 1. Client record
```sql
SELECT id, brand_name, market, industry, website_url, key_facts,
       business_type, target_audience_summary, gsc_property_id,
       ga4_property_id, currency, writing_language, language_code,
       dataforseo_location_code, google_drive_folder_id, slack_channel_id,
       logo_url
FROM clients
WHERE LOWER(brand_name) = LOWER('{{client_name}}')
LIMIT 1;
```

Required columns (add to clients table if not present):
- `writing_language` TEXT — e.g. "Australian English", "British English". Defaults to "English" if null.
- `language_code` TEXT — e.g. "en". Used in DataForSEO calls. Default "en".
- `dataforseo_location_code` INTEGER — DataForSEO location code for SERP searches. Required for correct market data.
- `google_drive_folder_id` TEXT — Google Drive folder ID for output docs. Optional; falls back to folder search by brand_name.
- `slack_channel_id` TEXT — Slack channel ID for delivery notifications. Optional; falls back to #content-automation.

### 2. Voice profile
```sql
SELECT sentence_patterns, vocabulary_preferences, structure_patterns,
       tone_description, opening_style, closing_style, proof_style,
       sample_passages
FROM voice_profiles
WHERE client_id = '{{client.id}}'
ORDER BY last_updated DESC
LIMIT 1;
```

### 3. Audience profile
```sql
SELECT *
FROM audience_profiles
WHERE client_id = '{{client.id}}'
LIMIT 1;
```

### 4. Content type
```sql
SELECT type_name, type_slug, business_context, purpose, audience_mindset,
       structure_template, seo_requirements, proof_elements, cta_guidance,
       internal_linking_rules, quality_criteria, common_mistakes,
       word_count_range, primary_intent
FROM content_types
WHERE type_slug = '{{content_type_slug}}'
LIMIT 1;
```

### 5. Published pages (for internal linking + cannibalism check)
```sql
SELECT page_title, page_url
FROM published_content_map
WHERE client_id = '{{client.id}}'
ORDER BY page_title;
```

---

## Output Format

Return a single JSON object. All downstream agents receive this as their `context` input.

```json
{
  "client": {
    "id": "uuid",
    "brand_name": "loaded from clients table",
    "market": "loaded from clients table",
    "industry": "loaded from clients table",
    "website_url": "loaded from clients table",
    "key_facts": "loaded from clients table",
    "business_type": "loaded from clients table",
    "target_audience_summary": "loaded from clients table",
    "gsc_property_id": "loaded from clients table",
    "ga4_property_id": "loaded from clients table",
    "currency": "loaded from clients table",
    "writing_language": "loaded from clients table",
    "dataforseo_location_code": "loaded from clients table",
    "language_code": "loaded from clients table",
    "google_drive_folder_id": "loaded from clients table",
    "slack_channel_id": "loaded from clients table",
    "logo_url": "loaded from clients table — null if not set"
  },
  "voice_profile": {
    "tone_description": "...",
    "sentence_patterns": "...",
    "vocabulary_preferences": "...",
    "opening_style": "...",
    "closing_style": "...",
    "proof_style": "...",
    "sample_passages": "..."
  },
  "audience_profile": { ... },
  "content_type": {
    "type_name": "Asset Class Page",
    "type_slug": "asset_class_page",
    "business_context": "...",
    "purpose": "...",
    "audience_mindset": "...",
    "structure_template": "...",
    "seo_requirements": "...",
    "proof_elements": "...",
    "cta_guidance": "...",
    "internal_linking_rules": "...",
    "quality_criteria": "...",
    "common_mistakes": "...",
    "word_count_range": "2000-2500",
    "primary_intent": "informational"
  },
  "published_pages": [
    { "title": "ETFs", "url": "https://clientd.example.com/etfs" }
  ],
  "run_inputs": {
    "topic": "Private equity",
    "target_keywords": ["private equity australia"],
    "v2o_brief": ""
  }
}
```

---

## Error Handling

- If client not found: return error `CLIENT_NOT_FOUND: No client matches '{{client_name}}'. Check brand_name in clients table.`
- If content type not found: return error `CONTENT_TYPE_NOT_FOUND: No content type matches slug '{{content_type_slug}}'.`
- If voice profile missing: include `voice_profile: null` — downstream agents will use generic tone fallback.
- If audience profile missing: include `audience_profile: null` — not a blocker.
- If published_pages is empty: include empty array — not a blocker, but note for coverage check.
