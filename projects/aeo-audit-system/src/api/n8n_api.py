"""
N8N API Wrapper
Flask API that exposes scrapers as HTTP endpoints for N8N workflows
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config
from utils.logger import get_logger
from utils.validators import validate_audit_request, ValidationError
from scrapers.reddit_scraper import RedditScraper
from scrapers.review_scraper import ReviewScraper
from scrapers.knowledge_checker import KnowledgePresenceChecker

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY

# Configure CORS
CORS(app, resources={r"/*": {"origins": config.get_cors_origins()}})

# Initialize logger
logger = get_logger(__name__)


# ============================================
# Authentication Decorator
# ============================================

def require_api_key(f):
    """Decorator to require API key for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip auth check if no API key configured (development mode)
        if not config.N8N_API_KEY:
            return f(*args, **kwargs)
        
        # Check API key in headers
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != config.N8N_API_KEY:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid or missing API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# Error Handlers
# ============================================

@app.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle validation errors"""
    logger.error(f"Validation error: {str(error)}")
    return jsonify({
        'error': 'Validation Error',
        'message': str(error)
    }), 400


@app.errorhandler(Exception)
def handle_generic_error(error):
    """Handle generic errors"""
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    
    if config.FLASK_DEBUG:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error)
        }), 500
    else:
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


# ============================================
# Health & Status Endpoints
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'aeo-audit-api',
        'version': '1.0.0',
        'environment': config.FLASK_ENV
    }), 200


@app.route('/status', methods=['GET'])
def status_check():
    """Detailed status check endpoint"""
    status = {
        'service': 'aeo-audit-api',
        'status': 'operational',
        'environment': config.FLASK_ENV,
        'configuration': {
            'reddit_configured': bool(config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET),
            'google_kg_configured': bool(config.GOOGLE_KG_API_KEY),
            'anthropic_configured': bool(config.ANTHROPIC_API_KEY),
            'skip_reddit': config.SKIP_REDDIT,
            'skip_reviews': config.SKIP_REVIEWS,
            'skip_knowledge': config.SKIP_KNOWLEDGE,
            'use_mock_data': config.USE_MOCK_DATA
        }
    }
    
    return jsonify(status), 200


# ============================================
# Reddit Scraping Endpoint
# ============================================

@app.route('/scrape/reddit', methods=['POST'])
@require_api_key
def scrape_reddit():
    """
    Scrape Reddit for brand mentions
    
    Request body:
    {
        "brand_name": "string",
        "subreddits": ["subreddit1", "subreddit2"],
        "days_back": 180 (optional),
        "limit": 100 (optional)
    }
    """
    logger.info("Received Reddit scraping request")
    
    try:
        data = request.get_json()
        
        # Validate required fields
        brand_name = data.get('brand_name')
        if not brand_name:
            raise ValidationError("brand_name is required")
        
        subreddits = data.get('subreddits', [])
        if not subreddits:
            # Default subreddits for general business
            subreddits = ['smallbusiness', 'Entrepreneur', 'business']
        
        days_back = data.get('days_back', config.DEFAULT_DAYS_BACK)
        limit = data.get('limit', config.MAX_REDDIT_RESULTS)
        
        # Check if Reddit scraping is disabled
        if config.SKIP_REDDIT:
            logger.info("Reddit scraping skipped (SKIP_REDDIT=True)")
            return jsonify({
                'skipped': True,
                'message': 'Reddit scraping is disabled'
            }), 200
        
        # Initialize scraper
        scraper = RedditScraper(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT
        )
        
        # Perform search
        logger.info(f"Searching Reddit for '{brand_name}' across {len(subreddits)} subreddits")
        results = scraper.search_brand_mentions(
            brand_name=brand_name,
            subreddits=subreddits,
            days_back=days_back,
            limit=limit
        )
        
        logger.info(f"Reddit search completed. Found {results['mentions_found']} mentions")
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Reddit scraping error: {str(e)}", exc_info=True)
        raise


@app.route('/scrape/reddit/competitors', methods=['POST'])
@require_api_key
def scrape_reddit_competitors():
    """
    Compare multiple brands on Reddit
    
    Request body:
    {
        "brands": ["Brand1", "Brand2", "Brand3"],
        "subreddits": ["subreddit1", "subreddit2"],
        "days_back": 180 (optional)
    }
    """
    logger.info("Received Reddit competitor comparison request")
    
    try:
        data = request.get_json()
        
        brands = data.get('brands', [])
        if not brands or len(brands) < 2:
            raise ValidationError("At least 2 brands required for comparison")
        
        subreddits = data.get('subreddits', ['smallbusiness', 'Entrepreneur'])
        days_back = data.get('days_back', config.DEFAULT_DAYS_BACK)
        
        if config.SKIP_REDDIT:
            return jsonify({'skipped': True}), 200
        
        # Initialize scraper
        scraper = RedditScraper(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT
        )
        
        # Compare brands
        logger.info(f"Comparing {len(brands)} brands on Reddit")
        results = scraper.get_competitor_comparison(
            brands=brands,
            subreddits=subreddits,
            days_back=days_back
        )
        
        logger.info("Reddit competitor comparison completed")
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Reddit competitor comparison error: {str(e)}", exc_info=True)
        raise


# ============================================
# Review Scraping Endpoint
# ============================================

@app.route('/scrape/reviews', methods=['POST'])
@require_api_key
def scrape_reviews():
    """
    Scrape reviews from multiple platforms
    
    Request body:
    {
        "business_name": "string",
        "domain": "example.com" (optional)
    }
    """
    logger.info("Received review scraping request")
    
    try:
        data = request.get_json()
        
        business_name = data.get('business_name')
        if not business_name:
            raise ValidationError("business_name is required")
        
        domain = data.get('domain')
        
        if config.SKIP_REVIEWS:
            logger.info("Review scraping skipped (SKIP_REVIEWS=True)")
            return jsonify({
                'skipped': True,
                'message': 'Review scraping is disabled'
            }), 200
        
        # Initialize scraper
        scraper = ReviewScraper()
        
        # Aggregate reviews
        logger.info(f"Aggregating reviews for '{business_name}'")
        results = scraper.aggregate_reviews(
            business_name=business_name,
            domain=domain
        )
        
        logger.info(f"Review aggregation completed. Found {results['aggregate']['total_reviews']} total reviews")
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Review scraping error: {str(e)}", exc_info=True)
        raise


# ============================================
# Knowledge Graph Checking Endpoint
# ============================================

@app.route('/check/knowledge', methods=['POST'])
@require_api_key
def check_knowledge():
    """
    Check knowledge platform presence
    
    Request body:
    {
        "brand_name": "string"
    }
    """
    logger.info("Received knowledge check request")
    
    try:
        data = request.get_json()
        
        brand_name = data.get('brand_name')
        if not brand_name:
            raise ValidationError("brand_name is required")
        
        if config.SKIP_KNOWLEDGE:
            logger.info("Knowledge check skipped (SKIP_KNOWLEDGE=True)")
            return jsonify({
                'skipped': True,
                'message': 'Knowledge checking is disabled'
            }), 200
        
        # Initialize checker
        checker = KnowledgePresenceChecker(
            google_kg_api_key=config.GOOGLE_KG_API_KEY
        )
        
        # Perform comprehensive check
        logger.info(f"Checking knowledge presence for '{brand_name}'")
        results = checker.comprehensive_check(brand_name)
        
        logger.info(f"Knowledge check completed. Authority score: {results['authority_metrics']['knowledge_authority_score']}")
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Knowledge check error: {str(e)}", exc_info=True)
        raise


# ============================================
# Complete Audit Endpoint
# ============================================

@app.route('/audit/complete', methods=['POST'])
@require_api_key
def complete_audit():
    """
    Run complete AEO audit (all scrapers)
    
    Request body:
    {
        "brand_name": "string",
        "domain": "example.com" (optional),
        "industry": "string" (optional),
        "competitors": ["Brand1", "Brand2"] (optional),
        "subreddits": ["sub1", "sub2"] (optional),
        "days_back": 180 (optional)
    }
    """
    logger.info("Received complete audit request")
    
    try:
        data = request.get_json()
        
        # Validate request
        validated_data = validate_audit_request(data)
        
        brand_name = validated_data['brand_name']
        domain = validated_data.get('domain')
        competitors = validated_data.get('competitors', [])
        industry = validated_data.get('industry')
        subreddits = data.get('subreddits', get_industry_subreddits(industry))
        days_back = validated_data.get('days_back', config.DEFAULT_DAYS_BACK)
        
        logger.info(f"Starting complete audit for '{brand_name}'")
        
        results = {
            'brand_name': brand_name,
            'domain': domain,
            'industry': industry,
            'competitors': competitors,
            'audit_timestamp': None,  # Would add timestamp
            'data': {}
        }
        
        # 1. Reddit Analysis
        if not config.SKIP_REDDIT:
            logger.info("Running Reddit analysis...")
            try:
                reddit_scraper = RedditScraper(
                    client_id=config.REDDIT_CLIENT_ID,
                    client_secret=config.REDDIT_CLIENT_SECRET,
                    user_agent=config.REDDIT_USER_AGENT
                )
                
                results['data']['reddit'] = reddit_scraper.search_brand_mentions(
                    brand_name=brand_name,
                    subreddits=subreddits,
                    days_back=days_back
                )
                
                # Compare with competitors if provided
                if competitors:
                    results['data']['reddit_comparison'] = reddit_scraper.get_competitor_comparison(
                        brands=[brand_name] + competitors,
                        subreddits=subreddits,
                        days_back=days_back
                    )
            except Exception as e:
                logger.error(f"Reddit analysis failed: {str(e)}")
                results['data']['reddit'] = {'error': str(e)}
        
        # 2. Review Aggregation
        if not config.SKIP_REVIEWS:
            logger.info("Running review aggregation...")
            try:
                review_scraper = ReviewScraper()
                results['data']['reviews'] = review_scraper.aggregate_reviews(
                    business_name=brand_name,
                    domain=domain
                )
            except Exception as e:
                logger.error(f"Review aggregation failed: {str(e)}")
                results['data']['reviews'] = {'error': str(e)}
        
        # 3. Knowledge Platform Check
        if not config.SKIP_KNOWLEDGE:
            logger.info("Running knowledge platform check...")
            try:
                knowledge_checker = KnowledgePresenceChecker(
                    google_kg_api_key=config.GOOGLE_KG_API_KEY
                )
                results['data']['knowledge'] = knowledge_checker.comprehensive_check(brand_name)
            except Exception as e:
                logger.error(f"Knowledge check failed: {str(e)}")
                results['data']['knowledge'] = {'error': str(e)}
        
        logger.info(f"Complete audit finished for '{brand_name}'")
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Complete audit error: {str(e)}", exc_info=True)
        raise


# ============================================
# Helper Functions
# ============================================

def get_industry_subreddits(industry: str = None) -> list:
    """Get relevant subreddits based on industry"""
    
    # Default general business subreddits
    default = [
        'smallbusiness',
        'Entrepreneur',
        'business',
        'marketing'
    ]
    
    if not industry:
        return default
    
    # Industry-specific subreddit mappings
    industry_map = {
        'office supplies': ['smallbusiness', 'office', 'procurement', 'facilitymanagement'],
        'saas': ['saas', 'startups', 'Entrepreneur', 'webdev'],
        'ecommerce': ['ecommerce', 'shopify', 'Entrepreneur', 'smallbusiness'],
        'healthcare': ['healthcare', 'medicine', 'nursing', 'healthIT'],
        'finance': ['finance', 'personalfinance', 'investing', 'FinTech'],
        'real estate': ['realestate', 'RealEstateInvesting', 'FirstTimeHomeBuyer'],
        'technology': ['technology', 'tech', 'gadgets', 'software'],
        'food': ['food', 'Cooking', 'recipes', 'FoodPorn'],
        'travel': ['travel', 'solotravel', 'backpacking', 'TravelHacks'],
    }
    
    industry_lower = industry.lower()
    for key, subreddits in industry_map.items():
        if key in industry_lower:
            return subreddits
    
    return default


# ============================================
# Main Application Entry Point
# ============================================

if __name__ == '__main__':
    # Print configuration on startup
    if not config.is_production():
        config.print_config()
    
    logger.info(f"Starting AEO Audit API on {config.FLASK_HOST}:{config.FLASK_PORT}")
    logger.info(f"Environment: {config.FLASK_ENV}")
    logger.info(f"Debug mode: {config.FLASK_DEBUG}")
    
    # Run Flask app
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
