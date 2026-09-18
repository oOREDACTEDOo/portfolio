import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import os

import time
import json
import pandas as pd
from dataforseo_query import DataForSEOQuery

# Initialize client
client = DataForSEOQuery(os.environ.get("DATAFORSEO_LOGIN"), os.environ.get("DATAFORSEO_PASSWORD"))

def categorize_service(keyword):
    """Categorize keyword by Client J service line"""
    keyword_lower = str(keyword).lower()

    if any(term in keyword_lower for term in ['excavator', 'digger']):
        return 'Excavators'
    elif any(term in keyword_lower for term in ['loader', 'skid steer']):
        return 'Loaders'
    elif any(term in keyword_lower for term in ['telehandler', 'forklift']):
        return 'Telehandlers'
    elif any(term in keyword_lower for term in ['container', 'storage']):
        return 'Shipping Containers'
    elif any(term in keyword_lower for term in ['tilt prop', 'acrow', 'propping']):
        return 'Tilt Props & Propping'
    elif any(term in keyword_lower for term in ['pump', 'dewater']):
        return 'Pumps'
    elif any(term in keyword_lower for term in ['shoring', 'trench box']):
        return 'Shoring Boxes'
    elif any(term in keyword_lower for term in ['refrigerated', 'reefer', 'cold storage']):
        return 'Refrigerated Containers'
    elif any(term in keyword_lower for term in ['dangerous goods', 'hazardous']):
        return 'Dangerous Goods'
    elif any(term in keyword_lower for term in ['worksite facilities', 'site facilities', 'portable buildings']):
        return 'Worksite Facilities'
    elif any(term in keyword_lower for term in ['traffic management', 'traffic control']):
        return 'Traffic Management'
    elif any(term in keyword_lower for term in ['pipe plugging', 'confined space']):
        return 'Pipe Plugging & Confined Space'
    else:
        return 'General Equipment'

# Australian cities (major markets)
AU_CITIES = [
    'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide',
    'gold coast', 'canberra', 'newcastle', 'wollongong', 'geelong',
    'hobart', 'townsville', 'cairns', 'darwin', 'toowoomba'
]

# New Zealand cities
NZ_CITIES = [
    'auckland', 'wellington', 'christchurch', 'hamilton', 'tauranga',
    'dunedin', 'palmerston north', 'napier', 'porirua', 'rotorua'
]

# Client J core services - National keywords
NATIONAL_KEYWORDS = [
    # Hire Equipment
    'excavator hire',
    'excavators for hire',
    'mini excavator hire',
    'excavator rental',

    'loader hire',
    'loaders for hire',
    'wheel loader hire',
    'loader rental',
    'skid steer loader hire',

    'telehandler hire',
    'telehandlers for hire',
    'telehandler rental',
    'forklift hire',

    # Shipping Containers
    'shipping container hire',
    'shipping containers for hire',
    'container hire',
    'storage container hire',
    'shipping container rental',
    '20ft container hire',
    '40ft container hire',

    'worksite facilities hire',
    'site facilities hire',
    'portable buildings hire',

    'refrigerated container hire',
    'refrigerated containers for hire',
    'cold storage container hire',
    'reefer container hire',

    'dangerous goods container hire',
    'dangerous goods storage',
    'hazardous goods container',

    'self storage containers',
    'portable storage containers',
    'storage containers for hire',

    # Shoring, Propping & Pumps
    'tilt prop hire',
    'tilt props for hire',
    'acrow props hire',
    'propping hire',

    'pump hire',
    'pumps for hire',
    'water pump hire',
    'submersible pump hire',
    'dewatering pump hire',
    'trash pump hire',

    'shoring box hire',
    'shoring boxes for hire',
    'trench box hire',
    'trench shoring hire',

    'shoring hire',
    'trench shoring',
    'excavation shoring',
    'hydraulic shoring',

    'pipe plugging equipment',
    'confined space equipment hire',
    'trench safety equipment',

    # Traffic Management
    'traffic management equipment hire',
    'traffic control equipment',
    'worksite traffic management',

    # General Equipment Terms
    'construction equipment hire',
    'plant equipment hire',
    'heavy equipment hire',
    'earthmoving equipment hire',
    'equipment hire',
    'plant hire',
    'machinery hire',
    'construction machinery hire'
]

