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

print("="*80)
print("Client J KEYWORD RESEARCH - AU & NZ")
print("="*80)
print(f"National Keywords: {len(NATIONAL_KEYWORDS)}")
print(f"AU Cities: {len(AU_CITIES)}")
print(f"NZ Cities: {len(NZ_CITIES)}")
print(f"Total Keywords to Research: {len(NATIONAL_KEYWORDS) * 2 + len(NATIONAL_KEYWORDS) * len(AU_CITIES) + len(NATIONAL_KEYWORDS) * len(NZ_CITIES)}")
print("="*80)

# Storage for results
all_results = []
api_calls_made = 0

# Function to fetch and store keyword data
def fetch_keywords(keywords_list, location_code, country, keyword_type, city=''):
    global api_calls_made
    batch_size = 10

    for i in range(0, len(keywords_list), batch_size):
        batch = keywords_list[i:i+batch_size]

        try:
            result = client.keyword_search_volume(batch, location_code=location_code)
            api_calls_made += 1

            if result and 'tasks' in result and len(result['tasks']) > 0:
                task = result['tasks'][0]

                if task.get('status_code') == 20000 and task.get('result'):
                    for item in task['result']:
                        keyword = item.get('keyword', '')
                        volume = item.get('search_volume', 0)

                        all_results.append({
                            'keyword': keyword,
                            'type': keyword_type,
                            'country': country,
                            'city': city,
                            'search_volume': volume,
                            'service_category': categorize_service(keyword)
                        })

                    # Print progress
                    successful = len([r for r in all_results if r['country']==country and r['type']==keyword_type and (not city or r['city']==city)])
                    print(f"  [{country}] {keyword_type.title()}: {successful:,} keywords collected (API calls: {api_calls_made})")

            time.sleep(0.3)  # Rate limiting

        except Exception as e:
            print(f"  Error: {str(e)}")
            time.sleep(1)

# Phase 1: National Keywords - Australia
print("\n[Phase 1] National Keywords - AUSTRALIA")
fetch_keywords(NATIONAL_KEYWORDS, 2036, 'AU', 'national')

# Phase 2: National Keywords - New Zealand
print("\n[Phase 2] National Keywords - NEW ZEALAND")
fetch_keywords(NATIONAL_KEYWORDS, 2554, 'NZ', 'national')

# Phase 3: Local Keywords - Australia
print("\n[Phase 3] Local Keywords - AUSTRALIA")
for city in AU_CITIES:
    local_keywords = [f"{kw} {city}" for kw in NATIONAL_KEYWORDS]
    fetch_keywords(local_keywords, 2036, 'AU', 'local', city)

# Phase 4: Local Keywords - New Zealand
print("\n[Phase 4] Local Keywords - NEW ZEALAND")
for city in NZ_CITIES:
    local_keywords = [f"{kw} {city}" for kw in NATIONAL_KEYWORDS]
    fetch_keywords(local_keywords, 2554, 'NZ', 'local', city)

# Save Results
print("\n" + "="*80)
print("SAVING RESULTS")
print("="*80)

df = pd.DataFrame(all_results)

# Save complete dataset
output_file = 'research_outputs/client_j_keywords_complete.csv'
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\nComplete dataset: {output_file}")
print(f"  Total keywords: {len(df):,}")

# Create summary
summary = {
    'total_keywords': len(df),
    'total_api_calls': api_calls_made,
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
    'top_keywords_nz': df[df['country']=='NZ'].nlargest(20, 'search_volume')[['keyword', 'search_volume', 'type']].to_dict('records'),
    'top_keywords_by_city_au': {}
}

# Top keywords per AU city
for city in AU_CITIES:
    city_data = df[(df['country']=='AU') & (df['city']==city)].nlargest(10, 'search_volume')
    if len(city_data) > 0:
        summary['top_keywords_by_city_au'][city] = city_data[['keyword', 'search_volume']].to_dict('records')

summary_file = 'research_outputs/client_j_keywords_summary.json'
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"Summary: {summary_file}")

print("\n" + "="*80)
print("RESEARCH COMPLETE")
print("="*80)
print(f"Total Keywords: {len(df):,}")
print(f"Total API Calls: {api_calls_made}")
print(f"AU Search Volume: {df[df['country']=='AU']['search_volume'].sum():,.0f}/month")
print(f"NZ Search Volume: {df[df['country']=='NZ']['search_volume'].sum():,.0f}/month")
print(f"Keywords with volume > 0: {len(df[df['search_volume']>0]):,} ({len(df[df['search_volume']>0])/len(df)*100:.1f}%)")
