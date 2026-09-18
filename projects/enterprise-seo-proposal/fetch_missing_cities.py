import os
import time
import json
import pandas as pd
from dataforseo_query import DataForSEOQuery

client = DataForSEOQuery(os.environ.get("DATAFORSEO_LOGIN"), os.environ.get("DATAFORSEO_PASSWORD"))

def categorize_service(keyword):
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

# Missing AU cities
MISSING_AU_CITIES = ['melbourne', 'brisbane', 'gold coast', 'wollongong', 'geelong', 'cairns', 'darwin']

NATIONAL_KEYWORDS = [
    'excavator hire', 'excavators for hire', 'mini excavator hire', 'excavator rental',
    'loader hire', 'loaders for hire', 'wheel loader hire', 'loader rental', 'skid steer loader hire',
    'telehandler hire', 'telehandlers for hire', 'telehandler rental', 'forklift hire',
    'shipping container hire', 'shipping containers for hire', 'container hire', 'storage container hire',
    'shipping container rental', '20ft container hire', '40ft container hire',
    'worksite facilities hire', 'site facilities hire', 'portable buildings hire',
    'refrigerated container hire', 'refrigerated containers for hire', 'cold storage container hire', 'reefer container hire',
    'dangerous goods container hire', 'dangerous goods storage', 'hazardous goods container',
    'self storage containers', 'portable storage containers', 'storage containers for hire',
    'tilt prop hire', 'tilt props for hire', 'acrow props hire', 'propping hire',
    'pump hire', 'pumps for hire', 'water pump hire', 'submersible pump hire', 'dewatering pump hire', 'trash pump hire',
    'shoring box hire', 'shoring boxes for hire', 'trench box hire', 'trench shoring hire',
    'shoring hire', 'trench shoring', 'excavation shoring', 'hydraulic shoring',
    'pipe plugging equipment', 'confined space equipment hire', 'trench safety equipment',
    'traffic management equipment hire', 'traffic control equipment', 'worksite traffic management',
    'construction equipment hire', 'plant equipment hire', 'heavy equipment hire', 'earthmoving equipment hire',
    'equipment hire', 'plant hire', 'machinery hire', 'construction machinery hire'
]

print("="*80)
print("FETCHING MISSING CITY DATA")
print("="*80)
print(f"Missing Cities: {', '.join(MISSING_AU_CITIES)}")
print(f"Keywords per city: {len(NATIONAL_KEYWORDS)}")
print("="*80)

all_results = []
api_calls = 0

for city in MISSING_AU_CITIES:
    print(f"\n[{city.upper()}] Fetching keywords...")
    local_keywords = [f"{kw} {city}" for kw in NATIONAL_KEYWORDS]

    batch_size = 10
    city_results = []

    for i in range(0, len(local_keywords), batch_size):
        batch = local_keywords[i:i+batch_size]

        try:
            result = client.keyword_search_volume(batch, location_code=2036)
            api_calls += 1

            if result and 'tasks' in result and len(result['tasks']) > 0:
                task = result['tasks'][0]

                if task.get('status_code') == 20000 and task.get('result'):
                    for item in task['result']:
                        keyword = item.get('keyword', '')
                        volume = item.get('search_volume', 0) or 0

                        city_results.append({
                            'keyword': keyword,
                            'type': 'local',
                            'country': 'AU',
                            'city': city,
                            'search_volume': volume,
                            'service_category': categorize_service(keyword)
                        })

            time.sleep(0.3)

        except Exception as e:
            print(f"  Error: {str(e)}")
            time.sleep(1)

    # Show top results for this city
    city_df = pd.DataFrame(city_results)
    if len(city_df) > 0:
        top_vol = city_df.nlargest(5, 'search_volume')
        total_vol = city_df['search_volume'].sum()
        print(f"  Total volume: {total_vol:,.0f}/month")
        print(f"  Top keywords:")
        for _, row in top_vol.iterrows():
            if row['search_volume'] > 0:
                print(f"    - {row['keyword']}: {row['search_volume']:,.0f}")

    all_results.extend(city_results)

# Save results
print("\n" + "="*80)
print("SAVING RESULTS")
print("="*80)

df_new = pd.DataFrame(all_results)

# Load existing data and merge
existing_file = 'research_outputs/client_j_keywords_complete.csv'
df_existing = pd.read_csv(existing_file)

# Combine
df_combined = pd.concat([df_existing, df_new], ignore_index=True)

# Save combined file
df_combined.to_csv(existing_file, index=False, encoding='utf-8-sig')
print(f"\nUpdated: {existing_file}")
print(f"  Previous records: {len(df_existing):,}")
print(f"  New records added: {len(df_new):,}")
print(f"  Total records: {len(df_combined):,}")

# Also save just the new data
new_file = 'research_outputs/missing_cities_keywords.csv'
df_new.to_csv(new_file, index=False, encoding='utf-8-sig')
print(f"  New data saved to: {new_file}")

print("\n" + "="*80)
print(f"API Calls Made: {api_calls}")
print(f"New AU Volume: {df_new['search_volume'].sum():,.0f}/month")
print("="*80)
