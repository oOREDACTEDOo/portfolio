#!/usr/bin/env python3
"""
Reddit Watchlist Manager CLI
Manages subreddit watchlists for brand monitoring via MCP server.

Usage:
    python reddit_watchlist.py --brand "Brand Name" --list
    python reddit_watchlist.py --brand "Brand Name" --add "wallpaper,HomeDecorating"
    python reddit_watchlist.py --brand "Brand Name" --remove "subreddit"
    python reddit_watchlist.py --list-all
"""

import argparse
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.reddit_visibility_scraper import RedditVisibilityScraper


def main():
    parser = argparse.ArgumentParser(
        description='Manage Reddit subreddit watchlists for MCP monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --brand "Client L" --list
  %(prog)s --brand "Client L" --add "wallpaper,InteriorDesign"
  %(prog)s --brand "Client L" --remove "wallpaper"
  %(prog)s --list-all
  %(prog)s --brand "Client L" --export

MCP Server Usage:
  Once you have a watchlist, use the MCP server to monitor these subreddits:

  1. The watchlist file is saved in data/watchlists/{brand_slug}.json
  2. Use the MCP's get_subreddit_new_posts tool with subreddits from the watchlist
  3. Example: "Check r/wallpaper for new posts" (MCP handles this)
        """
    )

    parser.add_argument(
        '--brand', '-b',
        help='Brand name to manage watchlist for'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all subreddits in the watchlist'
    )

    parser.add_argument(
        '--add', '-a',
        help='Add subreddits to watchlist (comma-separated)'
    )

    parser.add_argument(
        '--remove', '-r',
        help='Remove subreddits from watchlist (comma-separated)'
    )

    parser.add_argument(
        '--list-all',
        action='store_true',
        help='List all brand watchlists'
    )

    parser.add_argument(
        '--export',
        action='store_true',
        help='Export watchlist subreddits as comma-separated list (for scripts)'
    )

    parser.add_argument(
        '--notes',
        help='Notes to add when adding a subreddit manually'
    )

    args = parser.parse_args()

    scraper = RedditVisibilityScraper()

    # List all watchlists
    if args.list_all:
        watchlist_dir = scraper.watchlist_dir
        if watchlist_dir.exists():
            watchlists = list(watchlist_dir.glob('*.json'))
            if watchlists:
                print("\nExisting brand watchlists:")
                print("=" * 50)
                for wl_path in watchlists:
                    with open(wl_path, 'r') as f:
                        wl = json.load(f)
                    brand = wl.get('brand', wl_path.stem)
                    sub_count = len(wl.get('subreddits', {}))
                    updated = wl.get('updated_at', 'unknown')[:10]
                    print(f"  {brand}")
                    print(f"    Subreddits: {sub_count}")
                    print(f"    Last updated: {updated}")
                    print(f"    File: {wl_path.name}")
                    print()
            else:
                print("\nNo watchlists found. Run the scraper to create one.")
        else:
            print("\nNo watchlist directory found. Run the scraper to create one.")
        return

    # All other commands require --brand
    if not args.brand:
        parser.error("--brand is required for this operation")

    # List subreddits in watchlist
    if args.list:
        watchlist = scraper.load_watchlist(args.brand)
        subreddits = watchlist.get('subreddits', {})

        if subreddits:
            print(f"\nWatchlist for '{args.brand}':")
            print("=" * 50)
            print(f"Created: {watchlist.get('created_at', 'unknown')[:10]}")
            print(f"Updated: {watchlist.get('updated_at', 'unknown')[:10]}")
            print(f"Total subreddits: {len(subreddits)}")
            print("\nSubreddits (sorted by mention count):")
            print("-" * 50)

            # Sort by mention count
            sorted_subs = sorted(
                subreddits.items(),
                key=lambda x: x[1].get('mention_count', 0),
                reverse=True
            )

            for sub, info in sorted_subs:
                count = info.get('mention_count', 0)
                auto = "auto" if info.get('added_automatically') else "manual"
                first_seen = info.get('first_seen', '')[:10]
                notes = info.get('notes', '')

                print(f"  r/{sub}")
                print(f"    Mentions: {count} | Added: {auto} | First seen: {first_seen}")
                if notes:
                    print(f"    Notes: {notes}")
        else:
            print(f"\nNo watchlist found for '{args.brand}'.")
            print("Run the scraper with --google flag to discover subreddits:")
            print(f'  python scrape_reddit_visibility.py --brand "{args.brand}" --google')
        return

    # Export as comma-separated list
    if args.export:
        subreddits = scraper.get_watchlist_subreddits(args.brand)
        if subreddits:
            print(','.join(subreddits))
        else:
            print("# No subreddits in watchlist", file=sys.stderr)
        return

    # Add subreddits
    if args.add:
        subs_to_add = [s.strip() for s in args.add.split(',')]
        print(f"\nAdding subreddits to '{args.brand}' watchlist:")
        for sub in subs_to_add:
            scraper.add_subreddit_to_watchlist(args.brand, sub, notes=args.notes)
        return

    # Remove subreddits
    if args.remove:
        subs_to_remove = [s.strip() for s in args.remove.split(',')]
        print(f"\nRemoving subreddits from '{args.brand}' watchlist:")
        for sub in subs_to_remove:
            scraper.remove_subreddit_from_watchlist(args.brand, sub)
        return

    # Default: show help
    parser.print_help()


if __name__ == '__main__':
    main()
