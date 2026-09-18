"""
DataForSEO Query Tool - Interactive menu for common queries
"""

import requests
import json
import os
import argparse
from base64 import b64encode


class DataForSEOQuery:
    """Simple query tool for DataForSEO API"""

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.base_url = "https://api.dataforseo.com/v3"
        self.credentials = b64encode(f"{login}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.credentials}",
            "Content-Type": "application/json"
        }

    def serp_google_organic(self, keyword, location_code=2840):
        """Get Google organic SERP results for a keyword"""
        url = f"{self.base_url}/serp/google/organic/live/advanced"
        data = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": "en",
            "device": "desktop",
            "os": "windows"
        }]
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def keyword_search_volume(self, keywords, location_code=2840):
        """Get search volume for keywords"""
        url = f"{self.base_url}/keywords_data/google_ads/search_volume/live"
        data = [{
            "keywords": keywords if isinstance(keywords, list) else [keywords],
            "location_code": location_code,
            "language_code": "en"
        }]
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def ranked_keywords(self, domain):
        """Get ranked keywords for a domain"""
        url = f"{self.base_url}/dataforseo_labs/google/ranked_keywords/live"
        data = [{
            "target": domain,
            "language_code": "en",
            "location_code": 2840
        }]
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def domain_rank_overview(self, domain):
        """Get domain rank overview"""
        url = f"{self.base_url}/dataforseo_labs/google/domain_rank_overview/live"
        data = [{
            "target": domain,
            "language_code": "en",
            "location_code": 2840
        }]
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def competitor_domains(self, domain):
        """Get competitor domains"""
        url = f"{self.base_url}/dataforseo_labs/google/competitors_domain/live"
        data = [{
            "target": domain,
            "language_code": "en",
            "location_code": 2840,
            "limit": 10
        }]
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def backlinks_summary(self, domain):
        """Get backlinks summary for a domain"""
        url = f"{self.base_url}/backlinks/summary/live"
        data = [{
            "target": domain
        }]
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def get_account_info(self):
        """Get account balance and info"""
        url = f"{self.base_url}/appendix/user_data"
        response = requests.get(url, headers=self.headers)
        return response.json()


def print_menu():
    """Display available query options"""
    print("\n" + "=" * 60)
    print("DataForSEO Query Tool - What would you like to query?")
    print("=" * 60)
    print("\n1. Google SERP Results (organic search results for a keyword)")
    print("2. Keyword Search Volume (search volume for keywords)")
    print("3. Ranked Keywords (keywords a domain ranks for)")
    print("4. Domain Rank Overview (domain metrics and stats)")
    print("5. Competitor Domains (find competing domains)")
    print("6. Backlinks Summary (backlink profile of a domain)")
    print("7. Custom API Request (advanced - specify your own endpoint)")
    print("8. Exit")
    print("\n" + "=" * 60)


