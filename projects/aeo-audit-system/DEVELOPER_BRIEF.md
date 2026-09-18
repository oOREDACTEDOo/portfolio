# AEO Audit System - Developer Brief

## Project Overview

**Purpose:** Lead magnet tool that generates AEO (Answer Engine Optimization) visibility reports for marketing clients. Shows brands their "AI blind spots" across community platforms and review sites.

**Business Model:** Free audit report → captures leads → converts to paid services

**Current Status:** ~85% complete for Reddit + Google Reviews components

---

## Scope of This Brief

This brief covers only the two data collection components:

1. **Reddit Mentions Scraper** - Community visibility & sentiment
2. **Google Reviews Scraper** - Customer reviews via DataForSEO

---

## 1. Reddit Mentions Scraper

### Status: FUNCTIONAL ✅

**File:** `src/scrapers/reddit_visibility_scraper.py` (964 lines)

### How It Works

The scraper does **NOT** use Reddit's API (no approval needed). Instead:

1. **DataForSEO SERP API** searches Google for `"Brand Name" site:reddit.com`
2. **Reddit .json endpoints** fetch post data directly (appending `.json` to any Reddit URL returns JSON - no auth required)

```
User Input: "Client L"
     ↓
DataForSEO Google Search: "Client L" site:reddit.com
                          "Client L" site:reddit.com
     ↓
Returns list of Reddit post URLs
     ↓
Fetch each URL + .json (e.g., reddit.com/r/HomeDecorating/comments/xyz/.json)
     ↓
Extract: title, body, upvotes, comments, author, date
     ↓
Output: JSON report with all mentions + summary stats
```

### Brand Name Variation Handling

The scraper automatically handles brand name variations:

**Google Search Queries Generated:**
```python
# Input: "Client L"
# Searches both:
"Client L" site:reddit.com
"Client L" site:reddit.com
```

**Text Matching Variations (11+ patterns):**
```python
Client L
Client L
Client L      # HTML entity
client-l
client-l
Client L           # double space
```

**File Naming Normalization:**
```python
"Client L" → "client-l"  (slug for filenames)
```

### Data Collected Per Mention

| Field | Description |
|-------|-------------|
| `title` | Post title |
| `body` | Full post text (not truncated) |
| `url` | Direct link to Reddit post |
| `subreddit` | Which subreddit (e.g., "HomeDecorating") |
| `author` | Reddit username |
| `upvotes` | Post score |
| `upvote_ratio` | % upvotes vs downvotes |
| `comment_count` | Number of comments |
| `created_date` | When posted |
| `is_comment` | true if this is a comment, not a post |
| `source` | "google_dataforseo" or "reddit_json" |
| `google_rank` | Position in Google results (if found via Google) |

### Summary Statistics Generated

```json
{
  "total_mentions": 24,
  "total_upvotes": 642,
  "total_comments": 237,
  "avg_upvotes": 26.75,
  "avg_comments": 9.88,
  "total_engagement": 879,
  "subreddit_distribution": {
    "DesignMyRoom": 4,
    "interiordecorating": 3,
    "HomeDecorating": 2
  },
  "date_range": {
    "earliest": "2025-06-23",
    "latest": "2025-12-16"
  }
}
```

### Watchlist Feature

The scraper automatically tracks which subreddits mention the brand:

- Saves to `data/watchlists/{brand_slug}.json`
- Updates each time scraper runs
- Useful for ongoing monitoring

### CLI Usage

```bash
# Basic usage
python src/tools/scrape_reddit_visibility.py --brand "Client L"

# With options
python src/tools/scrape_reddit_visibility.py \
  --brand "Client L" \
  --days-back 180 \
  --include-comments \
  --use-google-search
```

### API Endpoint

```
POST /scrape/reddit
```

**Request:**
```json
{
  "brand_name": "Client L",
  "subreddits": ["HomeDecorating", "interiordecorating", "DIY"],
  "days_back": 180
}
```

**Response:** Full JSON report (see example in `reports/` folder)

---

## 2. Google Reviews Scraper

### Status: FUNCTIONAL ✅

**File:** `src/scrapers/google_reviews_scraper.py` (515 lines)

### How It Works

Uses **DataForSEO Business Data API** - no scraping required:

```
User Input: "Client L"
     ↓
Step 1: Search for business
POST https://api.dataforseo.com/v3/business_data/google/my_business_info/live
     ↓
Returns: place_id, rating, review_count, address
     ↓
Step 2: Fetch reviews (async)
POST https://api.dataforseo.com/v3/business_data/google/reviews/task_post
     ↓
Poll for results
GET https://api.dataforseo.com/v3/business_data/google/reviews/task_get/{task_id}
     ↓
Output: JSON with business info + individual reviews
```

