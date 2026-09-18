#!/usr/bin/env python3
"""
Reddit Brand Visibility Scraper CLI
Scrapes Reddit for brand mentions and outputs AI-ready JSON

NO API CREDENTIALS REQUIRED for basic usage
OPTIONAL: DataForSEO credentials enable Google search for additional Reddit posts

Usage:
    python scrape_reddit_visibility.py --brand "BrandName"
    python scrape_reddit_visibility.py --brand "BrandName" --industry saas
    python scrape_reddit_visibility.py --brand "BrandName" --google
"""

import os
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.reddit_visibility_scraper import (
    RedditVisibilityScraper,
    get_subreddits_for_industry,
    load_subreddits_config
)


def main():
    parser = argparse.ArgumentParser(
        description='Scrape Reddit for brand mentions (AI visibility analysis)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --brand "Acme Corp"
  %(prog)s --brand "Acme Corp" --industry saas
  %(prog)s --brand "Acme Corp" --subreddits "startups,saas,marketing"
  %(prog)s --brand "Acme Corp" --google
  %(prog)s --brand "Acme Corp" --days 90 --output results.json

Industries available:
  saas, ecommerce, healthcare, finance, technology, retail,
  food_beverage, travel_hospitality, education, manufacturing,
  consulting, marketing_advertising, legal, automotive,
  fitness_wellness, beauty_cosmetics, pet_care, home_improvement,
  office_supplies, real_estate

Size-based:
  enterprise, smb, startup

Business model:
  b2b, b2c

Location:
  us, uk, australia, canada

Google Search (--google flag):
  Requires DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD in .env file.
  Searches Google for "brand site:reddit.com" to find additional posts
  that Reddit's own search might miss.
        """
    )

    parser.add_argument(
        '--brand', '-b',
        required=True,
        help='Brand name to search for (required)'
    )

    parser.add_argument(
        '--subreddits', '-s',
        help='Comma-separated list of subreddits to search'
    )

    parser.add_argument(
        '--industry', '-i',
        help='Industry for auto subreddit selection (see --help for options)'
    )

    parser.add_argument(
        '--days', '-d',
        type=int,
        default=180,
        help='Days back to search (default: 180)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: reports/reddit_{brand}_{date}.json)'
    )

    parser.add_argument(
        '--google', '-g',
        action='store_true',
        help='Also search Google for Reddit posts (requires DataForSEO credentials)'
    )

    parser.add_argument(
        '--comments', '-c',
        action='store_true',
        help='Also search comments (slower, but finds more mentions)'
    )

    parser.add_argument(
        '--list-industries',
        action='store_true',
        help='List all available industries and exit'
    )

    args = parser.parse_args()

    # Handle --list-industries
    if args.list_industries:
        try:
            subreddit_config = load_subreddits_config()
            print("\nAvailable industries:")
            for industry in subreddit_config.get('industries', {}).keys():
                print(f"  - {industry}")
            print("\nSize-based options:")
            for size in subreddit_config.get('size_based', {}).keys():
                print(f"  - {size}")
            print("\nBusiness model: b2b, b2c")
            print("\nLocations:")
            for loc in subreddit_config.get('location_based', {}).keys():
                print(f"  - {loc}")
        except Exception as e:
            print(f"Error loading config: {e}")
        return

    # Determine subreddits to search
    if args.subreddits:
        subreddits = [s.strip() for s in args.subreddits.split(',')]
    elif args.industry:
        try:
            subreddits = get_subreddits_for_industry(args.industry)
            if not subreddits:
                print(f"Warning: Unknown industry '{args.industry}', using defaults")
                subreddits = ['smallbusiness', 'Entrepreneur', 'business', 'marketing', 'startups']
        except Exception:
            subreddits = ['smallbusiness', 'Entrepreneur', 'business', 'marketing', 'startups']
    else:
        # Default subreddits
        subreddits = ['smallbusiness', 'Entrepreneur', 'business', 'marketing', 'startups']

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_brand = args.brand.replace(' ', '_').lower()
        output_path = f"reports/reddit_{safe_brand}_{timestamp}.json"

    # Load DataForSEO credentials if Google search requested
    # Default credentials (same as dataforseo_query.py)
    DEFAULT_DATAFORSEO_LOGIN = os.environ.get("DATAFORSEO_LOGIN")
    DEFAULT_DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD")

    dataforseo_login = None
    dataforseo_password = None

    if args.google:
        import os
        # Try environment variables first, fall back to defaults
        dataforseo_login = os.environ.get("DATAFORSEO_LOGIN") or DEFAULT_DATAFORSEO_LOGIN
        dataforseo_password = os.environ.get("DATAFORSEO_PASSWORD") or DEFAULT_DATAFORSEO_PASSWORD

        if dataforseo_login and dataforseo_password:
            print(f"\nUsing DataForSEO credentials for Google search")
        else:
            print("\nWarning: DataForSEO credentials not available. Skipping Google search.\n")

    # Print header
    print("\n" + "=" * 50)
    print("Reddit Visibility Scraper")
    print("=" * 50)
    print(f"Brand: {args.brand}")
    print(f"Subreddits: {', '.join(subreddits)}")
    print(f"Days back: {args.days}")
    print(f"Include comments: {'Yes' if args.comments else 'No'}")
    print(f"Google search: {'Yes' if args.google and dataforseo_login else 'No'}")
    print(f"Output: {output_path}")
    print("=" * 50)

    # Initialize scraper
    scraper = RedditVisibilityScraper(
        dataforseo_login=dataforseo_login,
        dataforseo_password=dataforseo_password
    )

    # Run scrape
    results = scraper.scrape_brand_mentions(
        brand_name=args.brand,
        subreddits=subreddits,
        days_back=args.days,
        include_comments=args.comments,
        use_google_search=args.google
    )

    # Save results
    saved_path = scraper.save_results(results, output_path)

    # Update watchlist with discovered subreddits (for MCP monitoring)
    watchlist = scraper.update_watchlist_from_results(args.brand, results)

    # Print summary
    summary = results.get('summary', {})
    metadata = results.get('metadata', {})

    print("\n" + "=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total mentions found: {summary.get('total_mentions', 0)}")
    print(f"Total upvotes: {summary.get('total_upvotes', 0)}")
    print(f"Total comments: {summary.get('total_comments', 0)}")
    print(f"Average upvotes: {summary.get('avg_upvotes', 0)}")
    print(f"Total engagement: {summary.get('total_engagement', 0)}")

    if metadata.get('sources_used'):
        print(f"\nData sources used: {', '.join(metadata['sources_used'])}")

    if summary.get('subreddit_distribution'):
        print("\nMentions by subreddit:")
        for sub, count in list(summary['subreddit_distribution'].items())[:5]:
            print(f"  r/{sub}: {count}")

    if summary.get('date_range'):
        print(f"\nDate range:")
        print(f"  Earliest: {summary['date_range']['earliest']}")
        print(f"  Latest: {summary['date_range']['latest']}")

    # Check for errors
    errors = metadata.get('errors')
    if errors:
        print(f"\nWarnings ({len(errors)} subreddits had issues):")
        for err in errors[:3]:
            print(f"  r/{err['subreddit']}: {err['error']}")

    print(f"\nResults saved to: {saved_path}")

    # Show watchlist info for MCP monitoring
    watchlist_subs = scraper.get_watchlist_subreddits(args.brand)
    if watchlist_subs:
        print(f"\n" + "=" * 50)
        print("MCP MONITORING WATCHLIST")
        print("=" * 50)
        print(f"Subreddits to monitor for '{args.brand}':")
        for sub in watchlist_subs[:10]:  # Show top 10
            count = watchlist['subreddits'].get(sub, {}).get('mention_count', 0)
            print(f"  r/{sub} ({count} mentions)")
        if len(watchlist_subs) > 10:
            print(f"  ... and {len(watchlist_subs) - 10} more")
        print(f"\nWatchlist file: {scraper.get_watchlist_path(args.brand)}")

    print("\nThis JSON file is ready for AI sentiment/visibility analysis.")


if __name__ == '__main__':
    main()
