-- ============================================================
-- SEED DATA: Client D (Pilot Client)
-- Run this after supabase-schema.sql
-- ============================================================

-- 1. Insert client
insert into clients (
  id, brand_name, business_type, industry, market, currency,
  website_url, target_audience_summary
) values (
  'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
  'Client D',
  'marketplace',
  'Financial services / Investment marketplace',
  'AU',
  'AUD',
  'https://clientd.example.com',
  'Australian retail and wholesale investors researching asset classes. Secondary: financial advisers, SMSF trustees, accountants researching on behalf of clients.'
);

-- 2. Insert audience profile
insert into audience_profiles (
  client_id, audience_name, role_or_persona,
  already_knows, struggling_with, skeptical_of,
  responds_to, reading_level, content_preferences
) values (
  'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
  'Australian Investors',
  'Retail and wholesale investors researching asset classes. May be self-directed investors, SMSF trustees, or working with a financial adviser.',
  'Basic investing concepts (shares, bonds, property). Familiar with the ASX. Understands risk/return tradeoff at a high level.',
  'Understanding niche/alternative asset classes. Knowing which product structures suit them (managed fund vs ETF vs LIC). Evaluating risk beyond surface-level descriptions. Understanding tax implications.',
  'Marketing from fund managers. Promises of high returns without risk context. Overly simplified explanations that gloss over downsides.',
  'Specific data and statistics. Named sources and industry reports. Balanced coverage of both benefits and risks. Comparison frameworks that help them evaluate. Practical "how to" guidance.',
  'Grade 11-12. Professional, assumes financial literacy but not expertise.',
  'Scannable content with clear headings. Comparison tables. FAQs addressing practical questions. Data-rich with named sources.'
);

