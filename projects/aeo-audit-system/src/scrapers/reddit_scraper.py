"""
Reddit Brand Mention Scraper
Searches Reddit for brand mentions across relevant subreddits
Returns sentiment, reach, and engagement metrics
"""

import praw
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import time

class RedditScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """
        Initialize Reddit API client
        Get credentials from: https://www.reddit.com/prefs/apps
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.pushshift_base = "https://api.pullpush.io/reddit/search"
        
    def search_brand_mentions(
        self, 
        brand_name: str, 
        subreddits: List[str],
        days_back: int = 180,
        limit: int = 100
    ) -> Dict:
        """
        Search for brand mentions across specified subreddits
        
        Args:
            brand_name: Brand to search for (e.g., "Lyreco")
            subreddits: List of subreddit names (without r/)
            days_back: How far back to search (days)
            limit: Max results per subreddit
            
        Returns:
            Dict with mentions, sentiment indicators, and engagement metrics
        """
        all_mentions = []
        
        # Search each subreddit
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search using Reddit API (last ~1000 posts)
                for submission in subreddit.search(
                    f'"{brand_name}"', 
                    limit=limit,
                    time_filter='all'
                ):
                    mention = self._parse_submission(submission, brand_name)
                    if mention:
                        all_mentions.append(mention)
                
                # Also search comments using Pushshift for deeper coverage
                pushshift_mentions = self._search_pushshift(
                    brand_name, 
                    subreddit_name,
                    days_back
                )
                all_mentions.extend(pushshift_mentions)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error searching r/{subreddit_name}: {str(e)}")
                continue
        
        # Remove duplicates
        unique_mentions = self._deduplicate(all_mentions)
        
        # Calculate metrics
        metrics = self._calculate_metrics(unique_mentions, brand_name)
        
        return {
            'brand': brand_name,
            'mentions_found': len(unique_mentions),
            'mentions': unique_mentions[:50],  # Top 50 for report
            'metrics': metrics,
            'subreddits_searched': subreddits,
            'search_period_days': days_back
        }
    
    def _parse_submission(self, submission, brand_name: str) -> Optional[Dict]:
        """Parse a Reddit submission into structured data"""
        try:
            # Check if submission is too old (Reddit API limitation)
            submission_date = datetime.fromtimestamp(submission.created_utc)
            if (datetime.now() - submission_date).days > 365:
                return None
            
            return {
                'type': 'submission',
                'title': submission.title,
                'text': submission.selftext[:500] if submission.selftext else '',
                'url': f"https://reddit.com{submission.permalink}",
                'subreddit': submission.subreddit.display_name,
                'author': str(submission.author) if submission.author else '[deleted]',
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'created_date': submission_date.isoformat(),
                'sentiment_indicators': self._detect_sentiment(
                    submission.title + ' ' + submission.selftext
                )
            }
        except Exception as e:
            print(f"Error parsing submission: {str(e)}")
            return None
    
    def _search_pushshift(
        self, 
        brand_name: str, 
        subreddit: str,
        days_back: int
    ) -> List[Dict]:
        """
        Use Pushshift/Pullpush API for historical data
        Pushshift was sunset, but Pullpush.io maintains the API
        """
        mentions = []
        
        try:
            # Calculate date range
            after = int((datetime.now() - timedelta(days=days_back)).timestamp())
            
            # Search submissions
            url = f"{self.pushshift_base}/submission/"
            params = {
                'q': brand_name,
                'subreddit': subreddit,
                'after': after,
                'size': 100,
                'sort': 'desc',
                'sort_type': 'score'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('data', []):
                    mention = {
                        'type': 'submission',
                        'title': item.get('title', ''),
                        'text': item.get('selftext', '')[:500],
                        'url': f"https://reddit.com{item.get('permalink', '')}",
                        'subreddit': item.get('subreddit', ''),
                        'author': item.get('author', '[deleted]'),
                        'score': item.get('score', 0),
                        'num_comments': item.get('num_comments', 0),
                        'created_utc': item.get('created_utc', 0),
                        'created_date': datetime.fromtimestamp(
                            item.get('created_utc', 0)
                        ).isoformat(),
                        'sentiment_indicators': self._detect_sentiment(
                            item.get('title', '') + ' ' + item.get('selftext', '')
                        )
                    }
                    mentions.append(mention)
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Pushshift error: {str(e)}")
        
        return mentions
    
    def _detect_sentiment(self, text: str) -> Dict:
        """
        Simple sentiment detection using keyword matching
        For production, integrate with Claude API for better analysis
        """
        text_lower = text.lower()
        
        positive_keywords = [
            'great', 'excellent', 'amazing', 'best', 'love', 
            'recommend', 'perfect', 'fantastic', 'awesome', 'good'
        ]
        
        negative_keywords = [
            'terrible', 'worst', 'awful', 'horrible', 'bad',
            'disappointing', 'poor', 'avoid', 'never again', 'waste'
        ]
        
        neutral_keywords = [
            'using', 'tried', 'considering', 'thinking about',
            'anyone use', 'opinions on'
        ]
        
        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
        neutral_count = sum(1 for kw in neutral_keywords if kw in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count,
            'neutral_indicators': neutral_count
        }
    
    def _deduplicate(self, mentions: List[Dict]) -> List[Dict]:
        """Remove duplicate mentions based on URL"""
        seen_urls = set()
        unique = []
        
        for mention in mentions:
            url = mention.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(mention)
        
        return unique
    
    def _calculate_metrics(self, mentions: List[Dict], brand_name: str) -> Dict:
        """Calculate aggregate metrics from mentions"""
        if not mentions:
            return {
                'total_mentions': 0,
                'avg_score': 0,
                'total_engagement': 0,
                'sentiment_breakdown': {'positive': 0, 'negative': 0, 'neutral': 0},
                'top_subreddits': [],
                'visibility_score': 0
            }
        
        total_score = sum(m.get('score', 0) for m in mentions)
        total_comments = sum(m.get('num_comments', 0) for m in mentions)
        
        sentiment_counts = {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
        
        for mention in mentions:
            sentiment = mention.get('sentiment_indicators', {}).get('sentiment', 'neutral')
            sentiment_counts[sentiment] += 1
        
        # Count mentions per subreddit
        subreddit_counts = {}
        for mention in mentions:
            sub = mention.get('subreddit', 'unknown')
            subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
        
        top_subreddits = sorted(
            subreddit_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Visibility score (0-10)
        # Based on: number of mentions, avg score, engagement
        visibility_score = min(10, (
            (len(mentions) / 10) * 3 +  # 30% weight on volume
            (total_score / len(mentions) / 10) * 4 +  # 40% weight on avg score
            (total_comments / len(mentions) / 5) * 3  # 30% weight on engagement
        ))
        
        return {
            'total_mentions': len(mentions),
            'avg_score': round(total_score / len(mentions), 2),
            'total_engagement': total_score + total_comments,
            'sentiment_breakdown': sentiment_counts,
            'sentiment_ratio': {
                'positive_pct': round(sentiment_counts['positive'] / len(mentions) * 100, 1),
                'negative_pct': round(sentiment_counts['negative'] / len(mentions) * 100, 1),
                'neutral_pct': round(sentiment_counts['neutral'] / len(mentions) * 100, 1)
            },
            'top_subreddits': [
                {'name': sub, 'mentions': count} 
                for sub, count in top_subreddits
            ],
            'visibility_score': round(visibility_score, 1)
        }
    
    def get_competitor_comparison(
        self, 
        brands: List[str],
        subreddits: List[str],
        days_back: int = 180
    ) -> Dict:
        """
        Compare multiple brands across Reddit
        Useful for competitive analysis
        """
        results = {}
        
        for brand in brands:
            print(f"Analyzing {brand}...")
            results[brand] = self.search_brand_mentions(
                brand, 
                subreddits,
                days_back
            )
            time.sleep(2)  # Rate limiting
        
        # Create comparison matrix
        comparison = {
            'brands': brands,
            'metrics': {
                brand: data['metrics'] 
                for brand, data in results.items()
            },
            'full_data': results
        }
        
        return comparison


def main():
    """Example usage"""
    
    # Initialize scraper (replace with your credentials)
    scraper = RedditScraper(
        client_id='YOUR_CLIENT_ID',
        client_secret='YOUR_CLIENT_SECRET',
        user_agent='AEO_Audit_Bot/1.0'
    )
    
    # Define brand and relevant subreddits
    brand = "Lyreco"
    subreddits = [
        'smallbusiness',
        'procurement',
        'office',
        'facilitymanagement',
        'UKSmallBusiness',
        'OfficeChairs',
        'Ergonomics',
        'BuyItForLife'
    ]
    
    # Search for mentions
    print(f"Searching Reddit for '{brand}' mentions...")
    results = scraper.search_brand_mentions(brand, subreddits, days_back=180)
    
    # Output results
    print(json.dumps(results, indent=2))
    
    # Example: Competitor comparison
    competitors = ["Lyreco", "Viking", "Staples"]
    print(f"\nComparing competitors: {competitors}")
    comparison = scraper.get_competitor_comparison(
        competitors, 
        subreddits,
        days_back=180
    )
    
    print(json.dumps(comparison['metrics'], indent=2))


if __name__ == "__main__":
    main()
