# RAG Agent

**Role:** Query the client's knowledge base (content_chunks) to retrieve relevant prior content, source material, and voice examples.

Runs in parallel with `research.md` and `gsc-research.md`.

---

## Inputs

- `context` — full context object (needs `context.client.id`)
- `topic` — e.g. "Private equity"
- `target_keywords` — array

---

## Step 1 — Generate Embedding

Generate an embedding for the search query using OpenAI's `text-embedding-3-small` model.

**Query to embed:** Construct by combining topic + primary keyword:
```
"{{topic}} {{target_keywords[0]}} {{target_keywords[1] || ''}}"
```

**Tool:** Bash

```bash
OPENAI_API_KEY="op://Shared/OpenAI - Webprofits/credential" op run -- node scripts/generate-embeddings.js "{{query_string}}"
```

Output: JSON array of 1536 floats. Parse with `JSON.parse()` — pass directly as `query_embedding` to the RPC call.

---

## Step 2 — Query Content Chunks

**Tool:** Supabase RPC `match_content_chunks`

```sql
SELECT * FROM match_content_chunks(
  query_embedding => '{{embedding_vector}}',
  match_client_id => '{{context.client.id}}',
  match_threshold => 0.5,
  match_count => 20
);
```

Parameter notes:
- Use `=>` for named arguments (PostgreSQL syntax). `:=` is PL/pgSQL assignment syntax and will fail.
- Parameter is `match_client_id`, not `filter_client_id`.
- Threshold 0.5 matches the n8n baseline. The Step 3 filter below trims weak matches after retrieval.

Returns chunks with: `id`, `client_id`, `chunk_text`, `context_prefix`, `source_article_title`, `source_url`, `topic_tags`, `keyword_tags`, `content_type_tag`, `intent_tag`, `similarity`.

**Important:** The text column is `chunk_text` (not `content`). Use `chunk_text` in any SELECT referencing article content.

---

## Step 3 — Structure and Filter

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