-- 3. Insert content type: Asset Class Page
insert into content_types (
  type_name, type_slug, business_context, purpose, audience_mindset,
  structure_template, seo_requirements, proof_elements, cta_guidance,
  internal_linking_rules, quality_criteria, common_mistakes,
  example_references, word_count_range, primary_intent
) values (
  'Asset Class Page',
  'asset_class_page',
  'marketplace',
  'Educate investors about a specific asset class so they can make informed decisions about whether to invest, how to evaluate products, and what risks to consider. Simultaneously serve as an SEO landing page that ranks for "[asset class] Australia" and related searches, driving organic traffic to the product listings.',
  'The reader is an Australian investor (retail or wholesale) who is: researching whether this asset class belongs in their portfolio; trying to understand how it works, what the risks are, and how to get started; comparing this asset class against alternatives they already know; looking for a trustworthy, independent source (not a fund manager''s sales pitch); may be a self-directed investor, SMSF trustee, or working with a financial adviser.',

  -- structure_template
  '1. INTRODUCTION / DEFINITION
- What is [asset class]?
- Clear, concise definition in 2-3 sentences
- Brief context: why this asset class matters in the Australian market
- Key market data (AUM, growth, market size if available)

2. MARKET CONTEXT & GROWTH
- How the asset class has evolved in Australia
- Key growth drivers (regulatory, institutional, market conditions)
- Current market size and trajectory
- Cited data from industry reports (named sources)

3. TYPES / CATEGORIES
- Break down the asset class into its distinct sub-types
- Each sub-type gets: name and definition, how it differs, who it suits best, risk level relative to other sub-types
- Aim for 4-8 sub-types depending on the asset class

4. KEY FEATURES & BENEFITS
- 4-6 distinct benefits, each with a clear heading, explanation of why this matters, supporting data or evidence
- Must include: return potential, diversification benefit, accessibility, and any unique structural advantage

5. RISKS & CONSIDERATIONS
- 4-8 distinct risks, each with a clear heading, honest explanation (not downplayed), how it manifests in practice, mitigation if applicable
- Must include: market risk, liquidity risk, and any asset-class-specific risks
- This section should be roughly equal in depth to the benefits section

6. COMPARISON WITH ALTERNATIVES
- Comparison table: this asset class vs 3-4 alternatives
- Columns: Income source, Liquidity, Risk level, Typical returns, Minimum investment, Best suited for
- Brief paragraph interpreting the table

7. HOW TO EVALUATE / COMPARE PRODUCTS
- 4-6 evaluation criteria specific to this asset class
- Each criterion explained: what to look for, why it matters
- Practical guidance, not generic

8. HOW TO INVEST
- All available access methods in Australia: direct from fund manager, through a broker/trading platform, via superannuation, through SMSFs (with compliance notes), via robo-advisors (if applicable), through financial advisers
- Specific to this asset class

9. TAX CONSIDERATIONS (if substantial)
- Australian tax treatment specific to this asset class
- Income tax on distributions, capital gains tax implications, SMSF-specific treatment, franking credits (if applicable)
- Reference ATO/ASIC where appropriate

10. FAQ SECTION
- 8-14 questions targeting actual investor questions and "People Also Ask"
- Answers: concise but complete (2-4 sentences)
- Must cover: minimum investment, risk level, liquidity, tax, suitability, fees

11. CONCLUSION
- 2-3 sentence balanced summary
- Restate key value proposition and key risk
- Encourage informed decision-making (not a sales push)',

  -- seo_requirements
  'Primary keyword: "[Asset class] Australia" or "[Asset class] investments Australia"
H1: Include primary keyword naturally
H2s: Each major section should target a related keyword or question
Meta title: "[Asset Class] in Australia: Find & Compare [Asset Class] Investments" (match existing pattern)
Meta description: 150-160 chars, include primary keyword, mention compare/find
FAQ schema: Implement FAQ structured data for all FAQ questions
Internal links: Link to related asset class pages where contextually relevant
Word count: 2,500 - 4,500 words for the educational section (excluding listings)
Readability: Scannable with clear H2/H3 hierarchy. Short paragraphs (3-4 sentences max). Use tables and lists to break up dense information.',

  -- proof_elements
  'At minimum 3 named data sources (e.g., Morgan Stanley, ASIC, ABS, RBA, McKinsey, Morningstar, ASX, Bloomberg).
At minimum 2 specific statistics with attribution.
Australian regulatory references where relevant (ASIC, APRA, ATO).
Comparison table vs alternative asset classes.
No unattributed claims — every assertion about returns, risk levels, or market size must cite a source or be flagged [NEEDS VERIFICATION].',

  -- cta_guidance
  'Client D is a marketplace, not a fund manager. CTAs should:
- NOT push a specific product
- Encourage exploring the product listings on the page ("Compare [asset class] products listed on Client D")
- Encourage signing up for the newsletter
- Reference the ability to filter and compare products
- Maintain the independent, educational positioning',

  -- internal_linking_rules
  'Link to related asset class pages where they share characteristics (e.g., private credit → mortgage funds → bond funds).
Link to relevant articles/guides if they exist on the site.
Link to the main investments hub (/investments/).
Do NOT link to specific product pages — the listings section handles that.
Internal links should feel natural within the educational content, not forced.',

  -- quality_criteria
  'An excellent asset class page:
1. Educates completely — a reader with basic investing knowledge could understand this asset class well enough to decide whether to research further
2. Is balanced — benefits and risks receive equal treatment. No cheerleading.
3. Is data-rich — specific numbers, named sources, market data. Not vague generalisations.
4. Is Australian-specific — Australian market context, regulatory framework, tax treatment. Not generic global content.
5. Is structured for scanning — clear headings, short paragraphs, tables, FAQs.
6. Is differentiated — doesn''t read like every other financial education site. Includes unique comparison frameworks, addresses common misconceptions, or provides angles that competitors miss.
7. Is current — references recent market data, not outdated statistics.
8. Maintains neutrality — reads as independent research, not as a sales funnel.',

  -- common_mistakes
  '1. Generic introductions — "In today''s volatile market..." or "Investing is an important part of building wealth..."
2. US-centric content — Referencing TIPS, 401(k)s, municipal bonds, SEC. Everything must be Australian context (SMSF, ASX, ASIC, ATO, FCS).
3. Unbalanced coverage — All benefits, light on risks.
4. Missing comparison framework — A comparison table is mandatory.
5. Vague claims — "Strong returns" without numbers. "Growing market" without data.
6. Promotional tone — Content should never sound like a fund manager pitch.
7. Missing SMSF coverage — Tax and compliance implications for SMSFs should always be addressed.
8. Thin FAQ section — FAQs should target real investor questions and "People Also Ask" queries.
9. No internal links — Every asset class page should link to related asset class pages.
10. Inconsistent depth — All pages should target Tier 1 depth.',

  -- example_references
  '["https://clientd.example.com/investments/exchange-traded-funds", "https://clientd.example.com/investments/private-credit", "https://clientd.example.com/investments/mortgage-funds"]'::jsonb,

  '2500-4500',
  'informational'
);

