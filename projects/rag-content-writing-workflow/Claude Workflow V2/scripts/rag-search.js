#!/usr/bin/env node
/**
 * rag-search.js
 *
 * Generates an embedding for the query string and calls match_content_chunks
 * via the Supabase REST API. Returns matching chunks as JSON.
 *
 * Replaces the two-step approach (generate-embeddings.js + execute_sql) which
 * was unreliable because passing a ~30KB vector literal through execute_sql
 * hit tool parameter limits and failed silently.
 *
 * Usage (called by RAG agent via Bash):
 *   OPENAI_API_KEY="$(op read 'op://Shared/OpenAI - Webprofits/credential')" \
 *     node scripts/rag-search.js "query text" "client-uuid" [threshold] [count]
 *
 * Arguments:
 *   query      - text to embed and search for (required)
 *   client_id  - Supabase client UUID to filter chunks (required)
 *   threshold  - cosine similarity threshold, default 0.5 (optional)
 *   count      - max results to return, default 20 (optional)
 *
 * Output: JSON object written to stdout:
 *   { results: [...chunks with similarity], count: N, maxSimilarity: N }
 *
 * Errors: written to stderr, exit code 1.
 */

const https = require('https');

const SUPABASE_URL = 'https://REDACTED_PROJECT.supabase.co';
const SUPABASE_ANON_KEY = 'REDACTED_SUPABASE_ANON_KEY';

const query = process.argv[2];
const clientId = process.argv[3];
const threshold = parseFloat(process.argv[4] || '0.5');
const count = parseInt(process.argv[5] || '20', 10);

if (!query || !clientId) {
  process.stderr.write('Usage: node rag-search.js "query text" "client-uuid" [threshold] [count]\n');
  process.exit(1);
}

const openaiKey = process.env.OPENAI_API_KEY;
if (!openaiKey) {
  process.stderr.write('Error: OPENAI_API_KEY environment variable not set\n');
  process.exit(1);
}

function httpsPost(hostname, path, headers, body) {
  return new Promise((resolve, reject) => {
    const bodyStr = JSON.stringify(body);
    const options = {
      hostname,
      path,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(bodyStr),
        ...headers
      }
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch (e) {
          reject(new Error(`Failed to parse response: ${data.substring(0, 200)}`));
        }
      });
    });
    req.on('error', reject);
    req.write(bodyStr);
    req.end();
  });
}

async function main() {
  // Step 1: Generate embedding
  const embedRes = await httpsPost(
    'api.openai.com',
    '/v1/embeddings',
    { 'Authorization': `Bearer ${openaiKey}` },
    { model: 'text-embedding-3-small', input: query, encoding_format: 'float' }
  );

  if (embedRes.status !== 200 || embedRes.body.error) {
    process.stderr.write(`OpenAI error: ${JSON.stringify(embedRes.body.error)}\n`);
    process.exit(1);
  }

  const embedding = embedRes.body.data[0].embedding;

  // Step 2: Call Supabase RPC via REST API
  const rpcRes = await httpsPost(
    'REDACTED_PROJECT.supabase.co',
    '/rest/v1/rpc/match_content_chunks',
    {
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
    },
    {
      query_embedding: embedding,
      match_client_id: clientId,
      match_threshold: threshold,
      match_count: count
    }
  );

  if (rpcRes.status !== 200) {
    process.stderr.write(`Supabase RPC error (${rpcRes.status}): ${JSON.stringify(rpcRes.body)}\n`);
    process.exit(1);
  }

  const results = rpcRes.body;
  const maxSim = results.length > 0 ? Math.max(...results.map(r => r.similarity)) : 0;

  process.stdout.write(JSON.stringify({
    results,
    count: results.length,
    maxSimilarity: maxSim
  }));
}

main().catch(e => {
  process.stderr.write(`Error: ${e.message}\n`);
  process.exit(1);
});
