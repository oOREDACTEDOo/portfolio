#!/usr/bin/env node
/**
 * generate-embeddings.js
 *
 * Generates a 1536-dimension embedding vector using OpenAI text-embedding-3-small.
 * Used by the RAG agent to embed query strings before calling match_content_chunks.
 *
 * Usage (called by RAG agent via Bash):
 *   op run --env OPENAI_API_KEY="op://Shared/OpenAI - Webprofits/credential" \
 *     -- node scripts/generate-embeddings.js "query text here"
 *
 * Output: JSON array of 1536 floats written to stdout.
 * Errors: written to stderr, exit code 1.
 */

const https = require('https');

const query = process.argv[2];
if (!query) {
  process.stderr.write('Error: query text required as first argument\n');
  process.exit(1);
}

const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) {
  process.stderr.write('Error: OPENAI_API_KEY environment variable not set\n');
  process.exit(1);
}

const body = JSON.stringify({
  model: 'text-embedding-3-small',
  input: query,
  encoding_format: 'float'
});

const options = {
  hostname: 'api.openai.com',
  path: '/v1/embeddings',
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body)
  }
};

const req = https.request(options, (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    try {
      const parsed = JSON.parse(data);
      if (parsed.error) {
        process.stderr.write(`OpenAI API error: ${parsed.error.message}\n`);
        process.exit(1);
      }
      const embedding = parsed.data[0].embedding;
      process.stdout.write(JSON.stringify(embedding));
    } catch (e) {
      process.stderr.write(`Failed to parse response: ${e.message}\n`);
      process.exit(1);
    }
  });
});

req.on('error', (e) => {
  process.stderr.write(`Request error: ${e.message}\n`);
  process.exit(1);
});

req.write(body);
req.end();
