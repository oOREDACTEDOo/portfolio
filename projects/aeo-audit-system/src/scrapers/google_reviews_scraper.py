"""
Google Reviews Scraper for AEO Project
Fetches Google Business reviews and ratings via DataForSEO Business Data API.

Data sources:
1. DataForSEO Business Data API - Google Maps/Business reviews

This scraper fetches customer reviews from Google Business listings,
which is valuable for sentiment analysis and brand reputation tracking.

Output: JSON file with reviews for AI analysis.
"""

import requests
import base64
import re
from datetime import datetime
from typing import List, Dict, Optional
import time
import json
from pathlib import Path


class GoogleReviewsScraper:
    """
    Google Reviews scraper using DataForSEO Business Data API.

    Fetches:
    - Business listing information (name, address, rating, review count)
    - Individual reviews with text, rating, date, author
    - Review responses from business owners

    Perfect for:
    - Brand sentiment analysis
    - Competitor review monitoring
    - Customer feedback tracking
    """

    def __init__(
        self,
        dataforseo_login: str,
        dataforseo_password: str,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize Google Reviews scraper.

        Args:
            dataforseo_login: DataForSEO API login
            dataforseo_password: DataForSEO API password
            rate_limit_delay: Seconds to wait between API calls
        """
        self.dataforseo_login = dataforseo_login
        self.dataforseo_password = dataforseo_password
        self.dataforseo_base = "https://api.dataforseo.com/v3"
        self.rate_limit_delay = rate_limit_delay

        # Create auth header
        credentials = f"{dataforseo_login}:{dataforseo_password}"
        self.auth_header = base64.b64encode(credentials.encode()).decode()

        # Output directory
        self.output_dir = Path(__file__).parent.parent.parent / 'reports' / 'google_reviews'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def search_business(
        self,
        keyword: str,
        location_name: str = "Sydney,New South Wales,Australia",
        location_code: int = None,
        language_code: str = "en"
    ) -> Dict:
        """
        Search for a business on Google Maps to get its place_id.

        Args:
            keyword: Business name/search query (e.g., "Bunnings Warehouse")
            location_name: Location in format "City,State,Country"
                          (e.g., "Sydney,New South Wales,Australia")
            location_code: DataForSEO location code (optional, overrides location_name)
            language_code: Language code for results

        Returns:
            Dict with business search results
        """
        payload = [{
            'keyword': keyword,
            'language_code': language_code
        }]

        # Add location
        if location_code:
            payload[0]['location_code'] = location_code
        else:
            payload[0]['location_name'] = location_name

        print(f"  Searching for business: '{keyword}' in {location_name}...")
        response = self._make_request('business_data/google/my_business_info/live', payload)

        if response.get('error'):
            print(f"    Error: {response.get('message', 'Unknown error')}")
            return {'error': response.get('message'), 'results': []}

        # Parse results
        results = []
        tasks = response.get('tasks', [])
        for task in tasks:
            task_results = task.get('result') or []
            for item in task_results:
                items = item.get('items') or []
                for business in items:
                    results.append({
                        'title': business.get('title', ''),
                        'place_id': business.get('place_id', ''),
                        'cid': business.get('cid', ''),
                        'feature_id': business.get('feature_id', ''),
                        'address': business.get('address', ''),
                        'rating': business.get('rating', {}).get('value') if business.get('rating') else None,
                        'review_count': business.get('rating', {}).get('votes_count') if business.get('rating') else 0,
                        'category': business.get('category', ''),
                        'phone': business.get('phone', ''),
                        'url': business.get('url', ''),
                        'domain': business.get('domain', '')
                    })

        return {
            'keyword': keyword,
            'location': location_name,
            'results_count': len(results),
            'results': results
        }

    def get_reviews(
        self,
        keyword: str = None,
        place_id: str = None,
        feature_id: str = None,
        cid: str = None,
        location_name: str = "Sydney,New South Wales,Australia",
        location_code: int = None,
        language_code: str = "en",
        depth: int = 100,
        sort_by: str = "newest"
    ) -> Dict:
        """
        Get Google reviews for a business using async task_post/task_get.

        Args:
            keyword: Business name/search query (if place_id not known)
            place_id: Google Place ID (preferred if known)
            feature_id: Google feature ID (alternative to place_id)
            cid: Google CID (alternative to place_id)
            location_name: Location in format "City,State,Country"
            location_code: DataForSEO location code
            language_code: Language code
            depth: Number of reviews to fetch (max varies by plan)
            sort_by: Sort order - "newest", "highest_rating", "lowest_rating", "relevant"

        Returns:
            Dict with business info and reviews
        """
        results = {
            'scraped_at': datetime.now().isoformat(),
            'business': {},
            'reviews': [],
            'summary': {}
        }

        # Build payload - map sort_by to API expected values
        sort_by_map = {
            'newest': 'newest',
            'highest_rating': 'highest_rating',
            'lowest_rating': 'lowest_rating',
            'most_relevant': 'relevant',
            'relevant': 'relevant'
        }
        api_sort_by = sort_by_map.get(sort_by, 'newest')

        payload = [{
            'language_code': language_code,
            'depth': depth,
            'sort_by': api_sort_by
        }]

        # Add identifier (prefer place_id > cid > keyword search)
        if place_id:
            payload[0]['place_id'] = place_id
        elif cid:
            payload[0]['cid'] = cid
        elif keyword:
            payload[0]['keyword'] = keyword
        else:
            return {'error': 'Must provide keyword, place_id, or cid'}

        # Add location
        if location_code:
            payload[0]['location_code'] = location_code
        else:
            payload[0]['location_name'] = location_name

        identifier = place_id or cid or keyword
        print(f"  Fetching reviews for: '{identifier}'...")
        print(f"  Sort by: {api_sort_by}, Depth: {depth}")

        # Step 1: Submit task
        print(f"  Submitting review task...")
        post_response = self._make_request('business_data/google/reviews/task_post', payload)

        if post_response.get('error'):
            print(f"    Error submitting task: {post_response.get('message', 'Unknown error')}")
            results['error'] = post_response.get('message')
            return results

        # Get task ID
        task_id = None
        tasks = post_response.get('tasks', [])
        for task in tasks:
            if task.get('id'):
                task_id = task['id']
                break

        if not task_id:
            print(f"    Error: No task ID returned")
            results['error'] = 'No task ID returned'
            return results

        print(f"  Task submitted: {task_id}")
        print(f"  Waiting for results...")

        # Step 2: Poll for results (with timeout)
        max_attempts = 30  # 30 attempts * 2 seconds = 60 seconds max
        for attempt in range(max_attempts):
            time.sleep(2)  # Wait 2 seconds between polls

            get_response = self._make_request(f'business_data/google/reviews/task_get/{task_id}', None)

            if get_response.get('error'):
                print(f"    Error getting task: {get_response.get('message', 'Unknown error')}")
                continue

            # Check task status
            tasks = get_response.get('tasks', [])
            for task in tasks:
                status = task.get('status_code')
                if status == 20000:  # Success
                    print(f"  Task completed!")
                    # Parse results
                    task_results = task.get('result') or []
                    for item in task_results:
                        # Business info
                        results['business'] = {
                            'title': item.get('title', ''),
                            'place_id': item.get('place_id', ''),
                            'cid': item.get('cid', ''),
                            'address': item.get('address', ''),
                            'rating': item.get('rating', {}).get('value') if item.get('rating') else None,
                            'total_reviews': item.get('rating', {}).get('votes_count') if item.get('rating') else 0,
                            'reviews_fetched': item.get('reviews_count', 0)
                        }

                        # Individual reviews
                        reviews_data = item.get('items') or []
                        for review in reviews_data:
                            review_entry = {
                                'review_id': review.get('review_id', ''),
                                'rating': review.get('rating', {}).get('value') if review.get('rating') else None,
                                'text': review.get('review_text', ''),
                                'timestamp': review.get('timestamp', ''),
                                'time_ago': review.get('time_ago', ''),
                                'author': {
                                    'name': review.get('profile_name', ''),
                                    'url': review.get('profile_url', ''),
                                    'image_url': review.get('profile_image_url', ''),
                                    'reviews_count': review.get('reviews_count', 0),
                                    'photos_count': review.get('photos_count', 0)
                                },
                                'images': review.get('review_images', []),
                                'owner_response': None
                            }

                            # Check for owner response
                            if review.get('owner_answer'):
                                review_entry['owner_response'] = {
                                    'text': review.get('owner_answer', ''),
                                    'timestamp': review.get('owner_timestamp', ''),
                                    'time_ago': review.get('owner_time_ago', '')
                                }

                            results['reviews'].append(review_entry)

                    # Generate summary
                    if results['reviews']:
                        ratings = [r['rating'] for r in results['reviews'] if r['rating'] is not None]
                        results['summary'] = {
                            'total_reviews_fetched': len(results['reviews']),
                            'average_rating': round(sum(ratings) / len(ratings), 2) if ratings else None,
                            'rating_distribution': self._calculate_rating_distribution(ratings),
                            'reviews_with_text': sum(1 for r in results['reviews'] if r['text']),
                            'reviews_with_owner_response': sum(1 for r in results['reviews'] if r['owner_response']),
                            'reviews_with_images': sum(1 for r in results['reviews'] if r['images'])
                        }
                    return results

                elif status == 40000:  # Task not found or failed
                    print(f"    Task failed with status {status}")
                    results['error'] = f'Task failed with status {status}'
                    return results

            # Still processing, continue polling
            if attempt % 5 == 0:
                print(f"  Still waiting... (attempt {attempt + 1}/{max_attempts})")

        print(f"    Timeout waiting for task results")
        results['error'] = 'Timeout waiting for task results'
        return results

    def _make_request(self, endpoint: str, data) -> Dict:
        """
        Make authenticated request to DataForSEO API.

        Args:
            endpoint: API endpoint path
            data: Request payload (can be None for GET requests)

        Returns:
            API response as dict
        """
        headers = {
            'Authorization': f'Basic {self.auth_header}',
            'Content-Type': 'application/json'
        }

        url = f"{self.dataforseo_base}/{endpoint}"

        if data is None:
            # GET request
            response = requests.get(url, headers=headers, timeout=60)
        else:
            # POST request
            response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            return response.json()
        else:
            return {
                'error': True,
                'status_code': response.status_code,
                'message': response.text
            }

    def _calculate_rating_distribution(self, ratings: List[float]) -> Dict[str, int]:
        """Calculate distribution of ratings."""
        distribution = {'5_star': 0, '4_star': 0, '3_star': 0, '2_star': 0, '1_star': 0}
        for rating in ratings:
            if rating >= 4.5:
                distribution['5_star'] += 1
            elif rating >= 3.5:
                distribution['4_star'] += 1
            elif rating >= 2.5:
                distribution['3_star'] += 1
            elif rating >= 1.5:
                distribution['2_star'] += 1
            else:
                distribution['1_star'] += 1
        return distribution

    def scrape_brand_reviews(
        self,
        brand_name: str,
        search_queries: List[str] = None,
        location_name: str = "Sydney,New South Wales,Australia",
        reviews_per_location: int = 100,
        sort_by: str = "newest"
    ) -> Dict:
        """
        Scrape Google reviews for a brand across multiple locations/queries.

        Args:
            brand_name: Brand name for reporting
            search_queries: List of search queries (e.g., ["Brand Name Sydney", "Brand Name Melbourne"])
                           If None, just searches for brand_name
            location_name: Location in format "City,State,Country"
            reviews_per_location: Number of reviews to fetch per location
            sort_by: Sort order for reviews

        Returns:
            Dict with all results
        """
        if search_queries is None:
            search_queries = [brand_name]

        results = {
            'metadata': {
                'brand': brand_name,
                'scraped_at': datetime.now().isoformat(),
                'search_queries': search_queries,
                'location': location_name,
                'sort_by': sort_by
            },
            'locations': [],
            'all_reviews': [],
            'summary': {}
        }

        print(f"\nScraping Google Reviews for '{brand_name}'...")
        print(f"Search queries: {len(search_queries)}")
        print(f"Location: {location_name}")

        for query in search_queries:
            print(f"\n[Query: {query}]")

            # First search for the business
            search_results = self.search_business(
                keyword=query,
                location_name=location_name
            )

            time.sleep(self.rate_limit_delay)

            if not search_results.get('results'):
                print(f"  No businesses found for '{query}'")
                continue

            # Get reviews for the first (most relevant) result
            business = search_results['results'][0]
            print(f"  Found: {business['title']}")
            print(f"  Rating: {business['rating']} ({business['review_count']} reviews)")

            # Fetch reviews using place_id if available
            identifier_kwargs = {}
            if business.get('place_id'):
                identifier_kwargs['place_id'] = business['place_id']
            elif business.get('feature_id'):
                identifier_kwargs['feature_id'] = business['feature_id']
            elif business.get('cid'):
                identifier_kwargs['cid'] = business['cid']
            else:
                identifier_kwargs['keyword'] = query

            reviews_data = self.get_reviews(
                **identifier_kwargs,
                location_name=location_name,
                depth=reviews_per_location,
                sort_by=sort_by
            )

            time.sleep(self.rate_limit_delay)

            location_result = {
                'query': query,
                'business': reviews_data.get('business', {}),
                'reviews': reviews_data.get('reviews', []),
                'summary': reviews_data.get('summary', {})
            }
            results['locations'].append(location_result)
            results['all_reviews'].extend(reviews_data.get('reviews', []))

            print(f"  Fetched: {len(reviews_data.get('reviews', []))} reviews")

        # Generate overall summary
        all_ratings = [r['rating'] for r in results['all_reviews'] if r['rating'] is not None]
        results['summary'] = {
            'total_locations': len(results['locations']),
            'total_reviews': len(results['all_reviews']),
            'overall_average_rating': round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else None,
            'rating_distribution': self._calculate_rating_distribution(all_ratings),
            'reviews_with_text': sum(1 for r in results['all_reviews'] if r['text']),
            'reviews_with_owner_response': sum(1 for r in results['all_reviews'] if r['owner_response'])
        }

        return results

    def save_results(self, results: Dict, brand_name: str) -> str:
        """
        Save results to JSON file.

        Args:
            results: Scrape results
            brand_name: Brand name for filename

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_brand = re.sub(r'[^a-z0-9]+', '_', brand_name.lower()).strip('_')

        filepath = self.output_dir / f"{safe_brand}_google_reviews_{timestamp}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\nSaved to: {filepath}")
        return str(filepath)

    def extract_reviews_for_sentiment(self, results: Dict) -> List[Dict]:
        """
        Extract reviews in a simplified format optimized for AI sentiment analysis.

        Args:
            results: Full scrape results

        Returns:
            List of simplified review dicts
        """
        simplified = []
        for review in results.get('all_reviews', []):
            if review.get('text'):  # Only include reviews with text
                simplified.append({
                    'rating': review['rating'],
                    'text': review['text'],
                    'date': review.get('timestamp', review.get('time_ago', '')),
                    'has_owner_response': bool(review.get('owner_response')),
                    'author_review_count': review.get('author', {}).get('reviews_count', 0)
                })
        return simplified
