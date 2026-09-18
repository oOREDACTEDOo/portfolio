"""
Wikipedia & Knowledge Graph Checker
Checks brand presence in Wikipedia, Google Knowledge Graph, and Wikidata
"""

import requests
import json
from typing import Dict, Optional, List
from urllib.parse import quote

class KnowledgePresenceChecker:
    
    def __init__(self, google_kg_api_key: Optional[str] = None):
        """
        Initialize checker
        
        Args:
            google_kg_api_key: Optional Google Knowledge Graph API key
                              Get from: https://console.cloud.google.com/
        """
        self.google_kg_api_key = google_kg_api_key
        self.wikipedia_api = "https://en.wikipedia.org/w/api.php"
        self.wikidata_api = "https://www.wikidata.org/w/api.php"
        self.kg_api = "https://kgsearch.googleapis.com/v1/entities:search"
    
    def check_wikipedia(self, brand_name: str, exact_match: bool = False) -> Dict:
        """
        Check if brand has Wikipedia presence
        
        Args:
            brand_name: Brand to search for
            exact_match: If True, only return exact title matches
            
        Returns:
            Dict with Wikipedia presence data
        """
        print(f"Checking Wikipedia for: {brand_name}")
        
        try:
            # Search for articles
            search_params = {
                'action': 'query',
                'list': 'search',
                'srsearch': brand_name,
                'format': 'json',
                'srlimit': 5
            }
            
            response = requests.get(self.wikipedia_api, params=search_params, timeout=10)
            data = response.json()
            
            search_results = data.get('query', {}).get('search', [])
            
            if not search_results:
                return {
                    'platform': 'wikipedia',
                    'exists': False,
                    'brand_name': brand_name
                }
            
            # Get best match
            best_match = search_results[0]
            
            if exact_match and best_match['title'].lower() != brand_name.lower():
                return {
                    'platform': 'wikipedia',
                    'exists': False,
                    'brand_name': brand_name,
                    'closest_match': best_match['title']
                }
            
            # Get full article details
            page_title = best_match['title']
            article_data = self._get_wikipedia_article(page_title)
            
            return {
                'platform': 'wikipedia',
                'exists': True,
                'brand_name': brand_name,
                'article_title': page_title,
                'url': f"https://en.wikipedia.org/wiki/{quote(page_title.replace(' ', '_'))}",
                'summary': best_match.get('snippet', ''),
                'word_count': best_match.get('wordcount', 0),
                'details': article_data
            }
            
        except Exception as e:
            print(f"Wikipedia check error: {str(e)}")
            return {
                'platform': 'wikipedia',
                'exists': False,
                'brand_name': brand_name,
                'error': str(e)
            }
    
    def _get_wikipedia_article(self, page_title: str) -> Dict:
        """Get detailed article information"""
        try:
            # Get page info and stats
            params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'info|extlinks|categories|pageviews',
                'inprop': 'url',
                'ellimit': 'max',
                'format': 'json'
            }
            
            response = requests.get(self.wikipedia_api, params=params, timeout=10)
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            page_id = list(pages.keys())[0]
            page_data = pages[page_id]
            
            # Get external links (citations)
            external_links = page_data.get('extlinks', [])
            
            # Get categories
            categories = [
                cat['title'].replace('Category:', '') 
                for cat in page_data.get('categories', [])
            ]
            
            # Get page views (last 60 days average)
            pageviews = page_data.get('pageviews', {})
            if pageviews:
                total_views = sum(v for v in pageviews.values() if isinstance(v, int))
                avg_daily_views = total_views / len(pageviews) if pageviews else 0
            else:
                avg_daily_views = 0
            
            return {
                'page_id': page_id,
                'canonical_url': page_data.get('canonicalurl', ''),
                'external_links_count': len(external_links),
                'external_links': [link['*'] for link in external_links[:20]],  # Top 20
                'categories': categories,
                'avg_daily_pageviews': round(avg_daily_views, 0),
                'last_modified': page_data.get('touched', '')
            }
            
        except Exception as e:
            print(f"Error getting article details: {str(e)}")
            return {}
    
    def check_wikidata(self, brand_name: str) -> Dict:
        """
        Check Wikidata for structured brand data
        Wikidata is used by many AI systems for factual info
        """
        print(f"Checking Wikidata for: {brand_name}")
        
        try:
            # Search Wikidata
            search_params = {
                'action': 'wbsearchentities',
                'search': brand_name,
                'language': 'en',
                'format': 'json',
                'limit': 5
            }
            
            response = requests.get(self.wikidata_api, params=search_params, timeout=10)
            data = response.json()
            
            search_results = data.get('search', [])
            
            if not search_results:
                return {
                    'platform': 'wikidata',
                    'exists': False,
                    'brand_name': brand_name
                }
            
            # Get best match
            best_match = search_results[0]
            entity_id = best_match['id']
            
            # Get entity details
            entity_data = self._get_wikidata_entity(entity_id)
            
            return {
                'platform': 'wikidata',
                'exists': True,
                'brand_name': brand_name,
                'entity_id': entity_id,
                'label': best_match.get('label', ''),
                'description': best_match.get('description', ''),
                'url': f"https://www.wikidata.org/wiki/{entity_id}",
                'details': entity_data
            }
            
        except Exception as e:
            print(f"Wikidata check error: {str(e)}")
            return {
                'platform': 'wikidata',
                'exists': False,
                'brand_name': brand_name,
                'error': str(e)
            }
    
    def _get_wikidata_entity(self, entity_id: str) -> Dict:
        """Get full Wikidata entity details"""
        try:
            params = {
                'action': 'wbgetentities',
                'ids': entity_id,
                'format': 'json',
                'languages': 'en'
            }
            
            response = requests.get(self.wikidata_api, params=params, timeout=10)
            data = response.json()
            
            entity = data.get('entities', {}).get(entity_id, {})
            
            # Extract key properties
            claims = entity.get('claims', {})
            
            # Common properties
            properties_of_interest = {
                'P31': 'instance_of',  # What type of thing
                'P17': 'country',
                'P571': 'inception_date',
                'P112': 'founder',
                'P159': 'headquarters',
                'P856': 'official_website',
                'P452': 'industry',
                'P1128': 'employees'
            }
            
            extracted_props = {}
            for prop_id, prop_name in properties_of_interest.items():
                if prop_id in claims:
                    extracted_props[prop_name] = claims[prop_id]
            
            return {
                'claims_count': len(claims),
                'properties': extracted_props,
                'sitelinks_count': len(entity.get('sitelinks', {})),
                'sitelinks': list(entity.get('sitelinks', {}).keys())
            }
            
        except Exception as e:
            print(f"Error getting entity details: {str(e)}")
            return {}
    
    def check_google_knowledge_graph(self, brand_name: str) -> Dict:
        """
        Check Google Knowledge Graph
        Requires API key from Google Cloud Console
        """
        if not self.google_kg_api_key:
            return {
                'platform': 'google_knowledge_graph',
                'exists': False,
                'brand_name': brand_name,
                'error': 'API key not provided'
            }
        
        print(f"Checking Google Knowledge Graph for: {brand_name}")
        
        try:
            params = {
                'query': brand_name,
                'key': self.google_kg_api_key,
                'limit': 5,
                'indent': True
            }
            
            response = requests.get(self.kg_api, params=params, timeout=10)
            data = response.json()
            
            items = data.get('itemListElement', [])
            
            if not items:
                return {
                    'platform': 'google_knowledge_graph',
                    'exists': False,
                    'brand_name': brand_name
                }
            
            # Get best match
            best_match = items[0].get('result', {})
            
            return {
                'platform': 'google_knowledge_graph',
                'exists': True,
                'brand_name': brand_name,
                'kg_id': best_match.get('@id', ''),
                'name': best_match.get('name', ''),
                'types': best_match.get('@type', []),
                'description': best_match.get('description', ''),
                'detailed_description': best_match.get('detailedDescription', {}).get('articleBody', ''),
                'image_url': best_match.get('image', {}).get('contentUrl', '') if 'image' in best_match else '',
                'url': best_match.get('url', ''),
                'result_score': items[0].get('resultScore', 0)
            }
            
        except Exception as e:
            print(f"Knowledge Graph check error: {str(e)}")
            return {
                'platform': 'google_knowledge_graph',
                'exists': False,
                'brand_name': brand_name,
                'error': str(e)
            }
    
    def comprehensive_check(self, brand_name: str) -> Dict:
        """
        Check all knowledge platforms
        Returns unified report
        """
        print(f"\n=== Comprehensive Knowledge Check: {brand_name} ===\n")
        
        results = {
            'brand_name': brand_name,
            'platforms': {}
        }
        
        # Check each platform
        checks = [
            ('wikipedia', lambda: self.check_wikipedia(brand_name)),
            ('wikidata', lambda: self.check_wikidata(brand_name)),
            ('google_knowledge_graph', lambda: self.check_google_knowledge_graph(brand_name))
        ]
        
        for platform_name, check_func in checks:
            try:
                data = check_func()
                results['platforms'][platform_name] = data
            except Exception as e:
                print(f"Error checking {platform_name}: {str(e)}")
                results['platforms'][platform_name] = {
                    'platform': platform_name,
                    'exists': False,
                    'error': str(e)
                }
        
        # Calculate authority score
        results['authority_metrics'] = self._calculate_authority_score(results['platforms'])
        
        return results
    
    def _calculate_authority_score(self, platforms: Dict) -> Dict:
        """Calculate entity authority score based on knowledge platform presence"""
        score = 0
        max_score = 10
        
        # Wikipedia presence (40% of score)
        if platforms.get('wikipedia', {}).get('exists'):
            wiki_data = platforms['wikipedia']
            
            # Base points for existence
            score += 2
            
            # Points for article quality
            word_count = wiki_data.get('word_count', 0)
            if word_count > 500:
                score += 1
            if word_count > 2000:
                score += 1
            
            # Points for citations
            external_links = wiki_data.get('details', {}).get('external_links_count', 0)
            if external_links > 10:
                score += 0.5
            if external_links > 30:
                score += 0.5
        
        # Wikidata presence (30% of score)
        if platforms.get('wikidata', {}).get('exists'):
            wikidata = platforms['wikidata']
            
            # Base points
            score += 1.5
            
            # Points for data richness
            claims_count = wikidata.get('details', {}).get('claims_count', 0)
            if claims_count > 10:
                score += 0.75
            if claims_count > 30:
                score += 0.75
        
        # Knowledge Graph presence (30% of score)
        if platforms.get('google_knowledge_graph', {}).get('exists'):
            kg_data = platforms['google_knowledge_graph']
            
            # Base points
            score += 2
            
            # Points for match quality
            result_score = kg_data.get('result_score', 0)
            if result_score > 100:
                score += 0.5
            if result_score > 500:
                score += 0.5
        
        # Normalize to 0-10
        normalized_score = (score / max_score) * 10
        
        presence_count = sum(
            1 for p in platforms.values() 
            if p.get('exists', False)
        )
        
        return {
            'knowledge_authority_score': round(normalized_score, 1),
            'platforms_present': presence_count,
            'total_platforms_checked': len(platforms),
            'coverage_percentage': round((presence_count / len(platforms)) * 100, 1),
            'status': self._get_authority_status(normalized_score)
        }
    
    def _get_authority_status(self, score: float) -> str:
        """Get human-readable authority status"""
        if score >= 8:
            return 'Strong Entity Authority - Well established across knowledge platforms'
        elif score >= 6:
            return 'Moderate Authority - Present but could be strengthened'
        elif score >= 4:
            return 'Limited Authority - Minimal presence in knowledge systems'
        elif score >= 2:
            return 'Very Limited - Barely recognized as entity'
        else:
            return 'No Authority - Not recognized in knowledge platforms'


def main():
    """Example usage"""
    
    # Initialize checker (add your Google KG API key if you have one)
    checker = KnowledgePresenceChecker(
        google_kg_api_key='YOUR_API_KEY'  # Optional
    )
    
    # Single brand check
    brand = "Lyreco"
    print(f"Checking knowledge presence for: {brand}")
    
    results = checker.comprehensive_check(brand)
    print(json.dumps(results, indent=2))
    
    # Compare competitors
    print("\n=== Competitor Comparison ===")
    competitors = ["Lyreco", "Viking", "Staples"]
    
    comparison = {}
    for competitor in competitors:
        print(f"\nChecking {competitor}...")
        comp_results = checker.comprehensive_check(competitor)
        comparison[competitor] = comp_results['authority_metrics']
    
    print("\n=== Authority Scores ===")
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
