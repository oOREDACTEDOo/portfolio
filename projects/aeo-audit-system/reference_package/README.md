# AEO Scraper Reference Package

Two production-ready scrapers for brand visibility monitoring.

## Files Included

| File | Purpose |
|------|---------|
| `reddit_visibility_scraper.py` | Scrapes Reddit for brand mentions |
| `google_reviews_scraper.py` | Fetches Google Business reviews via DataForSEO |

---

## 1. RedditVisibilityScraper

Scrapes Reddit for brand mentions using multiple data sources.

### Data Sources
- **Reddit .json endpoints** - No authentication required
- **DataForSEO Google Search** - Searches `"brand" site:reddit.com` (requires credentials)

### Dependencies
```
requests
```

### Usage Example
```python
from reddit_visibility_scraper import RedditVisibilityScraper

# Initialize (DataForSEO credentials optional but recommended)
scraper = RedditVisibilityScraper(
    dataforseo_login="your_login",      # Optional
    dataforseo_password="your_password", # Optional
    rate_limit_delay=2.0
)

# Scrape brand mentions
results = scraper.scrape_brand_mentions(
    brand_name="Client L",
    subreddits=["HomeDecorating", "InteriorDesign", "wallpaper"],
    days_back=180,
    use_google_search=True,  # Requires DataForSEO
    strict_match=False
)

# Save results
scraper.save_results(results, "output/client-l_reddit.json")

# Access data
print(f"Total mentions: {results['metadata']['total_mentions']}")
for mention in results['mentions'][:5]:
    print(f"- {mention['title']} ({mention['upvotes']} upvotes)")
```

### Output Structure
```json
{
  "metadata": {
    "brand": "Client L",
    "scraped_at": "2025-12-18T12:00:00",
    "subreddits_searched": ["HomeDecorating", "InteriorDesign"],
    "days_back": 180,
    "total_mentions": 24,
    "sources_used": ["reddit_json", "google_dataforseo"]
  },
  "mentions": [
    {
      "title": "Post title",
      "body": "Full post content",
      "url": "https://reddit.com/r/...",
      "subreddit": "HomeDecorating",
      "author": "username",
      "upvotes": 182,
      "upvote_ratio": 0.95,
      "comment_count": 71,
      "created_date": "2025-12-09T09:43:45",
      "source": "reddit_json"
    }
  ],
  "summary": {
    "total_mentions": 24,
    "total_upvotes": 642,
    "total_comments": 237,
    "subreddit_distribution": {"HomeDecorating": 12, "InteriorDesign": 8}
  }
}
```

### Watchlist Feature
Automatically tracks subreddits where mentions are found:
```python
# After scraping, update watchlist
watchlist = scraper.update_watchlist_from_results("Client L", results)

# Get monitored subreddits
subreddits = scraper.get_watchlist_subreddits("Client L")
```

---

## 2. GoogleReviewsScraper

Fetches Google Business reviews via DataForSEO Business Data API.

### Dependencies
```
requests
```

### Required Credentials
- DataForSEO login and password (required)
- API credits charged per request

### Usage Example
```python
from google_reviews_scraper import GoogleReviewsScraper

# Initialize (credentials required)
scraper = GoogleReviewsScraper(
    dataforseo_login="your_login",
    dataforseo_password="your_password",
    rate_limit_delay=1.0
)

# Option 1: Search for business first, then get reviews
search_results = scraper.search_business(
    keyword="Bunnings Warehouse",
    location_name="Sydney,New South Wales,Australia"
)

if search_results['results']:
    business = search_results['results'][0]
    reviews = scraper.get_reviews(
        place_id=business['place_id'],
        location_name="Sydney,New South Wales,Australia",
        depth=100,
        sort_by="newest"
    )

# Option 2: Full workflow in one call
results = scraper.scrape_brand_reviews(
    brand_name="Bunnings",
    search_queries=["Bunnings Warehouse Sydney", "Bunnings Warehouse Melbourne"],
    location_name="Sydney,New South Wales,Australia",
    reviews_per_location=100,
    sort_by="newest"
)

# Save results
scraper.save_results(results, "Bunnings")

# Extract for AI sentiment analysis
simplified = scraper.extract_reviews_for_sentiment(results)
```

### Output Structure
```json
{
  "metadata": {
    "brand": "Bunnings",
    "scraped_at": "2025-12-18T12:00:00",
    "search_queries": ["Bunnings Warehouse Sydney"],
    "location": "Sydney,New South Wales,Australia"
  },
  "locations": [
    {
      "query": "Bunnings Warehouse Sydney",
      "business": {
        "title": "Bunnings Warehouse Alexandria",
        "place_id": "ChIJ...",
        "rating": 4.2,
        "total_reviews": 1523
      },
      "reviews": [...]
    }
  ],
  "all_reviews": [
    {
      "review_id": "...",
      "rating": 5,
      "text": "Great service and selection...",
      "timestamp": "2025-12-01T10:00:00",
      "author": {
        "name": "John D",
        "reviews_count": 45
      },
      "owner_response": {
        "text": "Thank you for your feedback!",
        "timestamp": "2025-12-02T09:00:00"
      }
    }
  ],
  "summary": {
    "total_reviews": 100,
    "overall_average_rating": 4.2,
    "rating_distribution": {"5_star": 45, "4_star": 30, ...},
    "reviews_with_owner_response": 23
  }
}
```

---

## DataForSEO Setup

1. Create account at https://dataforseo.com
2. Get API credentials from dashboard
3. Note: API calls are charged per request

### Pricing (approximate)
- Google SERP search: ~$0.002 per result
- Google Reviews: ~$0.01 per task

---

## Integration Notes

- Both scrapers are standalone - no external dependencies on the main project
- Rate limiting is built-in (configurable delay between requests)
- Both handle brand name variations (& ↔ "and", hyphens, etc.)
- Results are JSON-serializable for easy storage/processing
