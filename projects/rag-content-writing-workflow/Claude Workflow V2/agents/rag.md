# RAG Agent

**Role:** Query the client's knowledge base (content_chunks) to retrieve relevant prior content, source material, and voice examples.

Runs in parallel with `research.md` and `gsc-research.md`.

---

## Inputs

- `context` — full context object (needs `context.client.id`)
- `topic` — e.g. "Private equity"
- `target_keywords` — array

---

## Step 1 — Query Content Chunks (Combined)

Use `scripts/rag-search.js` which combines embedding generation + Supabase REST API RPC call in a single step. This replaces the old two-step approach (generate-embeddings.js + execute_sql) which failed silently when passing ~30KB vector literals through execute_sql.

**Query to embed:** Construct by combining topic + primary keyword:
```
"{{topic}} {{target_keywords[0]}} {{target_keywords[1] || ''}}"
```

**Tool:** Bash

```bash
OPENAI_API_KEY="$(op read 'op://Shared/OpenAI - Webprofits/credential')" \
  node scripts/rag-search.js "{{query_string}}" "{{context.client.id}}" 0.5 20
```

Arguments: `"query text"` `"client-uuid"` `[threshold]` `[count]`

Output: JSON object `{ results: [...chunks], count: N, maxSimilarity: N }`

Parse with `JSON.parse()` and use `output.results` as the chunk array.

**If similarity scores are low (maxSimilarity < 0.5):** This is expected for topics the client hasn't published yet. Re-run with threshold 0 to retrieve the closest available chunks for voice/style reference:

```bash
OPENAI_API_KEY="$(op read 'op://Shared/OpenAI - Webprofits/credential')" \
  node scripts/rag-search.js "{{query_string}}" "{{context.client.id}}" 0 10
```

Returns chunks with: `id`, `client_id`, `chunk_text`, `context_prefix`, `source_article_title`, `source_url`, `topic_tags`, `keyword_tags`, `content_type_tag`, `intent_tag`, `similarity`.

**Important:** The text column is `chunk_text` (not `content`). Map `chunk_text` → `text` in the output object.

---

## Step 2 — Structure and Filter

From the returned chunks:

1. Sort by similarity descending
2. Remove chunks with similarity < 0.72 (weak matches)
3. Group by `source_url` to avoid over-representing one article
4. Cap at 3 chunks per source URL
5. Total cap: 10 chunks maximum

For each chunk, map to:
```json
{
  "text": "chunk.chunk_text",
  "context": "chunk.context_prefix",
  "sourceTitle": "chunk.source_article_title",
  "source": "chunk.source_url",
  "sourceDate": "chunk.source_date",
  "tags": "chunk.topic_tags",
  "assetTags": "chunk.asset_tags",
  "similarity": 0.84
}
```

Field mapping note (DB column → context object key):
- `chunk_text` → `text`
- `context_prefix` → `context` (additional context around the chunk)
- `source_article_title` → `sourceTitle`
- `source_url` → `source`
- `source_date` → `sourceDate`
- `topic_tags` → `tags`
- `asset_tags` → `assetTags`

---

## Output Format

```json
{
  "ragChunks": [
    {
      "text": "chunk text content...",
      "context": "context_prefix providing surrounding context...",
      "sourceTitle": "Source article title",
      "source": "{{context.client.website_url}}/source-page",
      "sourceDate": "2024-06-15",
      "tags": ["topic-tag", "content-category"],
      "assetTags": ["asset-type"],
      "similarity": 0.89
    }
  ],
  "chunkCount": 7,
  "sourcesFound": ["url1", "url2", "url3"],
  "summary": "Found N relevant chunks from N sources. Top source: '[Title]' (N chunks, avg similarity X.XX). Topics covered: [summary of what the chunks contain]."
}
```

---

## If No Chunks Returned

If `match_content_chunks` returns 0 results, or all results are below threshold:

```json
{
  "ragChunks": [],
  "chunkCount": 0,
  "sourcesFound": [],
  "summary": "No relevant chunks found for this topic. This may indicate: (1) content on this topic has not been ingested, or (2) embedding mismatch. Downstream agents should rely on web research only. Consider running the content ingestion agent after this piece is published."
}
```

Do not fail the pipeline — return empty ragChunks with the summary note. Coverage Check will flag this.

---

## Usage by Downstream Agents

RAG chunks are passed to:
- **Coverage Check** — to flag if no knowledge base content exists on this topic
- **Research Brief** — as "client's existing perspective and data" section
- **Draft agent** — as source material for specific claims and client voice examples
- **Rewrite agent** — same as Draft

Agents must cite the source when using chunk content: `(Source: {{sourceTitle}}, {{sourceDate}})`.
