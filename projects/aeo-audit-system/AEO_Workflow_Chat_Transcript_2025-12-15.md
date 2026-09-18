# AEO Workflow Project - Chat Transcript
## Date: 2025-12-15

---

## Project Overview

**What You're Building:** Answer Engine Optimization (AEO) reporting system that tracks how AI engines (ChatGPT, Gemini) mention clients over time.

**Your Role:** SEO Specialist at WebProfits (Australia) modifying existing n8n workflows for client AEO monitoring.

---

## What Was Accomplished

### Workflow 1: AEO Scraper (AEO Context Mapping copy)

**Completed:**
- ✅ Fixed parallel wiring for ChatGPT and Gemini scrapers (two separate loops)
- ✅ Added Wait node (3 seconds) for Gemini rate limiting
- ✅ Updated Format Results code to output clean columns:
  - Question, ChatGPT Response, ChatGPT Sources, Gemini Response, Gemini Sources
- ✅ Added country dropdown to form (Australia, US, UK, NZ, Canada)
- ✅ Updated Parse Questions code to append country context to questions
- ✅ Fixed Create Spreadsheet → Append Row wiring (two branches from Format Results)
- ✅ Removed unnecessary Merge and Filter nodes
- ✅ Spreadsheets now create successfully with correct data

**Parse Questions Code (Updated):**
```javascript
// Get the questions list from input
const questionsText = $input.first().json.questions_list;
const country = $input.first().json.country || 'Australia';

// Split by newlines and clean up
const questions = questionsText
  .split('\n')
  .map(q => q.trim())
  .filter(q => q.length > 0);

// Return array of question objects with metadata
return questions.map((question, index) => {
  // Check if question already contains the country (case-insensitive)
  const countryAlreadyIncluded = question.toLowerCase().includes(country.toLowerCase());

  // Only append country context if not already mentioned
  const modifiedQuestion = countryAlreadyIncluded
    ? question
    : `${question} (Answer specifically for ${country}. Focus only on ${country} companies, products, and services.)`;

  return {
    json: {
      question: modifiedQuestion,
      original_question: question,
      question_number: index + 1,
      country: country,
      brand_name: $input.first().json.brand_name,
      business_type: $input.first().json.business_type,
      website: $input.first().json.website,
      key_product_service: $input.first().json.key_product_service,
      tier1_competitors: $input.first().json.tier1_competitors,
      tier2_competitors: $input.first().json.tier2_competitors,
      tier3_competitors: $input.first().json.tier3_competitors,
      timestamp: $input.first().json.timestamp,
      sheet_name: $input.first().json.sheet_name
    }
  };
});
```

**Format Results Code (Updated):**
```javascript
const items = $input.all();
const results = {};

// Group by question
for (const item of items) {
  const json = item.json;

  // Handle ChatGPT results
  if (json.chatgpt_sources && json.chatgpt_sources.length > 0) {
    const data = json.chatgpt_sources[0];
    const question = data.prompt || '';

    if (!results[question]) {
      results[question] = { Question: question };
    }
    results[question]['ChatGPT Response'] = data.answer || '';
    results[question]['ChatGPT Sources'] = (data.sources || []).join('\n');
  }

  // Handle Gemini results
  if (json.gemini_sources && json.gemini_sources.length > 0) {
    const data = json.gemini_sources[0];
    const question = data.prompt || '';

    if (!results[question]) {
      results[question] = { Question: question };
    }
    results[question]['Gemini Response'] = data.answer || '';
    results[question]['Gemini Sources'] = (data.sources || []).join('\n');
  }
}

// Convert to array
return Object.values(results).map(row => ({ json: row }));
```

---

### Workflow 2: AEO Report Generator (AEO Context Mapping Report Generator copy)