-- 4. Insert voice profile
insert into voice_profiles (
  client_id, sentence_patterns, vocabulary_preferences,
  structure_patterns, tone_description, opening_style,
  closing_style, proof_style
) values (
  'a1b2c3d4-e5f6-7890-abcd-ef1234567890',

  'Medium-length sentences (15-20 words average). Declarative and explanatory. Uses definition-first structure ("Private credit is a form of non-bank lending whereby..."). Minimal use of questions in body copy.',

  'Uses: "investors", "asset class", "risk-adjusted returns", "portfolio diversification", "due diligence". Avoids: hard sales language, first person ("we"), informal/casual phrasing. Financial terminology used freely but explained on first use. Australian spelling and regulatory references (ASIC, APRA, ASX, FCS, ATO, SMSF).',

  'Opens with a definition of the asset class. Sections follow logical progression: What → Types → Benefits → Risks → How to Compare → How to Invest → FAQ. Uses comparison tables to contrast with alternative investments. Cites specific data sources and industry reports. FAQs address practical investor questions. Closes with a balanced summary.',

  'Informative, professional, neutral. Not promotional — the site positions itself as an independent research platform, not a seller. Educational without being patronising.',

  'Always opens with a clear definition of the asset class. Never starts with generic statements like "In today''s market..." or "Investing is important...". Gets straight to what the asset class is and why it matters.',

  'Closes with a balanced 2-3 sentence summary. Restates the key value proposition alongside the key risk. Does not end with a hard sales push. Encourages informed decision-making.',

  'Cites industry reports by name (Morgan Stanley, McKinsey, Russell Investments, PGIM). Includes specific numbers ("$200 billion in AUM by 2024", "correlation of only 0.33 with US equities"). References regulatory bodies (ASIC RG45, APRA). Always balanced — pairs benefits with risks.'
);

-- 5. Insert published content map (all 16 asset class pages)
insert into published_content_map (client_id, page_title, page_url, content_type, primary_keyword, is_cornerstone) values
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Private Equity',            'https://clientd.example.com/investments/private-equity',           'asset_class_page', 'private equity Australia',            false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Large Caps Australia',       'https://clientd.example.com/investments/large-caps-australia',      'asset_class_page', 'large cap shares Australia',          false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Australian Equity Funds',    'https://clientd.example.com/investments/australian-equity-funds',   'asset_class_page', 'Australian equity funds',             false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Small Caps Australia',       'https://clientd.example.com/investments/small-caps-australia',      'asset_class_page', 'small cap shares Australia',          false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Exchange Traded Funds',      'https://clientd.example.com/investments/exchange-traded-funds',     'asset_class_page', 'ETFs Australia',                      true),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Large Caps Global',          'https://clientd.example.com/investments/large-caps-global',         'asset_class_page', 'global large cap funds Australia',    false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Bond Funds',                 'https://clientd.example.com/investments/bond-funds',                'asset_class_page', 'bond funds Australia',                false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Income Funds',               'https://clientd.example.com/investments/income-funds',              'asset_class_page', 'income funds Australia',              false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Property',                   'https://clientd.example.com/investments/property',                  'asset_class_page', 'property investment Australia',       false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Property Funds',             'https://clientd.example.com/investments/property-funds',            'asset_class_page', 'property funds Australia',            false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Mortgage Funds',             'https://clientd.example.com/investments/mortgage-funds',            'asset_class_page', 'mortgage funds Australia',            true),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Private Credit',             'https://clientd.example.com/investments/private-credit',            'asset_class_page', 'private credit Australia',            true),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'LICs/LITs',                  'https://clientd.example.com/investments/lics-lits',                 'asset_class_page', 'LICs LITs Australia',                 false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Multi-Asset Portfolios',     'https://clientd.example.com/investments/multi-asset-portfolios',    'asset_class_page', 'multi-asset portfolios Australia',    false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Managed Accounts',           'https://clientd.example.com/investments/managed-accounts',          'asset_class_page', 'managed accounts Australia',          false),
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Cash',                       'https://clientd.example.com/investments/cash',                      'asset_class_page', 'cash investments Australia',          false);
