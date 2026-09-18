"""
Review Site Scraper
Scrapes business reviews from Yelp, Trustpilot, and G2/Capterra
Uses Playwright for JavaScript-heavy sites
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import requests
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
import re

class ReviewScraper:
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_yelp(self, business_name: str, location: str = "") -> Dict:
        """
        Scrape Yelp reviews for a business
        Uses Playwright to handle dynamic content
        """
        print(f"Scraping Yelp for: {business_name}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Search for business
                search_query = business_name + (" " + location if location else "")
                search_url = f"https://www.yelp.com/search?find_desc={search_query.replace(' ', '+')}"
                
                page.goto(search_url, wait_until='networkidle')
                time.sleep(2)
                
                # Get first business result
                try:
                    first_result = page.locator('[data-testid="serp-ia-card"]').first
                    business_link = first_result.locator('a[href*="/biz/"]').first.get_attribute('href')
                    
                    if not business_link.startswith('http'):
                        business_link = f"https://www.yelp.com{business_link}"
                    
                    # Visit business page
                    page.goto(business_link, wait_until='networkidle')
                    time.sleep(2)
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract rating
                    rating_elem = soup.find('div', {'role': 'img', 'aria-label': re.compile(r'star rating')})
                    rating = None
                    if rating_elem:
                        rating_text = rating_elem.get('aria-label', '')
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    
                    # Extract review count
                    review_count_elem = soup.find('a', href=re.compile(r'#reviews'))
                    review_count = 0
                    if review_count_elem:
                        review_text = review_count_elem.get_text()
                        count_match = re.search(r'(\d+)', review_text.replace(',', ''))
                        if count_match:
                            review_count = int(count_match.group(1))
                    
                    # Extract recent reviews
                    reviews = []
                    review_elements = soup.find_all('div', {'data-testid': re.compile(r'review-card')})
                    
                    for review_elem in review_elements[:10]:  # Get top 10 reviews
                        review_data = self._parse_yelp_review(review_elem)
                        if review_data:
                            reviews.append(review_data)
                    
                    browser.close()
                    
                    return {
                        'platform': 'yelp',
                        'business_name': business_name,
                        'url': business_link,
                        'rating': rating,
                        'review_count': review_count,
                        'reviews': reviews,
                        'found': True
                    }
                    
                except Exception as e:
                    print(f"Business not found on Yelp: {str(e)}")
                    browser.close()
                    return {
                        'platform': 'yelp',
                        'business_name': business_name,
                        'found': False,
                        'error': str(e)
                    }
                    
            except Exception as e:
                print(f"Yelp scraping error: {str(e)}")
                browser.close()
                return {
                    'platform': 'yelp',
                    'business_name': business_name,
                    'found': False,
                    'error': str(e)
                }
    
    def _parse_yelp_review(self, review_elem) -> Optional[Dict]:
        """Parse individual Yelp review"""
        try:
            # Rating
            rating_elem = review_elem.find('div', {'role': 'img', 'aria-label': re.compile(r'star rating')})
            rating = None
            if rating_elem:
                rating_text = rating_elem.get('aria-label', '')
                rating_match = re.search(r'(\d+)', rating_text)
                if rating_match:
                    rating = int(rating_match.group(1))
            
            # Review text
            text_elem = review_elem.find('span', {'lang': True})
            text = text_elem.get_text(strip=True) if text_elem else ''
            
            # Date
            date_elem = review_elem.find('span', string=re.compile(r'\d{1,2}/\d{1,2}/\d{4}'))
            date = date_elem.get_text(strip=True) if date_elem else None
            
            return {
                'rating': rating,
                'text': text[:300],  # First 300 chars
                'date': date
            }
        except:
            return None
    
    def scrape_trustpilot(self, business_name: str, domain: Optional[str] = None) -> Dict:
        """
        Scrape Trustpilot reviews
        Can use domain or business name
        """
        print(f"Scraping Trustpilot for: {business_name}")
        
        # Try to find business page
        if domain:
            # Direct URL if we know the domain
            url = f"https://www.trustpilot.com/review/{domain}"
        else:
            # Search for business
            search_url = f"https://www.trustpilot.com/search?query={business_name.replace(' ', '+')}"
            
            try:
                response = requests.get(search_url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find first result
                first_result = soup.find('a', {'name': 'business-unit-card-link'})
                if first_result:
                    url = f"https://www.trustpilot.com{first_result.get('href')}"
                else:
                    return {
                        'platform': 'trustpilot',
                        'business_name': business_name,
                        'found': False,
                        'error': 'Business not found'
                    }
            except Exception as e:
                return {
                    'platform': 'trustpilot',
                    'business_name': business_name,
                    'found': False,
                    'error': str(e)
                }
        
        # Scrape business page
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract rating
            rating_elem = soup.find('p', {'data-rating-typography': 'true'})
            rating = None
            if rating_elem:
                rating = float(rating_elem.get_text(strip=True))
            
            # Extract review count
            review_count_elem = soup.find('p', {'data-reviews-count-typography': 'true'})
            review_count = 0
            if review_count_elem:
                count_text = review_count_elem.get_text(strip=True)
                count_match = re.search(r'([\d,]+)', count_text)
                if count_match:
                    review_count = int(count_match.group(1).replace(',', ''))
            
            # Extract rating distribution
            rating_dist = {}
            for i in range(1, 6):
                star_elem = soup.find('label', {'for': f'star-rating-{i}'})
                if star_elem:
                    parent = star_elem.find_parent('a')
                    if parent:
                        count_text = parent.get_text()
                        count_match = re.search(r'(\d+)', count_text)
                        if count_match:
                            rating_dist[f'{i}_star'] = int(count_match.group(1))
            
            # Extract recent reviews
            reviews = []
            review_cards = soup.find_all('article', {'data-service-review-card-paper': 'true'})
            
            for card in review_cards[:10]:
                review_data = self._parse_trustpilot_review(card)
                if review_data:
                    reviews.append(review_data)
            
            return {
                'platform': 'trustpilot',
                'business_name': business_name,
                'url': url,
                'rating': rating,
                'review_count': review_count,
                'rating_distribution': rating_dist,
                'reviews': reviews,
                'found': True
            }
            
        except Exception as e:
            print(f"Trustpilot scraping error: {str(e)}")
            return {
                'platform': 'trustpilot',
                'business_name': business_name,
                'found': False,
                'error': str(e)
            }
    
    def _parse_trustpilot_review(self, card) -> Optional[Dict]:
        """Parse individual Trustpilot review"""
        try:
            # Rating
            rating_elem = card.find('div', {'data-service-review-rating': True})
            rating = None
            if rating_elem:
                rating_img = rating_elem.find('img')
                if rating_img:
                    alt_text = rating_img.get('alt', '')
                    rating_match = re.search(r'(\d+)', alt_text)
                    if rating_match:
                        rating = int(rating_match.group(1))
            
            # Title
            title_elem = card.find('h2', {'data-service-review-title-typography': 'true'})
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Text
            text_elem = card.find('p', {'data-service-review-text-typography': 'true'})
            text = text_elem.get_text(strip=True) if text_elem else ''
            
            # Date
            date_elem = card.find('time')
            date = date_elem.get('datetime') if date_elem else None
            
            return {
                'rating': rating,
                'title': title,
                'text': text[:300],
                'date': date
            }
        except:
            return None
    
    def scrape_g2(self, product_name: str, category: str = "") -> Dict:
        """
        Scrape G2 reviews (for software products)
        Note: G2 has strong anti-scraping, may require proxies
        """
        print(f"Scraping G2 for: {product_name}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Search for product
                search_query = product_name + (" " + category if category else "")
                search_url = f"https://www.g2.com/search?query={search_query.replace(' ', '+')}"
                
                page.goto(search_url, wait_until='networkidle')
                time.sleep(3)
                
                # Click first result
                try:
                    first_result = page.locator('a[href*="/products/"]').first
                    product_link = first_result.get_attribute('href')
                    
                    if not product_link.startswith('http'):
                        product_link = f"https://www.g2.com{product_link}"
                    
                    page.goto(product_link, wait_until='networkidle')
                    time.sleep(3)
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract rating (G2 structure changes frequently)
                    rating = None
                    rating_elem = soup.find('div', {'data-testid': 'rating-value'})
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    
                    # Extract review count
                    review_count = 0
                    review_count_elem = soup.find('span', string=re.compile(r'\d+\s+Reviews'))
                    if review_count_elem:
                        count_text = review_count_elem.get_text()
                        count_match = re.search(r'([\d,]+)', count_text)
                        if count_match:
                            review_count = int(count_match.group(1).replace(',', ''))
                    
                    browser.close()
                    
                    return {
                        'platform': 'g2',
                        'product_name': product_name,
                        'url': product_link,
                        'rating': rating,
                        'review_count': review_count,
                        'found': True
                    }
                    
                except Exception as e:
                    print(f"Product not found on G2: {str(e)}")
                    browser.close()
                    return {
                        'platform': 'g2',
                        'product_name': product_name,
                        'found': False,
                        'error': str(e)
                    }
                    
            except Exception as e:
                print(f"G2 scraping error: {str(e)}")
                browser.close()
                return {
                    'platform': 'g2',
                    'product_name': product_name,
                    'found': False,
                    'error': str(e)
                }
    
    def aggregate_reviews(self, business_name: str, domain: Optional[str] = None) -> Dict:
        """
        Aggregate reviews from all platforms
        Returns unified metrics
        """
        results = {
            'business_name': business_name,
            'platforms': {}
        }
        
        # Scrape each platform
        platforms = [
            ('yelp', lambda: self.scrape_yelp(business_name)),
            ('trustpilot', lambda: self.scrape_trustpilot(business_name, domain)),
        ]
        
        for platform_name, scraper_func in platforms:
            try:
                print(f"\nScraping {platform_name}...")
                data = scraper_func()
                results['platforms'][platform_name] = data
                time.sleep(2)  # Rate limiting
            except Exception as e:
                print(f"Error scraping {platform_name}: {str(e)}")
                results['platforms'][platform_name] = {
                    'platform': platform_name,
                    'found': False,
                    'error': str(e)
                }
        
        # Calculate aggregate metrics
        results['aggregate'] = self._calculate_aggregate_metrics(results['platforms'])
        
        return results
    
    def _calculate_aggregate_metrics(self, platforms: Dict) -> Dict:
        """Calculate aggregate review metrics across platforms"""
        total_reviews = 0
        weighted_rating = 0
        platforms_found = 0
        
        for platform_name, data in platforms.items():
            if data.get('found') and data.get('review_count'):
                count = data['review_count']
                rating = data.get('rating', 0)
                
                total_reviews += count
                weighted_rating += rating * count
                platforms_found += 1
        
        avg_rating = weighted_rating / total_reviews if total_reviews > 0 else 0
        
        # Review volume score (0-10)
        volume_score = min(10, (total_reviews / 100) * 5)
        
        # Rating quality score (0-10)
        quality_score = (avg_rating / 5) * 10 if avg_rating > 0 else 0
        
        # Overall review authority score
        authority_score = (
            (volume_score * 0.6) +  # Volume matters more
            (quality_score * 0.3) +  # Quality is important
            (platforms_found * 0.1 * 10)  # Platform diversity
        )
        
        return {
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 2),
            'platforms_found': platforms_found,
            'volume_score': round(volume_score, 1),
            'quality_score': round(quality_score, 1),
            'authority_score': round(authority_score, 1)
        }


def main():
    """Example usage"""
    scraper = ReviewScraper()
    
    # Single platform examples
    print("=== Yelp Example ===")
    yelp_data = scraper.scrape_yelp("Lyreco", "France")
    print(json.dumps(yelp_data, indent=2))
    
    print("\n=== Trustpilot Example ===")
    trustpilot_data = scraper.scrape_trustpilot("Lyreco", "lyreco.com")
    print(json.dumps(trustpilot_data, indent=2))
    
    # Aggregate example
    print("\n=== Aggregate Reviews ===")
    aggregate_data = scraper.aggregate_reviews("Lyreco", "lyreco.com")
    print(json.dumps(aggregate_data, indent=2))


if __name__ == "__main__":
    main()