print("=" * 80)
print("Client J KEYWORD RESEARCH - AU & NZ")
print("=" * 80)
print(f"\nTotal National Keywords: {len(NATIONAL_KEYWORDS)}")
print(f"AU Cities: {len(AU_CITIES)}")
print(f"NZ Cities: {len(NZ_CITIES)}")
print(f"\nEstimated Total Keywords to Research:")
print(f"  - National (AU): {len(NATIONAL_KEYWORDS)}")
print(f"  - National (NZ): {len(NATIONAL_KEYWORDS)}")
print(f"  - Local (AU): {len(NATIONAL_KEYWORDS) * len(AU_CITIES)}")
print(f"  - Local (NZ): {len(NATIONAL_KEYWORDS) * len(NZ_CITIES)}")
print(f"  - TOTAL: {len(NATIONAL_KEYWORDS) * 2 + len(NATIONAL_KEYWORDS) * len(AU_CITIES) + len(NATIONAL_KEYWORDS) * len(NZ_CITIES)}")
print("=" * 80)

# Storage for results
all_results = []

# ============================================================================
# PHASE 1: National Keywords - Australia
# ============================================================================
print("\n\n[PHASE 1] Fetching National Keywords - AUSTRALIA")
print("-" * 80)

batch_size = 10
for i in range(0, len(NATIONAL_KEYWORDS), batch_size):
    batch = NATIONAL_KEYWORDS[i:i+batch_size]
    print(f"\nProcessing AU batch {i//batch_size + 1}/{(len(NATIONAL_KEYWORDS)-1)//batch_size + 1} ({len(batch)} keywords)...")

    try:
        result = client.keyword_search_volume(batch, location_code=2036)  # Australia

        if result and len(result) > 0:
            task_result = result[0]
            if 'result' in task_result and task_result['result']:
                for item in task_result['result']:
                    keyword = item.get('keyword', '')
                    volume = item.get('search_volume', 0)

                    all_results.append({
                        'keyword': keyword,
                        'type': 'national',
                        'country': 'AU',
                        'city': '',
                        'search_volume': volume,
                        'service_category': categorize_service(keyword)
                    })

                    if volume > 0:
                        print(f"  ✓ {keyword}: {volume:,}")
                    else:
                        print(f"  - {keyword}: No data")

        time.sleep(0.5)  # Rate limiting

    except Exception as e:
        print(f"  ✗ Error with batch: {str(e)}")
        time.sleep(1)

print(f"\n✓ Phase 1 Complete: {len([r for r in all_results if r['country']=='AU' and r['type']=='national'])} AU national keywords collected")

# ============================================================================
# PHASE 2: National Keywords - New Zealand
# ============================================================================
print("\n\n[PHASE 2] Fetching National Keywords - NEW ZEALAND")
print("-" * 80)

for i in range(0, len(NATIONAL_KEYWORDS), batch_size):
    batch = NATIONAL_KEYWORDS[i:i+batch_size]
    print(f"\nProcessing NZ batch {i//batch_size + 1}/{(len(NATIONAL_KEYWORDS)-1)//batch_size + 1} ({len(batch)} keywords)...")

    try:
        result = client.keyword_search_volume(batch, location_code=2554)  # New Zealand

        if result and len(result) > 0:
            task_result = result[0]
            if 'result' in task_result and task_result['result']:
                for item in task_result['result']:
                    keyword = item.get('keyword', '')
                    volume = item.get('search_volume', 0)

                    all_results.append({
                        'keyword': keyword,
                        'type': 'national',
                        'country': 'NZ',
                        'city': '',
                        'search_volume': volume,
                        'service_category': categorize_service(keyword)
                    })

                    if volume > 0:
                        print(f"  ✓ {keyword}: {volume:,}")
                    else:
                        print(f"  - {keyword}: No data")

        time.sleep(0.5)

    except Exception as e:
        print(f"  ✗ Error with batch: {str(e)}")
        time.sleep(1)

print(f"\n✓ Phase 2 Complete: {len([r for r in all_results if r['country']=='NZ' and r['type']=='national'])} NZ national keywords collected")

# ============================================================================
# PHASE 3: Local Keywords - Australia
# ============================================================================
print("\n\n[PHASE 3] Fetching Local Keywords - AUSTRALIA")
print("-" * 80)

local_keywords_au = []
for keyword in NATIONAL_KEYWORDS:
    for city in AU_CITIES:
        local_keywords_au.append({
            'keyword': f"{keyword} {city}",
            'base_keyword': keyword,
            'city': city
        })

print(f"Total AU local keywords to fetch: {len(local_keywords_au)}")

# Process in batches
batch_size = 10
for i in range(0, len(local_keywords_au), batch_size):
    batch = local_keywords_au[i:i+batch_size]
    batch_keywords = [item['keyword'] for item in batch]

    print(f"\nProcessing AU local batch {i//batch_size + 1}/{(len(local_keywords_au)-1)//batch_size + 1}...")

    try:
        result = client.keyword_search_volume(batch_keywords, location_code=2036)

        if result and len(result) > 0:
            task_result = result[0]
            if 'result' in task_result and task_result['result']:
                for idx, item in enumerate(task_result['result']):
                    keyword = item.get('keyword', '')
                    volume = item.get('search_volume', 0)

                    original_item = batch[idx] if idx < len(batch) else {'base_keyword': '', 'city': ''}

                    all_results.append({
                        'keyword': keyword,
                        'type': 'local',
                        'country': 'AU',
                        'city': original_item['city'],
                        'search_volume': volume,
                        'service_category': categorize_service(original_item.get('base_keyword', keyword))
                    })

                    if volume > 0:
                        print(f"  ✓ {keyword}: {volume:,}")

        time.sleep(0.5)

    except Exception as e:
        print(f"  ✗ Error with batch: {str(e)}")
        time.sleep(1)