def save_results(data, filename):
    """Save results to a JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"\n[SAVED] Results saved to: {filename}")


def run_interactive_mode(client):
    """Run the interactive menu mode"""
    while True:
        print_menu()
        choice = input("\nEnter your choice (1-8): ").strip()

        try:
            if choice == "1":
                keyword = input("\nEnter keyword to search: ").strip()
                location = input("Location code (press Enter for USA/2840): ").strip()
                location_code = int(location) if location else 2840

                print(f"\n[QUERYING] Getting SERP results for '{keyword}'...")
                result = client.serp_google_organic(keyword, location_code)
                print(json.dumps(result, indent=2))

                save = input("\nSave results to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"serp_{keyword.replace(' ', '_')}.json"
                    save_results(result, filename)

            elif choice == "2":
                keywords = input("\nEnter keywords (comma-separated): ").strip()
                keyword_list = [k.strip() for k in keywords.split(',')]

                print(f"\n[QUERYING] Getting search volume for {len(keyword_list)} keyword(s)...")
                result = client.keyword_search_volume(keyword_list)
                print(json.dumps(result, indent=2))

                save = input("\nSave results to file? (y/n): ").strip().lower()
                if save == 'y':
                    save_results(result, "keyword_search_volume.json")

            elif choice == "3":
                domain = input("\nEnter domain (e.g., example.com): ").strip()

                print(f"\n[QUERYING] Getting ranked keywords for '{domain}'...")
                result = client.ranked_keywords(domain)
                print(json.dumps(result, indent=2))

                save = input("\nSave results to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"ranked_keywords_{domain.replace('.', '_')}.json"
                    save_results(result, filename)

            elif choice == "4":
                domain = input("\nEnter domain (e.g., example.com): ").strip()

                print(f"\n[QUERYING] Getting domain rank overview for '{domain}'...")
                result = client.domain_rank_overview(domain)
                print(json.dumps(result, indent=2))

                save = input("\nSave results to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"domain_overview_{domain.replace('.', '_')}.json"
                    save_results(result, filename)

            elif choice == "5":
                domain = input("\nEnter domain (e.g., example.com): ").strip()

                print(f"\n[QUERYING] Getting competitors for '{domain}'...")
                result = client.competitor_domains(domain)
                print(json.dumps(result, indent=2))

                save = input("\nSave results to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"competitors_{domain.replace('.', '_')}.json"
                    save_results(result, filename)

            elif choice == "6":
                domain = input("\nEnter domain (e.g., example.com): ").strip()

                print(f"\n[QUERYING] Getting backlinks summary for '{domain}'...")
                result = client.backlinks_summary(domain)
                print(json.dumps(result, indent=2))

                save = input("\nSave results to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"backlinks_{domain.replace('.', '_')}.json"
                    save_results(result, filename)

            elif choice == "7":
                endpoint = input("\nEnter API endpoint (e.g., serp/google/organic/live/advanced): ").strip()
                method = input("HTTP method (GET/POST, default POST): ").strip().upper() or "POST"

                if method == "POST":
                    print("\nEnter JSON data (or press Enter to skip):")
                    data_input = input().strip()
                    data = json.loads(data_input) if data_input else None
                else:
                    data = None

                print(f"\n[QUERYING] Making {method} request to {endpoint}...")
                url = f"{client.base_url}/{endpoint}"

                if method == "POST":
                    response = requests.post(url, headers=client.headers, json=data)
                else:
                    response = requests.get(url, headers=client.headers)

                result = response.json()
                print(json.dumps(result, indent=2))

                save = input("\nSave results to file? (y/n): ").strip().lower()
                if save == 'y':
                    save_results(result, "custom_query.json")

            elif choice == "8":
                print("\nGoodbye!")
                break

            else:
                print("\n[ERROR] Invalid choice. Please enter 1-8.")

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

        input("\nPress Enter to continue...")


def main():
    # Default credentials (can be overridden with --login and --password arguments or environment variables)
    DEFAULT_LOGIN = os.environ.get("DATAFORSEO_LOGIN")
    DEFAULT_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD")

    parser = argparse.ArgumentParser(
        description='DataForSEO Query Tool - Query SEO data via command line or interactive menu',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python dataforseo_query.py

  # SERP results for a keyword
  python dataforseo_query.py --query serp --keyword "python tutorial"

  # Search volume for keywords
  python dataforseo_query.py --query volume --keywords "seo,marketing,analytics"

  # Ranked keywords for a domain
  python dataforseo_query.py --query ranked --domain example.com

  # Domain rank overview
  python dataforseo_query.py --query domain --domain example.com

  # Competitor domains
  python dataforseo_query.py --query competitors --domain example.com

  # Backlinks summary
  python dataforseo_query.py --query backlinks --domain example.com

  # Save results to file
  python dataforseo_query.py --query serp --keyword "python" --output results.json
        """
    )

    parser.add_argument('--query', choices=['serp', 'volume', 'ranked', 'domain', 'competitors', 'backlinks'],
                        help='Type of query to perform')
    parser.add_argument('--keyword', help='Keyword for SERP query')
    parser.add_argument('--keywords', help='Comma-separated keywords for volume query')
    parser.add_argument('--domain', help='Domain for domain-related queries')
    parser.add_argument('--location', type=int, default=2840, help='Location code (default: 2840 for USA)')
    parser.add_argument('--output', '-o', help='Output file to save results (JSON format)')
    parser.add_argument('--login', help='DataForSEO login (or set DATAFORSEO_LOGIN env var)')
    parser.add_argument('--password', help='DataForSEO password (or set DATAFORSEO_PASSWORD env var)')

    args = parser.parse_args()

    # Get credentials - priority: arguments > environment variables > defaults
    login = args.login or os.environ.get("DATAFORSEO_LOGIN") or DEFAULT_LOGIN
    password = args.password or os.environ.get("DATAFORSEO_PASSWORD") or DEFAULT_PASSWORD

    if not login or not password:
        if args.query:
            print("\n[ERROR] Credentials required. Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD environment variables,")
            print("        or provide --login and --password arguments.")
            return
        print("\nEnvironment variables not found. Please enter credentials:")
        login = input("Enter your DataForSEO login: ").strip()
        password = input("Enter your DataForSEO password: ").strip()

    client = DataForSEOQuery(login, password)

    # Command-line mode
    if args.query:
        try:
            result = None

            if args.query == 'serp':
                if not args.keyword:
                    print("\n[ERROR] --keyword required for SERP query")
                    return
                print(f"\n[QUERYING] Getting SERP results for '{args.keyword}'...")
                result = client.serp_google_organic(args.keyword, args.location)

            elif args.query == 'volume':
                if not args.keywords:
                    print("\n[ERROR] --keywords required for volume query")
                    return
                keyword_list = [k.strip() for k in args.keywords.split(',')]
                print(f"\n[QUERYING] Getting search volume for {len(keyword_list)} keyword(s)...")
                result = client.keyword_search_volume(keyword_list, args.location)

            elif args.query == 'ranked':
                if not args.domain:
                    print("\n[ERROR] --domain required for ranked keywords query")
                    return
                print(f"\n[QUERYING] Getting ranked keywords for '{args.domain}'...")
                result = client.ranked_keywords(args.domain)

            elif args.query == 'domain':
                if not args.domain:
                    print("\n[ERROR] --domain required for domain rank query")
                    return
                print(f"\n[QUERYING] Getting domain rank overview for '{args.domain}'...")
                result = client.domain_rank_overview(args.domain)

            elif args.query == 'competitors':
                if not args.domain:
                    print("\n[ERROR] --domain required for competitors query")
                    return
                print(f"\n[QUERYING] Getting competitors for '{args.domain}'...")
                result = client.competitor_domains(args.domain)

            elif args.query == 'backlinks':
                if not args.domain:
                    print("\n[ERROR] --domain required for backlinks query")
                    return
                print(f"\n[QUERYING] Getting backlinks summary for '{args.domain}'...")
                result = client.backlinks_summary(args.domain)

            if result:
                print(json.dumps(result, indent=2))

                if args.output:
                    save_results(result, args.output)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
    else:
        # Interactive mode
        run_interactive_mode(client)


if __name__ == "__main__":
    main()