### Data Collected

**Business Info:**
```json
{
  "title": "Client L",
  "place_id": "ChIJ...",
  "address": "123 Main St, Sydney",
  "rating": 4.5,
  "total_reviews": 127
}
```

**Per Review:**
```json
{
  "review_id": "abc123",
  "rating": 5,
  "text": "Great wallpaper selection...",
  "timestamp": "2025-10-15T14:30:00",
  "author": {
    "name": "John D.",
    "reviews_count": 45
  },
  "owner_response": {
    "text": "Thank you for your feedback!",
    "timestamp": "2025-10-16T09:00:00"
  }
}
```

**Summary:**
```json
{
  "total_reviews_fetched": 100,
  "average_rating": 4.5,
  "rating_distribution": {
    "5_star": 65,
    "4_star": 20,
    "3_star": 10,
    "2_star": 3,
    "1_star": 2
  },
  "reviews_with_owner_response": 45
}
```

### CLI Usage

```bash
# Basic usage
python src/tools/scrape_google_reviews.py --brand "Client L"

# With location
python src/tools/scrape_google_reviews.py \
  --brand "Bunnings Warehouse" \
  --location "Sydney,New South Wales,Australia" \
  --depth 100 \
  --sort newest
```

### API Endpoint

```
POST /scrape/google-reviews
```

**Request:**
```json
{
  "brand_name": "Client L",
  "location": "Sydney,New South Wales,Australia",
  "depth": 100,
  "sort_by": "newest"
}
```

---

## Configuration

### Required Credentials

**DataForSEO** (required for both scrapers):
```env
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password
```

Get credentials from: https://app.dataforseo.com/api-access

### Cost Per Audit

| API Call | Cost |
|----------|------|
| DataForSEO SERP (Reddit search) | ~$0.05 |
| DataForSEO Google Reviews | ~$0.10-0.20 |
| **Total per brand** | **~$0.15-0.25** |

---

## File Structure

```
C:\Projects\aeo-audit-system\
├── src/
│   ├── scrapers/
│   │   ├── reddit_visibility_scraper.py   # Reddit mentions (964 lines)
│   │   └── google_reviews_scraper.py      # Google Reviews (515 lines)
│   ├── tools/
│   │   ├── scrape_reddit_visibility.py    # Reddit CLI
│   │   ├── scrape_google_reviews.py       # Google Reviews CLI
│   │   └── scrape_brand_visibility.py     # Combined CLI
│   └── api/
│       └── n8n_api.py                     # Flask REST API
├── reports/
│   ├── reddit_client-l_*.json        # Sample Reddit outputs
│   └── google_reviews/                    # Sample Google Reviews outputs
├── data/
│   └── watchlists/                        # Subreddit watchlists per brand
├── config/
│   ├── .env.example                       # Environment template
│   └── subreddits.json                    # Industry subreddit mappings
└── requirements.txt                       # Python dependencies
```

---

## Sample Output Files

Located in `reports/` folder:

- `reddit_client-l_20251218_130645.json` - 24 mentions found
- `google_reviews/bunnings_google_reviews_20251218_144304.json`
- `google_reviews/clienta_google_reviews_20251219_101127.json`

---

## What's NOT Built (Out of Scope)

These components are planned but not implemented:

- Data aggregator (combining sources)
- Claude AI analyzer (sentiment/insights)
- Report generator (PDF output)
- N8N workflow integration

---

## Quick Start for Developers

1. **Install dependencies:**
   ```bash
   cd C:\Projects\aeo-audit-system
   pip install -r requirements.txt
   ```

2. **Configure credentials:**
   ```bash
   cp config/.env.example .env
   # Edit .env with DataForSEO credentials
   ```

3. **Test Reddit scraper:**
   ```bash
   python src/tools/scrape_reddit_visibility.py --brand "Test Brand" --use-google-search
   ```

4. **Test Google Reviews scraper:**
   ```bash
   python src/tools/scrape_google_reviews.py --brand "Bunnings Warehouse"
   ```

5. **Check output:**
   ```bash
   ls reports/
   ```

---

## Key Technical Notes

1. **No Reddit API approval needed** - Uses Google search + Reddit .json endpoints
2. **Brand variations are automatic** - & ↔ "and" handled in code
3. **Async polling for Google Reviews** - task_post → poll → task_get pattern
4. **Rate limiting built-in** - 2 second delays between requests
5. **Full text preserved** - Post bodies are not truncated

---

## Contact

For questions about this codebase, refer to:
- `START_HERE.md` - Project overview
- `docs/SETUP.md` - Detailed setup instructions
- Sample JSON files in `reports/` folder
