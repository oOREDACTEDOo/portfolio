#!/usr/bin/env python3
"""
Google Reviews Scraper CLI
Fetches Google Business reviews and ratings via DataForSEO.

Usage:
    python scrape_google_reviews.py --brand "BrandName"
    python scrape_google_reviews.py --brand "BrandName" --queries "Brand Sydney,Brand Melbourne"
    python scrape_google_reviews.py --brand "BrandName" --location "Sydney, Australia" --depth 50
"""

import os
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.google_reviews_scraper import GoogleReviewsScraper


# Default DataForSEO credentials
DEFAULT_DATAFORSEO_LOGIN = os.environ.get("DATAFORSEO_LOGIN")
DEFAULT_DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape Google Reviews for brand sentiment analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --brand "Client L"
  %(prog)s --brand "Client L" --queries "Client L Sydney,Client L Melbourne"
  %(prog)s --brand "Client L" --location "Sydney, Australia" --depth 50
  %(prog)s --brand "Client L" --search "Client L wallpaper store"

Output:
  JSON file with reviews, ratings, and business info in reports/google_reviews/
  Optimized for AI sentiment analysis.

Sort options:
  newest         - Most recent reviews first (default)
  highest_rating - Highest rated reviews first
  lowest_rating  - Lowest rated reviews first
  most_relevant  - Google's relevance ranking
        """
    )

    parser.add_argument(
        '--brand', '-b',
        required=True,
        help='Brand name (for reporting and default search)'
    )

    parser.add_argument(
        '--queries', '-q',
        help='Comma-separated search queries (e.g., "Brand Sydney,Brand Melbourne")'
    )

    parser.add_argument(
        '--search', '-s',
        help='Single search query (alternative to --queries)'
    )

    parser.add_argument(
        '--location', '-l',
        default='Sydney,New South Wales,Australia',
        help='Location in "City,State,Country" format (default: Sydney,New South Wales,Australia)'
    )

    parser.add_argument(
        '--depth', '-d',
        type=int,
        default=100,
        help='Number of reviews to fetch per location (default: 100)'
    )

    parser.add_argument(
        '--sort',
        choices=['newest', 'highest_rating', 'lowest_rating', 'most_relevant'],
        default='newest',
        help='Sort order for reviews (default: newest)'
    )

    parser.add_argument(
        '--find-business',
        action='store_true',
        help='Only search for business, do not fetch reviews'
    )

    args = parser.parse_args()

    # Determine search queries
    queries = []
    if args.queries:
        queries = [q.strip() for q in args.queries.split(',') if q.strip()]
    elif args.search:
        queries = [args.search]
    else:
        queries = [args.brand]

    # Print header
    print("\n" + "=" * 60)
    print("GOOGLE REVIEWS SCRAPER")
    print("=" * 60)
    print(f"Brand: {args.brand}")
    print(f"Search queries: {', '.join(queries)}")
    print(f"Location: {args.location}")
    print(f"Reviews per location: {args.depth}")
    print(f"Sort by: {args.sort}")
    print("=" * 60)

    # Initialize scraper
    scraper = GoogleReviewsScraper(
        dataforseo_login=DEFAULT_DATAFORSEO_LOGIN,
        dataforseo_password=DEFAULT_DATAFORSEO_PASSWORD
    )

    # Business search only mode
    if args.find_business:
        print("\n[Business Search Mode]")
        for query in queries:
            print(f"\nSearching: '{query}'")
            results = scraper.search_business(
                keyword=query,
                location_name=args.location
            )

            if results.get('results'):
                print(f"Found {len(results['results'])} businesses:\n")
                for i, biz in enumerate(results['results'][:5], 1):
                    print(f"  {i}. {biz['title']}")
                    print(f"     Rating: {biz['rating']} ({biz['review_count']} reviews)")
                    print(f"     Address: {biz['address']}")
                    print(f"     Place ID: {biz['place_id']}")
                    print(f"     Category: {biz['category']}")
                    print()
            else:
                print("  No businesses found")
        return

    # Full review scrape
    results = scraper.scrape_brand_reviews(
        brand_name=args.brand,
        search_queries=queries,
        location_name=args.location,
        reviews_per_location=args.depth,
        sort_by=args.sort
    )

    # Save results
    saved_path = scraper.save_results(results, args.brand)

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    summary = results.get('summary', {})
    print(f"\nTotal locations searched: {summary.get('total_locations', 0)}")
    print(f"Total reviews fetched: {summary.get('total_reviews', 0)}")
    print(f"Overall average rating: {summary.get('overall_average_rating', 'N/A')}")

    rating_dist = summary.get('rating_distribution', {})
    if rating_dist:
        print(f"\nRating distribution:")
        for stars in ['5_star', '4_star', '3_star', '2_star', '1_star']:
            count = rating_dist.get(stars, 0)
            bar = '*' * min(count, 50)
            print(f"  {stars.replace('_', ' ')}: {count:4} {bar}")

    print(f"\nReviews with text: {summary.get('reviews_with_text', 0)}")
    print(f"Reviews with owner response: {summary.get('reviews_with_owner_response', 0)}")

    # Show location breakdown
    if results.get('locations'):
        print(f"\n" + "-" * 40)
        print("LOCATIONS BREAKDOWN")
        print("-" * 40)
        for loc in results['locations']:
            biz = loc.get('business', {})
            loc_summary = loc.get('summary', {})
            print(f"\n  [{loc['query']}]")
            print(f"  Business: {biz.get('title', 'N/A')}")
            print(f"  Rating: {biz.get('rating', 'N/A')} ({biz.get('total_reviews', 0)} total reviews)")
            print(f"  Fetched: {loc_summary.get('total_reviews_fetched', 0)} reviews")

    print(f"\n" + "=" * 60)
    print("FILE SAVED")
    print("=" * 60)
    print(f"  {saved_path}")

    print("\nThis JSON file is ready for AI sentiment analysis.")
    print("Use the 'all_reviews' array for batch processing.")


if __name__ == '__main__':
    main()