**Completed:**
- ✅ Added Form Trigger with fields: brand_name, period_1_sheet_url, period_2_sheet_url, competitors
- ✅ Added two Google Sheets nodes to fetch Period 1 and Period 2 data
- ✅ Added Merge node (Choose Branch mode) to wait for both sheets
- ✅ Created Build Prompt Code node to format comparison data
- ✅ Updated Report Generator prompt for comparison analysis
- ✅ Changed model from GPT-4 to GPT-4o (128K token limit)
- ✅ Added HTTP Request nodes to create Google Doc (using Google Sheets OAuth)
- ✅ Added HTTP Request node to add content to Google Doc
- ✅ Workflow creates Google Doc with comparison report

**Node Names (must match exactly):**
- `Form Trigger`
- `Get Period 1 Data`
- `Get Period 2 Data`
- `Build Prompt Code`
- `Report Generator`
- `Create Google Doc`
- `Add Content to Doc`

**Build Prompt Code:**
```javascript
const period1 = $('Get Period 1 Data').all();
const period2 = $('Get Period 2 Data').all();
const form = $('Form Trigger').first().json;

let comparisonData = '';

for (let i = 0; i < period1.length; i++) {
  const p1 = period1[i].json;
  const p2 = period2[i]?.json || {};

  comparisonData += `
=== Question ${i + 1}: ${p1.Question} ===

PERIOD 1:
ChatGPT Response: ${p1['ChatGPT Response'] || 'N/A'}
ChatGPT Sources: ${p1['ChatGPT Sources'] || 'None'}
Gemini Response: ${p1['Gemini Response'] || 'N/A'}
Gemini Sources: ${p1['Gemini Sources'] || 'None'}

PERIOD 2:
ChatGPT Response: ${p2['ChatGPT Response'] || 'N/A'}
ChatGPT Sources: ${p2['ChatGPT Sources'] || 'None'}
Gemini Response: ${p2['Gemini Response'] || 'N/A'}
Gemini Sources: ${p2['Gemini Sources'] || 'None'}

---
`;
}

return [{
  json: {
    brand_name: form.brand_name,
    competitors: form.competitors,
    comparison_data: comparisonData
  }
}];
```

**Report Generator Prompt:**
```
CRITICAL: You MUST analyze ALL questions provided - there are approximately 33 questions. Do not stop early. Do not summarize. Provide the complete structured analysis for EVERY single question. Continue until all questions are analyzed.

OUTPUT FORMAT: Use plain text only. Do NOT use markdown formatting like ###, **, or *. Use CAPS or line breaks for emphasis instead.

If the responses for Period 1 and Period 2 are identical or nearly identical, simply state "No significant changes detected" for that question. Do not generate filler content or nonsensical analysis.

Your Role:
You are an expert AEO strategist analysing fortnightly visibility shifts for {{ $json.brand_name }}. Evaluate how LLM-generated answers (ChatGPT + Gemini) have changed over time for a fixed set of monitored commercial questions.

Your Objective:
Provide a structured, consistent, and commercially meaningful comparison of model responses across periods, focused on brand visibility, competitor visibility, and answer evolution.

Instructions:
- ONLY analyse the exact questions provided. Do not generate new questions.
- Evaluate ChatGPT and Gemini independently, then synthesise a combined insight.
- For each question, compare Period 1 vs Period 2 using these criteria:
  - Visibility Change: whether an answer is present, missing, longer, shorter, or more detailed
  - Citation Change: new citations, lost citations, or any referencing differences
  - Competitor Change: brands newly mentioned or removed
  - Content Context Change: shifts in tone, accuracy, specificity, or consumer guidance
  - Brand Impact: how these changes affect {{ $json.brand_name }}'s competitive position
- If an answer or citation is missing for a period, explicitly flag this.

Competitors to watch for:
{{ $json.competitors }}

Data to Analyse:
{{ $json.comparison_data }}

Output Format:
For each question, output:

Question: {question}

Visibility Change:
- ...

Citation Change:
- ...

Competitor Change:
- ...

Content Change:
- ...

Brand Impact:
- ...

Recommendation:
- ...

---

Final Evaluation:
Provide a summary of key changes in the LLM landscape for {{ $json.brand_name }}, with key callouts for visibility changes (e.g., no longer listed, more harshly evaluated, new keywords in sentiment).
```

