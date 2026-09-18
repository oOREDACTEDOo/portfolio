"""
Reddit Visibility Scraper for AEO Project
Optimized for AI sentiment and visibility analysis
Collects full post content without truncation

Data sources:
1. DataForSEO Google search (recommended) - Searches Google for "brand" site:reddit.com
2. Reddit .json endpoints - Direct subreddit search (no auth needed)

Note: Pullpush.io was removed as it has been down since April 2025.
Future: Reddit API via PRAW when access is approved.

Subreddit Watchlist Feature:
- Automatically tracks subreddits where brand mentions are found
- Saves client-specific watchlists for MCP server monitoring
- Watchlists stored in data/watchlists/{client_slug}.json
"""

import requests
import base64
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import json
from pathlib import Path
from urllib.parse import quote_plus
import unicodedata


class RedditVisibilityScraper:
    """
    Reddit scraper optimized for AI visibility analysis.
    Collects brand mentions with full content for batch AI processing.

    Data sources:
    1. DataForSEO Google search - Best results, finds posts Google indexed
    2. Reddit .json endpoints - Direct search, no auth needed

    Future: Reddit API (PRAW) when access is approved
    """

    def __init__(
        self,
        user_agent: str = None,
        rate_limit_delay: float = 2.0,
        dataforseo_login: str = None,
        dataforseo_password: str = None
    ):
        """
        Initialize scraper.

        Args:
            user_agent: Optional custom user agent string
            rate_limit_delay: Seconds to wait between requests (default: 2.0)
            dataforseo_login: Optional DataForSEO login for Google search
            dataforseo_password: Optional DataForSEO password
        """
        self.user_agent = user_agent or 'AEO-Visibility-Scraper/1.0 (brand monitoring research)'
        self.reddit_base = "https://www.reddit.com"
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent
        })

        # DataForSEO credentials (optional)
        self.dataforseo_login = dataforseo_login
        self.dataforseo_password = dataforseo_password
        self.dataforseo_base = "https://api.dataforseo.com/v3"

        # Watchlist directory for MCP monitoring
        self.watchlist_dir = Path(__file__).parent.parent.parent / 'data' / 'watchlists'
        self.watchlist_dir.mkdir(parents=True, exist_ok=True)

    def scrape_brand_mentions(
        self,
        brand_name: str,
        subreddits: List[str],
        days_back: int = 180,
        include_comments: bool = False,
        use_google_search: bool = False,
        strict_match: bool = False
    ) -> Dict:
        """
        Scrape Reddit for brand mentions optimized for AI analysis.

        Args:
            brand_name: Brand to search for
            subreddits: List of subreddit names to search
            days_back: How far back to search (days)
            include_comments: Whether to also search comments (slower)
            use_google_search: Use DataForSEO to find additional Reddit posts via Google
            strict_match: Only include posts that actually contain the brand name (default: False)

        Returns:
            Dict with metadata, mentions list, and summary stats
        """
        all_mentions = []
        errors = []
        sources_used = set()

        # Method 0: Google search for Reddit posts (if enabled and credentials available)
        if use_google_search and self.dataforseo_login and self.dataforseo_password:
            print(f"\nSearching Google for '{brand_name}' Reddit mentions...")
            google_mentions = self._search_google_for_reddit(brand_name, days_back)
            if google_mentions:
                all_mentions.extend(google_mentions)
                sources_used.add('google_dataforseo')
                print(f"  Found {len(google_mentions)} posts via Google")
            time.sleep(self.rate_limit_delay)
        elif use_google_search:
            print("\nGoogle search requested but DataForSEO credentials not configured. Skipping.")

        print(f"\nSearching for '{brand_name}' across {len(subreddits)} subreddits...")

        for i, subreddit_name in enumerate(subreddits, 1):
            print(f"  [{i}/{len(subreddits)}] r/{subreddit_name}...", end=" ", flush=True)
            sub_mentions = 0

            try:
                # Reddit .json endpoint search
                reddit_mentions = self._search_reddit_json(
                    brand_name, subreddit_name
                )
                if reddit_mentions:
                    all_mentions.extend(reddit_mentions)
                    sources_used.add('reddit_json')
                    sub_mentions += len(reddit_mentions)

                print(f"{sub_mentions} found")
                time.sleep(self.rate_limit_delay)  # Rate limiting between subreddits

            except Exception as e:
                print(f"error: {str(e)[:50]}")
                errors.append({
                    'subreddit': subreddit_name,
                    'error': str(e)
                })
                continue

        # Deduplicate by URL
        unique_mentions = self._deduplicate(all_mentions)

        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        unique_mentions = [
            m for m in unique_mentions
            if m.get('created_utc', 0) > cutoff_date.timestamp()
        ]

        # Strict match filter: only keep posts that actually contain the brand name
        if strict_match:
            pre_filter_count = len(unique_mentions)
            unique_mentions = self._filter_by_brand_mention(unique_mentions, brand_name)
            filtered_out = pre_filter_count - len(unique_mentions)
            if filtered_out > 0:
                print(f"\nFiltered out {filtered_out} posts that didn't mention '{brand_name}'")

        # Sort by engagement (upvotes + comments)
        unique_mentions.sort(
            key=lambda x: x.get('upvotes', 0) + x.get('comment_count', 0),
            reverse=True
        )

        print(f"\nTotal unique mentions: {len(unique_mentions)}")

        # Build response
        return {
            'metadata': {
                'brand': brand_name,
                'scraped_at': datetime.now().isoformat(),
                'subreddits_searched': subreddits,
                'days_back': days_back,
                'total_mentions': len(unique_mentions),
                'sources_used': list(sources_used),
                'errors': errors if errors else None
            },
            'mentions': unique_mentions,
            'summary': self._calculate_summary(unique_mentions)
        }

    # NOTE: Pullpush.io has been down since April 2025
    # If it comes back online, methods can be re-added here
    # For now, we rely on Google/DataForSEO and Reddit .json endpoints

    def _placeholder_for_future_reddit_api(self) -> None:
        """
        Placeholder for Reddit API integration.
        When Reddit API access is approved, add PRAW-based search here.
        This would complement Google search by finding recent posts
        that haven't been indexed by Google yet.
        """
        pass

    def _deprecated_pullpush(self) -> None:
        """Pullpush.io was shut down in April 2025. Kept as reference."""
        # URL was: https://api.pullpush.io/reddit/search/submission/
        # Alternatives to monitor: reveddit.com, unddit.com
        pass

    def _search_reddit_json(
        self,
        brand_name: str,
        subreddit_name: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search using Reddit's .json endpoint (no auth required).

        This method appends .json to Reddit URLs to get JSON responses.
        Rate limited but doesn't require API credentials.
        """
        mentions = []

        try:
            # URL encode the brand name for search
            encoded_brand = quote_plus(f'"{brand_name}"')

            # Search endpoint with .json
            url = f"{self.reddit_base}/r/{subreddit_name}/search.json"
            params = {
                'q': brand_name,
                'restrict_sr': 'true',  # Restrict to subreddit
                'sort': 'relevance',
                'limit': limit,
                't': 'year'  # Time filter: year
            }

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Reddit returns nested structure
                children = data.get('data', {}).get('children', [])

                for child in children:
                    item = child.get('data', {})
                    created_utc = item.get('created_utc', 0)

                    mention = {
                        'title': item.get('title', ''),
                        'body': item.get('selftext', ''),  # Full text
                        'url': f"https://reddit.com{item.get('permalink', '')}",
                        'subreddit': item.get('subreddit', ''),
                        'author': item.get('author', '[deleted]'),
                        'upvotes': item.get('score', 0),
                        'upvote_ratio': item.get('upvote_ratio'),
                        'comment_count': item.get('num_comments', 0),
                        'created_utc': created_utc,
                        'created_date': datetime.fromtimestamp(created_utc).isoformat() if created_utc else None,
                        'source': 'reddit_json'
                    }
                    mentions.append(mention)

            elif response.status_code == 429:
                # Rate limited - back off and retry once
                print("(rate limited, waiting)...", end=" ", flush=True)
                time.sleep(10)
                response = self.session.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    children = data.get('data', {}).get('children', [])
                    for child in children:
                        item = child.get('data', {})
                        created_utc = item.get('created_utc', 0)
                        mention = {
                            'title': item.get('title', ''),
                            'body': item.get('selftext', ''),
                            'url': f"https://reddit.com{item.get('permalink', '')}",
                            'subreddit': item.get('subreddit', ''),
                            'author': item.get('author', '[deleted]'),
                            'upvotes': item.get('score', 0),
                            'upvote_ratio': item.get('upvote_ratio'),
                            'comment_count': item.get('num_comments', 0),
                            'created_utc': created_utc,
                            'created_date': datetime.fromtimestamp(created_utc).isoformat() if created_utc else None,
                            'source': 'reddit_json'
                        }
                        mentions.append(mention)

        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            pass

        return mentions

    def _search_reddit_all(
        self,
        brand_name: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search across all of Reddit using .json endpoint.
        Use this for broad searches not limited to specific subreddits.
        """
        mentions = []

        try:
            url = f"{self.reddit_base}/search.json"
            params = {
                'q': brand_name,
                'sort': 'relevance',
                'limit': limit,
                't': 'year'
            }

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                children = data.get('data', {}).get('children', [])

                for child in children:
                    item = child.get('data', {})
                    created_utc = item.get('created_utc', 0)

                    mention = {
                        'title': item.get('title', ''),
                        'body': item.get('selftext', ''),
                        'url': f"https://reddit.com{item.get('permalink', '')}",
                        'subreddit': item.get('subreddit', ''),
                        'author': item.get('author', '[deleted]'),
                        'upvotes': item.get('score', 0),
                        'upvote_ratio': item.get('upvote_ratio'),
                        'comment_count': item.get('num_comments', 0),
                        'created_utc': created_utc,
                        'created_date': datetime.fromtimestamp(created_utc).isoformat() if created_utc else None,
                        'source': 'reddit_json_all'
                    }
                    mentions.append(mention)

        except Exception:
            pass

        return mentions

    def _search_google_for_reddit(
        self,
        brand_name: str,
        days_back: int = 180,
        num_results: int = 100
    ) -> List[Dict]:
        """
        Search Google for Reddit posts mentioning the brand using DataForSEO.

        This finds posts that Reddit's own search might miss, especially
        older posts or posts in unexpected subreddits.

        Args:
            brand_name: Brand to search for
            days_back: How far back to search (not directly supported, but filters results)
            num_results: Number of Google results to fetch

        Returns:
            List of mention dicts from Reddit posts found via Google
        """
        mentions = []

        if not self.dataforseo_login or not self.dataforseo_password:
            return mentions

        try:
            # Create auth header
            credentials = f"{self.dataforseo_login}:{self.dataforseo_password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json'
            }

            # Build search queries for brand variations
            # e.g., "Client L" and "Client L"
            search_queries = self._get_google_search_queries(brand_name)

            all_urls_found = set()

            for search_query in search_queries:
                print(f"    Searching: {search_query}")

                # DataForSEO SERP API request
                post_data = [{
                    "keyword": search_query,
                    "location_name": "United States",
                    "language_name": "English",
                    "depth": num_results,
                    "se_domain": "google.com"
                }]

                response = requests.post(
                    f"{self.dataforseo_base}/serp/google/organic/live/advanced",
                    headers=headers,
                    json=post_data,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract results
                    tasks = data.get('tasks', [])
                    for task in tasks:
                        result = task.get('result') or []
                        for r in result:
                            items = r.get('items') or []
                            for item in items:
                                if item.get('type') != 'organic':
                                    continue

                                url = item.get('url', '')

                                # Only process Reddit post URLs
                                if not re.match(r'https?://(www\.)?reddit\.com/r/\w+/comments/', url):
                                    continue

                                # Skip if we already processed this URL
                                if url in all_urls_found:
                                    continue
                                all_urls_found.add(url)

                                # Fetch the actual Reddit post data + comments via .json
                                post_mentions = self._fetch_reddit_post_json(url, brand_name)
                                for pm in post_mentions:
                                    pm['source'] = 'google_dataforseo'
                                    pm['google_rank'] = item.get('rank_absolute', 0)
                                    pm['search_query'] = search_query
                                    mentions.append(pm)

                                time.sleep(self.rate_limit_delay)
                else:
                    print(f"    DataForSEO error: {response.status_code}")

                time.sleep(1)  # Brief pause between queries


        except Exception as e:
            print(f"  Google search error: {str(e)[:50]}")

        return mentions

    def _fetch_reddit_post_json(self, url: str, brand_name: str = None) -> List[Dict]:
        """
        Fetch a single Reddit post's data and comments using the .json endpoint.

        Args:
            url: Reddit post URL
            brand_name: If provided, also extract comments mentioning the brand

        Returns:
            List of mention dicts (post + any brand-mentioning comments)
        """
        mentions = []

        try:
            # Convert URL to .json endpoint
            json_url = url.rstrip('/') + '.json'

            response = self.session.get(json_url, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Reddit returns array: [post_data, comments_data]
                if isinstance(data, list) and len(data) > 0:
                    post_listing = data[0]
                    children = post_listing.get('data', {}).get('children', [])

                    if children:
                        item = children[0].get('data', {})
                        created_utc = item.get('created_utc', 0)

                        post_mention = {
                            'title': item.get('title', ''),
                            'body': item.get('selftext', ''),
                            'url': f"https://reddit.com{item.get('permalink', '')}",
                            'subreddit': item.get('subreddit', ''),
                            'author': item.get('author', '[deleted]'),
                            'upvotes': item.get('score', 0),
                            'upvote_ratio': item.get('upvote_ratio'),
                            'comment_count': item.get('num_comments', 0),
                            'created_utc': created_utc,
                            'created_date': datetime.fromtimestamp(created_utc).isoformat() if created_utc else None,
                            'is_comment': False,
                        }
                        mentions.append(post_mention)

                        # If brand_name provided, also search comments
                        if brand_name and len(data) > 1:
                            comment_mentions = self._extract_brand_comments(
                                data[1], brand_name, item.get('permalink', '')
                            )
                            mentions.extend(comment_mentions)

        except Exception:
            pass

        return mentions

    def _extract_brand_comments(
        self,
        comments_data: Dict,
        brand_name: str,
        post_permalink: str
    ) -> List[Dict]:
        """
        Extract comments that mention the brand from a Reddit post's comments.

        Args:
            comments_data: The comments portion of Reddit .json response
            brand_name: Brand to search for
            post_permalink: The parent post's permalink

        Returns:
            List of comment mention dicts
        """
        mentions = []
        brand_variations = self._get_brand_variations(brand_name)

        def search_comments(children, depth=0):
            if depth > 5:  # Limit recursion depth
                return
            for child in children:
                if child.get('kind') != 't1':
                    continue

                comment_data = child.get('data', {})
                body = comment_data.get('body', '')
                body_lower = body.lower()

                # Check if brand is mentioned
                if any(variation in body_lower for variation in brand_variations):
                    created_utc = comment_data.get('created_utc', 0)

                    mentions.append({
                        'title': f"[Comment on: {post_permalink.split('/')[-2] if post_permalink else 'post'}]",
                        'body': body,
                        'url': f"https://reddit.com{comment_data.get('permalink', '')}",
                        'subreddit': comment_data.get('subreddit', ''),
                        'author': comment_data.get('author', '[deleted]'),
                        'upvotes': comment_data.get('score', 0),
                        'upvote_ratio': None,
                        'comment_count': 0,
                        'created_utc': created_utc,
                        'created_date': datetime.fromtimestamp(created_utc).isoformat() if created_utc else None,
                        'is_comment': True,
                        'parent_post': post_permalink,
                    })

                # Recurse into replies
                replies = comment_data.get('replies', '')
                if replies and isinstance(replies, dict):
                    reply_children = replies.get('data', {}).get('children', [])
                    search_comments(reply_children, depth + 1)

        children = comments_data.get('data', {}).get('children', [])
        search_comments(children)

        return mentions

    def _get_google_search_queries(self, brand_name: str) -> List[str]:
        """
        Generate Google search queries for brand variations.
        Uses exact match quotes for precise results.

        e.g., "Client L" -> ['"Client L" site:reddit.com', '"Client L" site:reddit.com']
        """
        queries = set()
        brand_lower = brand_name.lower()

        # Original brand name
        queries.add(f'"{brand_name}" site:reddit.com')

        # & to and variation
        if '&' in brand_name:
            variation = brand_name.replace('&', 'and')
            queries.add(f'"{variation}" site:reddit.com')

        # and to & variation
        if ' and ' in brand_name.lower():
            variation = brand_name.replace(' and ', ' & ').replace(' And ', ' & ').replace(' AND ', ' & ')
            queries.add(f'"{variation}" site:reddit.com')

        return list(queries)

    def _get_brand_variations(self, brand_name: str) -> List[str]:
        """Generate common variations of a brand name for matching in text."""
        brand_lower = brand_name.lower()
        variations = set([
            brand_lower,
            brand_lower.replace('&', 'and'),
            brand_lower.replace(' and ', ' & '),
            brand_lower.replace('&', ' and '),
            brand_lower.replace('&', '&amp;'),  # HTML entity
            brand_lower.replace('-', ' '),
            brand_lower.replace(' ', '-'),
            brand_lower.replace('.', ''),
            brand_lower.replace(',', ''),
            # Also handle if brand has 'and' - convert to &
            brand_lower.replace(' and ', '&'),
            brand_lower.replace(' and ', '&amp;'),
        ])
        # Remove empty strings and duplicates
        return [v for v in variations if v.strip()]

    def _deduplicate(self, mentions: List[Dict]) -> List[Dict]:
        """Remove duplicate mentions by URL."""
        seen_urls = set()
        unique = []

        for mention in mentions:
            url = mention.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(mention)

        return unique

    def _filter_by_brand_mention(
        self,
        mentions: List[Dict],
        brand_name: str
    ) -> List[Dict]:
        """
        Filter mentions to only include posts that actually contain the brand name.

        Reddit search can return loosely related posts. This ensures we only
        keep posts that explicitly mention the brand.

        Args:
            mentions: List of mention dicts
            brand_name: Brand name to search for

        Returns:
            Filtered list of mentions
        """
        filtered = []
        brand_variations = self._get_brand_variations(brand_name)

        for mention in mentions:
            text = (
                mention.get('title', '') + ' ' + mention.get('body', '')
            ).lower()

            # Check if any brand variation is in the text
            if any(variation in text for variation in brand_variations):
                filtered.append(mention)

        return filtered

    def _calculate_summary(self, mentions: List[Dict]) -> Dict:
        """Calculate summary statistics for AI context."""
        if not mentions:
            return {
                'total_mentions': 0,
                'total_upvotes': 0,
                'total_comments': 0,
                'avg_upvotes': 0,
                'avg_comments': 0,
                'subreddit_distribution': {},
                'date_range': None
            }

        total_upvotes = sum(m.get('upvotes', 0) for m in mentions)
        total_comments = sum(m.get('comment_count', 0) for m in mentions)

        # Subreddit distribution
        subreddit_counts = {}
        for mention in mentions:
            sub = mention.get('subreddit', 'unknown')
            subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1

        # Sort by count
        subreddit_distribution = dict(
            sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)
        )

        # Date range
        dates = [m.get('created_utc', 0) for m in mentions if m.get('created_utc')]
        date_range = None
        if dates:
            date_range = {
                'earliest': datetime.fromtimestamp(min(dates)).isoformat(),
                'latest': datetime.fromtimestamp(max(dates)).isoformat()
            }

        return {
            'total_mentions': len(mentions),
            'total_upvotes': total_upvotes,
            'total_comments': total_comments,
            'avg_upvotes': round(total_upvotes / len(mentions), 2),
            'avg_comments': round(total_comments / len(mentions), 2),
            'total_engagement': total_upvotes + total_comments,
            'subreddit_distribution': subreddit_distribution,
            'date_range': date_range
        }

    def save_results(self, results: Dict, output_path: str) -> str:
        """
        Save results to JSON file.

        Args:
            results: Scrape results dict
            output_path: Path to save JSON file

        Returns:
            Absolute path to saved file
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return str(path.absolute())

    # ========== Subreddit Watchlist Methods ==========

    def _brand_to_slug(self, brand_name: str) -> str:
        """
        Convert brand name to a filesystem-safe slug.

        Args:
            brand_name: Brand name (e.g., "Client L")

        Returns:
            Slug (e.g., "client-l")
        """
        # Normalize unicode characters
        slug = unicodedata.normalize('NFKD', brand_name)
        # Convert to lowercase
        slug = slug.lower()
        # Replace & and 'and' with nothing (they're connectors)
        slug = slug.replace('&', '').replace(' and ', '_')
        # Replace spaces and special chars with underscores
        slug = re.sub(r'[^a-z0-9]+', '_', slug)
        # Remove leading/trailing underscores and collapse multiple
        slug = re.sub(r'_+', '_', slug).strip('_')
        return slug

    def get_watchlist_path(self, brand_name: str) -> Path:
        """Get the path to a brand's watchlist file."""
        slug = self._brand_to_slug(brand_name)
        return self.watchlist_dir / f"{slug}.json"

    def load_watchlist(self, brand_name: str) -> Dict:
        """
        Load existing watchlist for a brand.

        Args:
            brand_name: Brand name

        Returns:
            Watchlist dict with subreddits and metadata
        """
        watchlist_path = self.get_watchlist_path(brand_name)

        if watchlist_path.exists():
            with open(watchlist_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Return empty watchlist structure
        return {
            'brand': brand_name,
            'slug': self._brand_to_slug(brand_name),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'subreddits': {}  # {subreddit_name: {mention_count, last_seen, first_seen}}
        }

    def save_watchlist(self, brand_name: str, watchlist: Dict) -> str:
        """
        Save watchlist for a brand.

        Args:
            brand_name: Brand name
            watchlist: Watchlist dict

        Returns:
            Path to saved file
        """
        watchlist_path = self.get_watchlist_path(brand_name)
        watchlist['updated_at'] = datetime.now().isoformat()

        with open(watchlist_path, 'w', encoding='utf-8') as f:
            json.dump(watchlist, f, indent=2, ensure_ascii=False)

        return str(watchlist_path)

    def update_watchlist_from_results(self, brand_name: str, results: Dict) -> Dict:
        """
        Update a brand's subreddit watchlist based on scrape results.

        Automatically adds any new subreddits where brand mentions were found.

        Args:
            brand_name: Brand name
            results: Scrape results from scrape_brand_mentions()

        Returns:
            Updated watchlist dict
        """
        watchlist = self.load_watchlist(brand_name)
        now = datetime.now().isoformat()

        # Extract subreddit distribution from results
        subreddit_counts = results.get('summary', {}).get('subreddit_distribution', {})

        new_subreddits = []
        updated_subreddits = []

        for subreddit, count in subreddit_counts.items():
            if subreddit in watchlist['subreddits']:
                # Update existing
                watchlist['subreddits'][subreddit]['mention_count'] += count
                watchlist['subreddits'][subreddit]['last_seen'] = now
                updated_subreddits.append(subreddit)
            else:
                # Add new subreddit to watchlist
                watchlist['subreddits'][subreddit] = {
                    'mention_count': count,
                    'first_seen': now,
                    'last_seen': now,
                    'added_automatically': True
                }
                new_subreddits.append(subreddit)

        # Save the updated watchlist
        self.save_watchlist(brand_name, watchlist)

        # Log what changed
        if new_subreddits:
            print(f"\n[Watchlist] Updated for '{brand_name}':")
            print(f"   New subreddits added: {', '.join(new_subreddits)}")
        if updated_subreddits:
            print(f"   Existing subreddits updated: {len(updated_subreddits)}")
        print(f"   Total subreddits in watchlist: {len(watchlist['subreddits'])}")
        print(f"   Watchlist saved to: {self.get_watchlist_path(brand_name)}")

        return watchlist

    def get_watchlist_subreddits(self, brand_name: str) -> List[str]:
        """
        Get list of subreddit names from a brand's watchlist.

        Useful for MCP server monitoring - returns subreddits sorted by mention count.

        Args:
            brand_name: Brand name

        Returns:
            List of subreddit names, sorted by mention count (highest first)
        """
        watchlist = self.load_watchlist(brand_name)
        subreddits = watchlist.get('subreddits', {})

        # Sort by mention count descending
        sorted_subs = sorted(
            subreddits.items(),
            key=lambda x: x[1].get('mention_count', 0),
            reverse=True
        )

        return [sub[0] for sub in sorted_subs]

    def add_subreddit_to_watchlist(self, brand_name: str, subreddit: str, notes: str = None) -> Dict:
        """
        Manually add a subreddit to a brand's watchlist.

        Args:
            brand_name: Brand name
            subreddit: Subreddit name (without r/)
            notes: Optional notes about why this subreddit was added

        Returns:
            Updated watchlist
        """
        watchlist = self.load_watchlist(brand_name)
        now = datetime.now().isoformat()

        if subreddit not in watchlist['subreddits']:
            watchlist['subreddits'][subreddit] = {
                'mention_count': 0,
                'first_seen': now,
                'last_seen': now,
                'added_automatically': False,
                'notes': notes
            }
            self.save_watchlist(brand_name, watchlist)
            print(f"Added r/{subreddit} to watchlist for '{brand_name}'")
        else:
            print(f"r/{subreddit} already in watchlist for '{brand_name}'")

        return watchlist

    def remove_subreddit_from_watchlist(self, brand_name: str, subreddit: str) -> Dict:
        """
        Remove a subreddit from a brand's watchlist.

        Args:
            brand_name: Brand name
            subreddit: Subreddit name to remove

        Returns:
            Updated watchlist
        """
        watchlist = self.load_watchlist(brand_name)

        if subreddit in watchlist['subreddits']:
            del watchlist['subreddits'][subreddit]
            self.save_watchlist(brand_name, watchlist)
            print(f"Removed r/{subreddit} from watchlist for '{brand_name}'")
        else:
            print(f"r/{subreddit} not in watchlist for '{brand_name}'")

        return watchlist


def load_subreddits_config(config_path: str = None) -> Dict:
    """Load subreddit configuration from JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / 'config' / 'subreddits.json'

    with open(config_path, 'r') as f:
        return json.load(f)


def get_subreddits_for_industry(industry: str, config: Dict = None) -> List[str]:
    """
    Get list of subreddits for a given industry.

    Args:
        industry: Industry key (e.g., 'saas', 'ecommerce', 'healthcare')
        config: Optional subreddits config dict (loads from file if not provided)

    Returns:
        List of subreddit names
    """
    if config is None:
        config = load_subreddits_config()

    # Check industries first
    if industry in config.get('industries', {}):
        return config['industries'][industry]

    # Check size-based
    if industry in config.get('size_based', {}):
        return config['size_based'][industry]

    # Check b2b/b2c
    if industry == 'b2b':
        return config.get('b2b', [])
    if industry == 'b2c':
        return config.get('b2c', [])

    # Check location-based
    if industry in config.get('location_based', {}):
        return config['location_based'][industry]

    # Fall back to default
    return config.get('default', ['smallbusiness', 'Entrepreneur', 'business'])
