# RAG content writing workflow

A designed-and-built system for automated, on-brand content production across multiple clients, replacing the idea of training a custom model per client with retrieval-augmented generation and a multi-stage editing pipeline. Built at Webprofits, an AI-native marketing agency.

## The problem

Producing on-brand content at volume for multiple clients usually means either a slow manual process or generic AI output that needs a full rewrite anyway. Training a separate fine-tuned model per client was the original idea, but Claude doesn't support fine-tuning, and a model-per-client approach is expensive to maintain and slow to update whenever a client's voice or facts change. This system gets the same result (content that actually sounds like the client) without training anything: client voice, structure rules, and real source material live in a database, and get pulled into the generation pipeline at the right stage.

## Architecture

Three components:

- **Supabase** (Postgres + pgvector) stores per-client voice profiles, content-type templates, audience profiles, a growing knowledge base of the client's own past content (chunked and embedded), Search Console performance data, and job tracking. Nine tables in total.
- **n8n** orchestrates four workflows: ingest a client's existing content into the knowledge base, generate new content, update existing content, and a feedback loop that re-ingests published content so the knowledge base compounds over time.
- **Claude** runs the actual writing, in stages rather than one shot.

## The pipeline

Eight stages per new article (nine or ten for an update, which adds an E-E-A-T assessment and a Search Console data pull up front):

1. **Coverage check** – how much relevant material already exists for this client and topic, and what approach that calls for
2. **Research** – synthesise web search, competitor content, and the client's own material into a research brief
3. **Angle + outline** – find a differentiated angle and structure it against the content type's template
4. **Draft** – write the full piece against the voice profile and outline
5. **Critique** – a separate editorial pass that flags unsupported claims, filler, and AI-typical phrasing by name ("In today's...", "It's important to note", vague qualifiers like "significant improvement"). This is the step that actually stops the output reading like AI content, not the writing step
6. **Gap research** – go find the specific evidence the critique says is missing
7. **Rewrite** – fold that evidence back in and fix what the critique flagged
8. **Fact-check + polish** – verify claims, add internal links from the client's own published-content map, final copyedit

Different stages deliberately use different models depending on how much judgement each one needs: Opus for outline/draft/critique, Sonnet for research, gap-filling, and polish. That's a real cost/quality decision, not just "call the API everywhere."

## What's actually built and tested, not just planned

Workflow 1 (content ingestion) and Workflow 2 (new content generation) are complete: built node by node in n8n, tested end to end on a real 16-page client batch, with the specific bugs hit and fixed documented as they happened (raw HTML exceeding Claude's context window, an embeddings API body-mode gotcha, a Supabase trigger referencing the wrong column name, and so on). A second client was onboarded through the same pipeline. See `RAG-Content-System-Plan.md` for the full plan and a running build log across six sessions.

Workflow 3 (content update, the more complex one, since it needs the Search Console API and the E-E-A-T assessment) and Workflow 4 (feedback loop) were also built node by node in n8n. Both were left untested end to end: a full update or feedback-loop run burns through Claude API calls fast, and it wasn't worth the token spend without a real client update queued up.

## Cost

Calculated per pipeline stage rather than estimated in the abstract: roughly $0.55–$2.10 per new article and $0.70–$2.50 per update in Claude API costs, depending on length. Producing hundreds of articles a month comes in under $250 in API fees.

## What's in this folder

- `RAG-Content-System-Plan.md`: the full plan, covering architecture, database design, all four n8n workflows node by node, the pipeline stages in full prompt detail, cost estimates, and a session-by-session build log
- `supabase-schema.sql`: the database schema
- `Claude Workflow/` and `Claude Workflow V2/`: actual pipeline outputs (research briefs, drafts, critiques, rewrites) from real generation runs
- `client-i-vto-guide.md` / `client-i-vto-briefs.md`: a real client's voice/tone/objective briefs used to build a voice profile
- `dataforseo_query.py`: a supporting script for keyword/SERP research feeding the pipeline

Client names throughout this folder have been replaced with generic labels (Client A, Client D, and so on). The system and the results are real; the client identities have been withheld.
