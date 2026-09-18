#!/usr/bin/env python3
"""
Unified Brand Visibility Scraper CLI
Scrapes brand mentions and engagement across multiple platforms:
- Reddit (mentions via Google search + .json endpoints)
- Facebook (like counts via DataForSEO)
- Pinterest (pin counts via DataForSEO)
- Google Reviews (reviews and ratings via DataForSEO)

Each platform's data is saved to separate JSON files.

Usage:
    python scrape_brand_visibility.py --brand "BrandName" --domain "example.com"
    python scrape_brand_visibility.py --brand "BrandName" --domain "example.com" --platforms reddit,facebook,google_reviews
    python scrape_brand_visibility.py --brand "BrandName" --domain "example.com" --reddit-only
"""

import os
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.reddit_visibility_scraper import RedditVisibilityScraper
from src.scrapers.social_media_scraper import SocialMediaScraper, discover_brand_urls
from src.scrapers.google_reviews_scraper import GoogleReviewsScraper


# Default DataForSEO credentials
DEFAULT_DATAFORSEO_LOGIN = os.environ.get("DATAFORSEO_LOGIN")
DEFAULT_DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD")


def main():
    parser = argparse.ArgumentParser(
        description='Unified brand visibility scraper - Reddit, Facebook, Pinterest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --brand "Client L" --domain "clientl.example.com"
  %(prog)s --brand "Client L" --domain "clientl.example.com" --platforms reddit,facebook,google_reviews
  %(prog)s --brand "Client L" --reddit-only
  %(prog)s --brand "Client L" --social-only --urls "https://example.com"
  %(prog)s --brand "Client L" --reviews-only --review-queries "Client L Sydney"

Platform options:
  reddit         - Search Reddit for brand mentions (via Google + .json endpoints)
  facebook       - Get Facebook like counts for brand URLs
  pinterest      - Get Pinterest pin counts for brand URLs
  google_reviews - Get Google Business reviews and ratings

Output:
  Separate JSON files for each platform in the reports/ directory.
        """
    )

    parser.add_argument(
        '--brand', '-b',
        required=True,
        help='Brand name to search for'
    )

    parser.add_argument(
        '--domain', '-d',
        help='Brand domain for social media URL checks (e.g., clientl.example.com)'
    )

    parser.add_argument(
        '--urls', '-u',
        help='Comma-separated list of URLs for social media checks'
    )

    parser.add_argument(
        '--platforms', '-p',
        default='reddit,facebook,pinterest,google_reviews',
        help='Platforms to check (default: reddit,facebook,pinterest,google_reviews)'
    )

    parser.add_argument(
        '--reddit-only',
        action='store_true',
        help='Only scrape Reddit'
    )

    parser.add_argument(
        '--social-only',
        action='store_true',
        help='Only scrape social media (Facebook, Pinterest)'
    )

    parser.add_argument(
        '--reviews-only',
        action='store_true',
        help='Only scrape Google Reviews'
    )

    parser.add_argument(
        '--review-queries',
        help='Comma-separated search queries for Google Reviews (e.g., "Brand Sydney,Brand Melbourne")'
    )

    parser.add_argument(
        '--review-location',
        default='Sydney,New South Wales,Australia',
        help='Location in "City,State,Country" format (default: Sydney,New South Wales,Australia)'
    )

    parser.add_argument(
        '--review-depth',
        type=int,
        default=100,
        help='Number of reviews to fetch per location (default: 100)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=180,
        help='Days back to search for Reddit mentions (default: 180)'
    )

    parser.add_argument(
        '--industry', '-i',
        help='Industry for Reddit subreddit selection'
    )

    args = parser.parse_args()

    # Determine platforms
    if args.reddit_only:
        platforms = ['reddit']
    elif args.social_only:
        platforms = ['facebook', 'pinterest']
    elif args.reviews_only:
        platforms = ['google_reviews']
    else:
        platforms = [p.strip().lower() for p in args.platforms.split(',')]

    # Validate platform requirements
    social_platforms = [p for p in platforms if p in ['facebook', 'pinterest']]
    if social_platforms and not args.domain and not args.urls:
        print("Error: --domain or --urls required for Facebook/Pinterest checks")
        sys.exit(1)

    # Print header
    print("\n" + "=" * 60)
    print("UNIFIED BRAND VISIBILITY SCRAPER")
    print("=" * 60)
    print(f"Brand: {args.brand}")
    print(f"Platforms: {', '.join(platforms)}")
    if args.domain:
        print(f"Domain: {args.domain}")
    print(f"Reddit days back: {args.days}")
    print("=" * 60)

    all_results = {
        'brand': args.brand,
        'scraped_at': datetime.now().isoformat(),
        'platforms_scraped': [],
        'files_saved': {}
    }

    # ========== REDDIT ==========
    if 'reddit' in platforms:
        print("\n" + "-" * 60)
        print("REDDIT MENTIONS")
        print("-" * 60)

        reddit_scraper = RedditVisibilityScraper(
            dataforseo_login=DEFAULT_DATAFORSEO_LOGIN,
            dataforseo_password=DEFAULT_DATAFORSEO_PASSWORD
        )

        # Get subreddits
        if args.industry:
            from src.scrapers.reddit_visibility_scraper import get_subreddits_for_industry
            subreddits = get_subreddits_for_industry(args.industry)
        else:
            subreddits = ['smallbusiness', 'Entrepreneur', 'business', 'marketing', 'startups']

        # Run Reddit scrape
        reddit_results = reddit_scraper.scrape_brand_mentions(
            brand_name=args.brand,
            subreddits=subreddits,
            days_back=args.days,
            use_google_search=True
        )

        # Save Reddit results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_brand = args.brand.replace(' ', '_').lower()
        reddit_path = f"reports/reddit_{safe_brand}_{timestamp}.json"
        reddit_saved = reddit_scraper.save_results(reddit_results, reddit_path)

        # Update watchlist
        reddit_scraper.update_watchlist_from_results(args.brand, reddit_results)

        all_results['files_saved']['reddit'] = reddit_saved
        all_results['platforms_scraped'].append('reddit')

        # Print Reddit summary
        summary = reddit_results.get('summary', {})
        print(f"\nReddit Results:")
        print(f"  Total mentions: {summary.get('total_mentions', 0)}")
        print(f"  Total upvotes: {summary.get('total_upvotes', 0)}")
        print(f"  Total engagement: {summary.get('total_engagement', 0)}")
        print(f"  Saved to: {reddit_saved}")

    # ========== SOCIAL MEDIA (Facebook, Pinterest) ==========
    if social_platforms:
        print("\n" + "-" * 60)
        print("SOCIAL MEDIA ENGAGEMENT")
        print("-" * 60)

        social_scraper = SocialMediaScraper(
            dataforseo_login=DEFAULT_DATAFORSEO_LOGIN,
            dataforseo_password=DEFAULT_DATAFORSEO_PASSWORD
        )

        # Get URLs
        urls = []
        if args.urls:
            urls = [u.strip() for u in args.urls.split(',') if u.strip()]
        if args.domain:
            domain_urls = discover_brand_urls(
                args.domain,
                DEFAULT_DATAFORSEO_LOGIN,
                DEFAULT_DATAFORSEO_PASSWORD
            )
            urls.extend(domain_urls)

        # Deduplicate
        urls = list(dict.fromkeys(urls))

        # Run social scrape
        social_results = social_scraper.scrape_brand_social_metrics(
            brand_name=args.brand,
            urls=urls,
            platforms=social_platforms
        )

        # Save social results
        saved_files = social_scraper.save_results(social_results, args.brand)

        for platform, filepath in saved_files.items():
            all_results['files_saved'][platform] = filepath
            if platform != 'combined':
                all_results['platforms_scraped'].append(platform)

        # Print social summary
        summary = social_results.get('summary', {})
        print(f"\nSocial Media Results:")
        if 'facebook' in social_platforms:
            print(f"  Facebook likes: {summary.get('total_facebook_likes', 0):,}")
        if 'pinterest' in social_platforms:
            print(f"  Pinterest pins: {summary.get('total_pinterest_pins', 0):,}")
        print(f"  Total social engagement: {summary.get('total_social_engagement', 0):,}")

    # ========== GOOGLE REVIEWS ==========
    if 'google_reviews' in platforms:
        print("\n" + "-" * 60)
        print("GOOGLE REVIEWS")
        print("-" * 60)

        reviews_scraper = GoogleReviewsScraper(
            dataforseo_login=DEFAULT_DATAFORSEO_LOGIN,
            dataforseo_password=DEFAULT_DATAFORSEO_PASSWORD
        )

        # Determine search queries
        review_queries = None
        if args.review_queries:
            review_queries = [q.strip() for q in args.review_queries.split(',') if q.strip()]

        # Run reviews scrape
        reviews_results = reviews_scraper.scrape_brand_reviews(
            brand_name=args.brand,
            search_queries=review_queries,
            location_name=args.review_location,
            reviews_per_location=args.review_depth,
            sort_by='newest'
        )

        # Save reviews results
        reviews_saved = reviews_scraper.save_results(reviews_results, args.brand)
        all_results['files_saved']['google_reviews'] = reviews_saved
        all_results['platforms_scraped'].append('google_reviews')

        # Print reviews summary
        summary = reviews_results.get('summary', {})
        print(f"\nGoogle Reviews Results:")
        print(f"  Total reviews fetched: {summary.get('total_reviews', 0)}")
        print(f"  Average rating: {summary.get('overall_average_rating', 'N/A')}")
        print(f"  Reviews with text: {summary.get('reviews_with_text', 0)}")
        print(f"  Reviews with owner response: {summary.get('reviews_with_owner_response', 0)}")
        print(f"  Saved to: {reviews_saved}")

    # ========== FINAL SUMMARY ==========
    print("\n" + "=" * 60)
    print("SCRAPE COMPLETE")
    print("=" * 60)
    print(f"Brand: {args.brand}")
    print(f"Platforms scraped: {', '.join(all_results['platforms_scraped'])}")
    print(f"\nFiles saved:")
    for platform, filepath in all_results['files_saved'].items():
        print(f"  [{platform}] {filepath}")

    print("\nAll JSON files are ready for AI analysis.")
    print("Each platform's data is in a separate file for independent processing.")


if __name__ == '__main__':
    main()