print(f"\n✓ Phase 3 Complete: {len([r for r in all_results if r['country']=='AU' and r['type']=='local'])} AU local keywords collected")

# ============================================================================
# PHASE 4: Local Keywords - New Zealand
# ============================================================================
print("\n\n[PHASE 4] Fetching Local Keywords - NEW ZEALAND")
print("-" * 80)

local_keywords_nz = []
for keyword in NATIONAL_KEYWORDS:
    for city in NZ_CITIES:
        local_keywords_nz.append({
            'keyword': f"{keyword} {city}",
            'base_keyword': keyword,
            'city': city
        })

print(f"Total NZ local keywords to fetch: {len(local_keywords_nz)}")

for i in range(0, len(local_keywords_nz), batch_size):
    batch = local_keywords_nz[i:i+batch_size]
    batch_keywords = [item['keyword'] for item in batch]

    print(f"\nProcessing NZ local batch {i//batch_size + 1}/{(len(local_keywords_nz)-1)//batch_size + 1}...")

    try:
        result = client.keyword_search_volume(batch_keywords, location_code=2554)

        if result and len(result) > 0:
            task_result = result[0]
            if 'result' in task_result and task_result['result']:
                for idx, item in enumerate(task_result['result']):
                    keyword = item.get('keyword', '')
                    volume = item.get('search_volume', 0)

                    original_item = batch[idx] if idx < len(batch) else {'base_keyword': '', 'city': ''}

                    all_results.append({
                        'keyword': keyword,
                        'type': 'local',
                        'country': 'NZ',
                        'city': original_item['city'],
                        'search_volume': volume,
                        'service_category': categorize_service(original_item.get('base_keyword', keyword))
                    })

                    if volume > 0:
                        print(f"  ✓ {keyword}: {volume:,}")

        time.sleep(0.5)

    except Exception as e:
        print(f"  ✗ Error with batch: {str(e)}")
        time.sleep(1)

print(f"\n✓ Phase 4 Complete: {len([r for r in all_results if r['country']=='NZ' and r['type']=='local'])} NZ local keywords collected")

# ============================================================================
# SAVE RESULTS
# ============================================================================
print("\n\n" + "=" * 80)
print("SAVING RESULTS")
print("=" * 80)

# Convert to DataFrame
df = pd.DataFrame(all_results)

# Save complete dataset
output_file = 'research_outputs/client_j_keywords_complete.csv'
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n✓ Complete dataset saved: {output_file}")
print(f"  Total keywords: {len(df):,}")

# Save summary by category
summary_file = 'research_outputs/client_j_keywords_summary.json'
summary = {
    'total_keywords': len(df),
    'by_country': {
        'AU': {
            'national': len(df[(df['country']=='AU') & (df['type']=='national')]),
            'local': len(df[(df['country']=='AU') & (df['type']=='local')]),
            'total_volume': int(df[df['country']=='AU']['search_volume'].sum())
        },
        'NZ': {
            'national': len(df[(df['country']=='NZ') & (df['type']=='national')]),
            'local': len(df[(df['country']=='NZ') & (df['type']=='local')]),
            'total_volume': int(df[df['country']=='NZ']['search_volume'].sum())
        }
    },
    'by_service_category': df.groupby('service_category')['search_volume'].sum().to_dict(),
    'top_keywords_au': df[df['country']=='AU'].nlargest(20, 'search_volume')[['keyword', 'search_volume', 'type']].to_dict('records'),
    'top_keywords_nz': df[df['country']=='NZ'].nlargest(20, 'search_volume')[['keyword', 'search_volume', 'type']].to_dict('records')
}

with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"✓ Summary saved: {summary_file}")

print("\n" + "=" * 80)
print("RESEARCH COMPLETE")
print("=" * 80)
print(f"\nTotal Keywords Researched: {len(df):,}")
print(f"Total Search Volume (AU): {df[df['country']=='AU']['search_volume'].sum():,.0f}/month")
print(f"Total Search Volume (NZ): {df[df['country']=='NZ']['search_volume'].sum():,.0f}/month")
print(f"\nKeywords with volume > 0: {len(df[df['search_volume']>0]):,} ({len(df[df['search_volume']>0])/len(df)*100:.1f}%)")
