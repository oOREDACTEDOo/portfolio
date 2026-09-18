"""
Social Media Visibility Scraper for AEO Project
Fetches brand social engagement metrics from Facebook and Pinterest via DataForSEO.

Data sources:
1. DataForSEO Social Media API - Facebook likes, Pinterest pins

Note: This scraper checks engagement metrics for specific URLs (brand website,
product pages, etc.) - not social media profile searches.

Output: Separate JSON files per platform for AI analysis.
"""

import requests
import base64
import re
from datetime import datetime
from typing import List, Dict, Optional
import time
import json
from pathlib import Path


class SocialMediaScraper:
    """
    Social media engagement scraper using DataForSEO API.

    Fetches:
    - Facebook: Like counts for URLs (via Facebook Like Button embeds)
    - Pinterest: Pin counts for URLs (via Pinterest Save Button embeds)

    Note: This measures how often brand URLs are shared/liked on social platforms,
    not brand mentions within social media posts.
    """

    def __init__(
        self,
        dataforseo_login: str,
        dataforseo_password: str,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize social media scraper.

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
        self.output_dir = Path(__file__).parent.parent.parent / 'reports' / 'social_media'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _make_request(self, endpoint: str, data: List[Dict]) -> Dict:
        """
        Make authenticated request to DataForSEO API.

        Args:
            endpoint: API endpoint path
            data: Request payload

        Returns:
            API response as dict
        """
        headers = {
            'Authorization': f'Basic {self.auth_header}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f"{self.dataforseo_base}/{endpoint}",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                'error': True,
                'status_code': response.status_code,
                'message': response.text
            }

    def get_facebook_likes(self, urls: List[str], tag: str = None) -> Dict:
        """
        Get Facebook like counts for URLs.

        Args:
            urls: List of URLs to check (max 10 per request)
            tag: Optional tag to identify this request

        Returns:
            Dict with results for each URL
        """
        results = {
            'platform': 'facebook',
            'scraped_at': datetime.now().isoformat(),
            'total_urls': len(urls),
            'total_likes': 0,
            'urls': []
        }

        # Process in batches of 10 (API limit)
        for i in range(0, len(urls), 10):
            batch = urls[i:i+10]

            payload = [{
                'targets': batch,
                'tag': tag or f'facebook_batch_{i}'
            }]

            print(f"  Checking Facebook likes for {len(batch)} URLs...")
            response = self._make_request('business_data/social_media/facebook/live', payload)

            if response.get('error'):
                print(f"    Error: {response.get('message', 'Unknown error')}")
                continue

            # Parse results
            tasks = response.get('tasks', [])
            for task in tasks:
                task_results = task.get('result') or []
                for item in task_results:
                    url_data = {
                        'url': item.get('page_url', ''),
                        'like_count': item.get('like_count', 0)
                    }
                    results['urls'].append(url_data)
                    results['total_likes'] += url_data['like_count']

            time.sleep(self.rate_limit_delay)

        results['urls_processed'] = len(results['urls'])
        return results

    def get_pinterest_pins(self, urls: List[str], tag: str = None) -> Dict:
        """
        Get Pinterest pin counts for URLs.

        Args:
            urls: List of URLs to check (max 10 per request)
            tag: Optional tag to identify this request

        Returns:
            Dict with results for each URL
        """
        results = {
            'platform': 'pinterest',
            'scraped_at': datetime.now().isoformat(),
            'total_urls': len(urls),
            'total_pins': 0,
            'urls': []
        }

        # Process in batches of 10 (API limit)
        for i in range(0, len(urls), 10):
            batch = urls[i:i+10]

            payload = [{
                'targets': batch,
                'tag': tag or f'pinterest_batch_{i}'
            }]

            print(f"  Checking Pinterest pins for {len(batch)} URLs...")
            response = self._make_request('business_data/social_media/pinterest/live', payload)

            if response.get('error'):
                print(f"    Error: {response.get('message', 'Unknown error')}")
                continue

            # Parse results
            tasks = response.get('tasks', [])
            for task in tasks:
                task_results = task.get('result') or []
                for item in task_results:
                    url_data = {
                        'url': item.get('page_url', ''),
                        'pins_count': item.get('pins_count', 0)
                    }
                    results['urls'].append(url_data)
                    results['total_pins'] += url_data['pins_count']

            time.sleep(self.rate_limit_delay)

        results['urls_processed'] = len(results['urls'])
        return results

    def scrape_brand_social_metrics(
        self,
        brand_name: str,
        urls: List[str],
        platforms: List[str] = None
    ) -> Dict:
        """
        Scrape social media metrics for a brand's URLs.

        Args:
            brand_name: Brand name for reporting
            urls: List of brand URLs to check
            platforms: Which platforms to check ['facebook', 'pinterest'] (default: both)

        Returns:
            Dict with results per platform
        """
        if platforms is None:
            platforms = ['facebook', 'pinterest']

        results = {
            'metadata': {
                'brand': brand_name,
                'scraped_at': datetime.now().isoformat(),
                'urls_checked': urls,
                'platforms': platforms
            },
            'facebook': None,
            'pinterest': None,
            'summary': {}
        }

        print(f"\nScraping social metrics for '{brand_name}'...")
        print(f"URLs to check: {len(urls)}")
        print(f"Platforms: {', '.join(platforms)}")

        # Facebook
        if 'facebook' in platforms:
            print("\n[Facebook]")
            results['facebook'] = self.get_facebook_likes(urls, tag=brand_name)
            print(f"  Total likes: {results['facebook']['total_likes']}")

        # Pinterest
        if 'pinterest' in platforms:
            print("\n[Pinterest]")
            results['pinterest'] = self.get_pinterest_pins(urls, tag=brand_name)
            print(f"  Total pins: {results['pinterest']['total_pins']}")

        # Summary
        results['summary'] = {
            'total_facebook_likes': results['facebook']['total_likes'] if results['facebook'] else 0,
            'total_pinterest_pins': results['pinterest']['total_pins'] if results['pinterest'] else 0,
            'total_social_engagement': (
                (results['facebook']['total_likes'] if results['facebook'] else 0) +
                (results['pinterest']['total_pins'] if results['pinterest'] else 0)
            )
        }

        return results

    def save_results(self, results: Dict, brand_name: str) -> Dict[str, str]:
        """
        Save results to separate JSON files per platform.

        Args:
            results: Scrape results
            brand_name: Brand name for filename

        Returns:
            Dict of {platform: filepath}
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_brand = re.sub(r'[^a-z0-9]+', '_', brand_name.lower()).strip('_')

        saved_files = {}

        # Save combined report
        combined_path = self.output_dir / f"{safe_brand}_social_combined_{timestamp}.json"
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        saved_files['combined'] = str(combined_path)

        # Save Facebook separately
        if results.get('facebook'):
            fb_data = {
                'metadata': {
                    'brand': brand_name,
                    'platform': 'facebook',
                    'scraped_at': results['metadata']['scraped_at']
                },
                **results['facebook']
            }
            fb_path = self.output_dir / f"{safe_brand}_facebook_{timestamp}.json"
            with open(fb_path, 'w', encoding='utf-8') as f:
                json.dump(fb_data, f, indent=2, ensure_ascii=False)
            saved_files['facebook'] = str(fb_path)

        # Save Pinterest separately
        if results.get('pinterest'):
            pin_data = {
                'metadata': {
                    'brand': brand_name,
                    'platform': 'pinterest',
                    'scraped_at': results['metadata']['scraped_at']
                },
                **results['pinterest']
            }
            pin_path = self.output_dir / f"{safe_brand}_pinterest_{timestamp}.json"
            with open(pin_path, 'w', encoding='utf-8') as f:
                json.dump(pin_data, f, indent=2, ensure_ascii=False)
            saved_files['pinterest'] = str(pin_path)

        return saved_files


def discover_brand_urls(brand_domain: str, dataforseo_login: str, dataforseo_password: str) -> List[str]:
    """
    Use DataForSEO to discover URLs for a brand domain.

    This can help find product pages, blog posts, etc. that might have
    social engagement.

    Args:
        brand_domain: Main domain (e.g., 'clientl.example.com')
        dataforseo_login: DataForSEO login
        dataforseo_password: DataForSEO password

    Returns:
        List of discovered URLs
    """
    # For now, return common URL patterns
    # In the future, this could use DataForSEO's site explorer
    base_url = f"https://www.{brand_domain}" if not brand_domain.startswith('www.') else f"https://{brand_domain}"

    return [
        base_url,
        f"{base_url}/",
        f"{base_url}/products",
        f"{base_url}/blog",
        f"{base_url}/about",
        f"{base_url}/collections"
    ]