**Create Google Doc (HTTP Request):**
- Method: POST
- URL: `https://docs.googleapis.com/v1/documents`
- Authentication: Predefined Credential Type
- Credential Type: Google Sheets OAuth2 API
- Body Parameters:
  - title: `{{ $('Build Prompt Code').first().json.brand_name }}_AEO_Comparison_{{ new Date().toISOString().split('T')[0] }}`

**Add Content to Doc (HTTP Request):**
- Method: POST
- URL: `https://docs.googleapis.com/v1/documents/{{ $json.documentId }}:batchUpdate`
- Authentication: Predefined Credential Type
- Credential Type: Google Sheets OAuth2 API
- Body (JSON):
```json
{
  "requests": [
    {
      "insertText": {
        "location": { "index": 1 },
        "text": {{ JSON.stringify($('Report Generator').first().json.message.content) }}
      }
    }
  ]
}
```

---

## Still To Do

| Task | Status | Notes |
|------|--------|-------|
| Gemini API | ⏸️ Paused | Needs paid tier or wait for daily quota reset |
| Google Drive credentials | ⏸️ Waiting | Ask Alex to set up (for folder organization) |
| Move docs/sheets to AEO folder | ⏸️ Waiting | Needs Google Drive credentials |
| Slack notification | 🔲 Not started | Add after Add Content to Doc node |
| Test with real comparison data | 🔲 Not started | Run scraper now, again in 2 weeks, then compare |

---

## Slack Notification (To Add)

After Add Content to Doc, add Slack node with this message:
```
🔍 *AEO Comparison Report Ready*

*Brand:* {{ $('Build Prompt Code').first().json.brand_name }}
*Date:* {{ new Date().toISOString().split('T')[0] }}

📄 *View Report:* https://docs.google.com/document/d/{{ $('Create Google Doc').first().json.documentId }}/edit
```

---

## Key Technical Details

### Gemini API Rate Limits (Free Tier)
- 15-20 requests per minute
- ~1,500 requests per day
- Resets at midnight Pacific Time
- For production (hundreds of questions): Need paid tier

### Google Sheets OAuth Workaround
- Used Google Sheets OAuth2 credentials to call Google Docs API
- Works because both APIs use same OAuth scopes
- Avoids needing separate Google Docs credentials

### n8n Node Naming
- Expressions like `$('Node Name')` must match exact node names
- Case-sensitive
- Update all expressions if you rename nodes

---

## Folder Location (For Later)

AEO folder ID: `105leZoSvZ2TWcFw2pkwNqYK_w66SZlJr`
URL: https://drive.google.com/drive/folders/105leZoSvZ2TWcFw2pkwNqYK_w66SZlJr

Once you have Google Drive credentials, add a "Move file" node to move:
- Spreadsheets from scraper workflow
- Google Docs from report generator workflow

---

## Workflow Diagrams

### Scraper Workflow:
```
Form Trigger → CONSTANTS → Parse Questions → Loop Over Items ─┬→ ChatGPT Scraper ─┬→ Merge1 → Format Results ─┬→ Create Spreadsheet
                                                              │                    │                          │
                                                              └→ Wait → Gemini ────┘                          └→ Append Row → Send Message
```

### Report Generator Workflow:
```
Form Trigger ─┬→ Get Period 1 Data ─┬→ Merge (Choose Branch) → Build Prompt Code → Report Generator → Create Google Doc → Add Content to Doc → Slack
              │                     │
              └→ Get Period 2 Data ─┘
```

---

## Contact for Credentials

- **Alex** - n8n workspace admin (for Google Drive/Docs credentials)

---

## Next Steps

1. Add Slack notification to Report Generator
2. Run scraper with real client questions
3. Wait 2 weeks
4. Run scraper again
5. Run Report Generator with both spreadsheets
6. Review actual comparison report with real data differences

---

*Transcript saved: 2025-12-15*
