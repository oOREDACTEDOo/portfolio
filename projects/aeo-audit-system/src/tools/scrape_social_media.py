#!/usr/bin/env python3
"""
Social Media Engagement Scraper CLI
Fetches Facebook likes and Pinterest pins for brand URLs via DataForSEO.

Usage:
    python scrape_social_media.py --brand "BrandName" --urls "https://example.com,https://example.com/products"
    python scrape_social_media.py --brand "BrandName" --domain "example.com"
    python scrape_social_media.py --brand "BrandName" --urls-file urls.txt
"""

import os
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.social_media_scraper import SocialMediaScraper, discover_brand_urls


# Default DataForSEO credentials
DEFAULT_DATAFORSEO_LOGIN = os.environ.get("DATAFORSEO_LOGIN")
DEFAULT_DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape social media engagement metrics for brand URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --brand "Client L" --urls "https://clientl.example.com,https://clientl.example.com/collections"
  %(prog)s --brand "Client L" --domain "clientl.example.com"
  %(prog)s --brand "Client L" --urls-file brand_urls.txt
  %(prog)s --brand "Client L" --urls "https://clientl.example.com" --platforms facebook

Platforms available:
  facebook  - Get Facebook Like button counts for URLs
  pinterest - Get Pinterest Pin/Save counts for URLs

Note: This checks how often brand URLs are liked/pinned on social platforms,
not mentions of the brand within social media posts.
        """
    )

    parser.add_argument(
        '--brand', '-b',
        required=True,
        help='Brand name (for reporting)'
    )

    parser.add_argument(
        '--urls', '-u',
        help='Comma-separated list of URLs to check'
    )

    parser.add_argument(
        '--domain', '-d',
        help='Brand domain - will auto-discover common URL patterns'
    )

    parser.add_argument(
        '--urls-file', '-f',
        help='File containing URLs (one per line)'
    )

    parser.add_argument(
        '--platforms', '-p',
        default='facebook,pinterest',
        help='Comma-separated platforms to check (default: facebook,pinterest)'
    )

    args = parser.parse_args()

    # Determine URLs to check
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

    if args.urls_file:
        try:
            with open(args.urls_file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                urls.extend(file_urls)
        except FileNotFoundError:
            print(f"Error: URLs file not found: {args.urls_file}")
            sys.exit(1)

    if not urls:
        print("Error: No URLs specified. Use --urls, --domain, or --urls-file")
        sys.exit(1)

    # Deduplicate URLs
    urls = list(dict.fromkeys(urls))

    # Parse platforms
    platforms = [p.strip().lower() for p in args.platforms.split(',')]
    valid_platforms = ['facebook', 'pinterest']
    platforms = [p for p in platforms if p in valid_platforms]

    if not platforms:
        print(f"Error: No valid platforms specified. Choose from: {', '.join(valid_platforms)}")
        sys.exit(1)

    # Print header
    print("\n" + "=" * 50)
    print("Social Media Engagement Scraper")
    print("=" * 50)
    print(f"Brand: {args.brand}")
    print(f"URLs to check: {len(urls)}")
    print(f"Platforms: {', '.join(platforms)}")
    print("=" * 50)

    # Initialize scraper
    scraper = SocialMediaScraper(
        dataforseo_login=DEFAULT_DATAFORSEO_LOGIN,
        dataforseo_password=DEFAULT_DATAFORSEO_PASSWORD
    )

    # Run scrape
    results = scraper.scrape_brand_social_metrics(
        brand_name=args.brand,
        urls=urls,
        platforms=platforms
    )

    # Save results
    saved_files = scraper.save_results(results, args.brand)

    # Print summary
    print("\n" + "=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)

    summary = results.get('summary', {})

    if 'facebook' in platforms and results.get('facebook'):
        print(f"\n[Facebook]")
        print(f"  Total likes: {summary.get('total_facebook_likes', 0)}")
        fb_urls = results['facebook'].get('urls', [])
        if fb_urls:
            # Sort by likes descending
            fb_urls_sorted = sorted(fb_urls, key=lambda x: x.get('like_count', 0), reverse=True)
            print(f"  Top URLs by likes:")
            for item in fb_urls_sorted[:5]:
                print(f"    {item['like_count']:,} likes - {item['url'][:60]}...")

    if 'pinterest' in platforms and results.get('pinterest'):
        print(f"\n[Pinterest]")
        print(f"  Total pins: {summary.get('total_pinterest_pins', 0)}")
        pin_urls = results['pinterest'].get('urls', [])
        if pin_urls:
            # Sort by pins descending
            pin_urls_sorted = sorted(pin_urls, key=lambda x: x.get('pins_count', 0), reverse=True)
            print(f"  Top URLs by pins:")
            for item in pin_urls_sorted[:5]:
                print(f"    {item['pins_count']:,} pins - {item['url'][:60]}...")

    print(f"\nTotal social engagement: {summary.get('total_social_engagement', 0):,}")

    print(f"\n" + "=" * 50)
    print("FILES SAVED")
    print("=" * 50)
    for platform, filepath in saved_files.items():
        print(f"  {platform}: {filepath}")

    print("\nThese JSON files are ready for AI analysis.")


if __name__ == '__main__':
    main()
