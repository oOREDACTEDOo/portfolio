import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import json

print("COMPLETING FINAL PRIORITIES")
print("=" * 80)

# Load legacy data
legacy_data = pd.read_csv('priority_7_legacy_brands_complete.csv')
legacy_data['Search Volume'] = pd.to_numeric(legacy_data['Search Volume'], errors='coerce')
legacy_data = legacy_data.dropna(subset=['Search Volume'])

# PRIORITY 5B: INTENT JOURNEY
print("\nPRIORITY 5B: INTENT JOURNEY MAPPING")
print("=" * 80)

def classify_funnel_stage(keyword, intent):
    keyword_lower = str(keyword).lower()

    awareness_terms = ['what is', 'what are', 'how does', 'types of', 'meaning', 'definition']
    if any(term in keyword_lower for term in awareness_terms):
        return 'Awareness'

    consideration_terms = ['best', 'compare', 'vs', 'cost', 'price', 'size', 'dimensions']
    if any(term in keyword_lower for term in consideration_terms):
        return 'Consideration'

    decision_terms = ['hire', 'rental', 'rent', 'buy', 'near me', 'quote']
    if any(term in keyword_lower for term in decision_terms):
        return 'Decision'

    if intent == 'Informational':
        return 'Awareness'
    elif intent == 'Commercial':
        return 'Consideration'
    elif intent == 'Transactional':
        return 'Decision'

    return 'Consideration'

legacy_data['Funnel_Stage'] = legacy_data.apply(lambda row: classify_funnel_stage(row['Keyword'], row['Intent']), axis=1)

total_keywords = len(legacy_data)
total_volume = legacy_data['Search Volume'].sum()

print("\nFunnel Stage Distribution:")
for stage in ['Awareness', 'Consideration', 'Decision']:
    stage_data = legacy_data[legacy_data['Funnel_Stage'] == stage]
    count = len(stage_data)
    volume = stage_data['Search Volume'].sum()
    print(f"{stage}: {count:,} keywords ({count/total_keywords*100:.1f}%), {int(volume):,} volume")

journey_summary = {
    'awareness': {
        'keywords': int(len(legacy_data[legacy_data['Funnel_Stage'] == 'Awareness'])),
        'volume': int(legacy_data[legacy_data['Funnel_Stage'] == 'Awareness']['Search Volume'].sum())
    },
    'consideration': {
        'keywords': int(len(legacy_data[legacy_data['Funnel_Stage'] == 'Consideration'])),
        'volume': int(legacy_data[legacy_data['Funnel_Stage'] == 'Consideration']['Search Volume'].sum())
    },
    'decision': {
        'keywords': int(len(legacy_data[legacy_data['Funnel_Stage'] == 'Decision'])),
        'volume': int(legacy_data[legacy_data['Funnel_Stage'] == 'Decision']['Search Volume'].sum())
    }
}

with open('priority_5b_intent_journey.json', 'w') as f:
    json.dump(journey_summary, f, indent=2)

# PRIORITY 6: CATEGORY MARKET SIZING
print("\nPRIORITY 6: CATEGORY MARKET SIZING")
print("=" * 80)

category_sizing = []

for category in ['Mobile Storage/Containers', 'General Equipment', 'Trench Safety/Specialty']:
    cat_data = legacy_data[legacy_data['Category'] == category]

    if len(cat_data) > 0:
        total_vol = cat_data['Search Volume'].sum()
        keyword_count = len(cat_data)
        avg_difficulty = cat_data['Keyword Difficulty'].mean() if 'Keyword Difficulty' in cat_data.columns else 0

        # By intent
        transactional_vol = cat_data[cat_data['Intent'] == 'Transactional']['Search Volume'].sum()
        commercial_vol = cat_data[cat_data['Intent'] == 'Commercial']['Search Volume'].sum()
        informational_vol = cat_data[cat_data['Intent'] == 'Informational']['Search Volume'].sum()

        category_sizing.append({
            'category': category,
            'total_keywords_au': int(keyword_count),
            'total_volume_au': int(total_vol),
            'avg_difficulty': round(float(avg_difficulty), 1) if avg_difficulty else 0,
            'transactional_volume': int(transactional_vol),
            'commercial_volume': int(commercial_vol),
            'informational_volume': int(informational_vol)
        })

        print(f"\n{category}:")
        print(f"  Total Keywords: {keyword_count:,}")
        print(f"  Total Volume (AU): {int(total_vol):,}")
        print(f"  Avg Difficulty: {avg_difficulty:.1f}" if avg_difficulty else "  Avg Difficulty: N/A")
        print(f"  Transactional: {int(transactional_vol):,}")
        print(f"  Commercial: {int(commercial_vol):,}")
        print(f"  Informational: {int(informational_vol):,}")

with open('priority_6_category_market_sizing.json', 'w') as f:
    json.dump(category_sizing, f, indent=2)

pd.DataFrame(category_sizing).to_csv('priority_6_category_market_sizing.csv', index=False)

print("\n" + "=" * 80)
print("PRIORITIES 5B & 6 COMPLETE")
print("=" * 80)
print("\nFiles created:")
print("  - priority_5b_intent_journey.json")
print("  - priority_6_category_market_sizing.json")
print("  - priority_6_category_market_sizing.csv")
