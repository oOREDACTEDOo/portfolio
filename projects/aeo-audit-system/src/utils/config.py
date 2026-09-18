"""
Configuration Management Module
Loads and validates environment variables
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)


class Config:
    """Application configuration loaded from environment variables"""
    
    # ============================================
    # Reddit API Configuration
    # ============================================
    REDDIT_CLIENT_ID: str = os.getenv('REDDIT_CLIENT_ID', '')
    REDDIT_CLIENT_SECRET: str = os.getenv('REDDIT_CLIENT_SECRET', '')
    REDDIT_USER_AGENT: str = os.getenv('REDDIT_USER_AGENT', 'AEO_Audit_Bot/1.0')
    
    # ============================================
    # Google APIs
    # ============================================
    GOOGLE_KG_API_KEY: Optional[str] = os.getenv('GOOGLE_KG_API_KEY')
    
    # ============================================
    # AI Testing APIs
    # ============================================
    ANTHROPIC_API_KEY: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    PERPLEXITY_API_KEY: Optional[str] = os.getenv('PERPLEXITY_API_KEY')
    
    # ============================================
    # DataForSEO API
    # ============================================
    DATAFORSEO_LOGIN: Optional[str] = os.getenv('DATAFORSEO_LOGIN')
    DATAFORSEO_PASSWORD: Optional[str] = os.getenv('DATAFORSEO_PASSWORD')
    
    # ============================================
    # Flask Configuration
    # ============================================
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG: bool = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_PORT: int = int(os.getenv('FLASK_PORT', 5000))
    FLASK_HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_SECRET_KEY: str = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # ============================================
    # API Security
    # ============================================
    N8N_API_KEY: Optional[str] = os.getenv('N8N_API_KEY')
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', 'http://localhost:5678')
    
    # ============================================
    # Rate Limiting
    # ============================================
    RATE_LIMIT_REDDIT: int = int(os.getenv('RATE_LIMIT_REDDIT', 30))
    RATE_LIMIT_WIKIPEDIA: int = int(os.getenv('RATE_LIMIT_WIKIPEDIA', 100))
    RATE_LIMIT_REVIEWS: int = int(os.getenv('RATE_LIMIT_REVIEWS', 10))
    
    # ============================================
    # Scraping Configuration
    # ============================================
    DEFAULT_DAYS_BACK: int = int(os.getenv('DEFAULT_DAYS_BACK', 180))
    MAX_REDDIT_RESULTS: int = int(os.getenv('MAX_REDDIT_RESULTS', 100))
    MAX_REVIEW_RESULTS: int = int(os.getenv('MAX_REVIEW_RESULTS', 50))
    
    # ============================================
    # Logging Configuration
    # ============================================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/aeo-audit.log')
    LOG_MAX_BYTES: int = int(os.getenv('LOG_MAX_BYTES', 10485760))
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # ============================================
    # Caching Configuration
    # ============================================
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB: int = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD')
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', 3600))
    
    # ============================================
    # Development Flags
    # ============================================
    SKIP_REDDIT: bool = os.getenv('SKIP_REDDIT', 'False').lower() == 'true'
    SKIP_REVIEWS: bool = os.getenv('SKIP_REVIEWS', 'False').lower() == 'true'
    SKIP_KNOWLEDGE: bool = os.getenv('SKIP_KNOWLEDGE', 'False').lower() == 'true'
    SKIP_AI_TESTING: bool = os.getenv('SKIP_AI_TESTING', 'False').lower() == 'true'
    USE_MOCK_DATA: bool = os.getenv('USE_MOCK_DATA', 'False').lower() == 'true'
    
    # ============================================
    # Production Settings
    # ============================================
    PRODUCTION: bool = os.getenv('PRODUCTION', 'False').lower() == 'true'
    MAX_CONCURRENT_AUDITS: int = int(os.getenv('MAX_CONCURRENT_AUDITS', 5))
    REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # ============================================
    # Report Generation
    # ============================================
    REPORT_OUTPUT_DIR: str = os.getenv('REPORT_OUTPUT_DIR', 'reports/')
    
    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate required configuration
        Returns list of missing required variables
        """
        missing = []
        
        # Check required Reddit credentials
        if not cls.REDDIT_CLIENT_ID:
            missing.append('REDDIT_CLIENT_ID')
        if not cls.REDDIT_CLIENT_SECRET:
            missing.append('REDDIT_CLIENT_SECRET')
        
        # Warn about optional but recommended
        warnings = []
        if not cls.GOOGLE_KG_API_KEY:
            warnings.append('GOOGLE_KG_API_KEY (optional but recommended)')
        if not cls.ANTHROPIC_API_KEY:
            warnings.append('ANTHROPIC_API_KEY (needed for Claude analysis)')
        
        if warnings:
            print(f"⚠️  Optional credentials missing: {', '.join(warnings)}")
        
        return missing
    
    @classmethod
    def get_cors_origins(cls) -> list[str]:
        """Get CORS origins as list"""
        return [origin.strip() for origin in cls.CORS_ORIGINS.split(',')]
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return cls.PRODUCTION or cls.FLASK_ENV == 'production'
    
    @classmethod
    def print_config(cls, hide_secrets: bool = True):
        """Print current configuration (for debugging)"""
        print("\n" + "="*50)
        print("🔧 AEO Audit System Configuration")
        print("="*50)
        
        def mask_secret(value: Optional[str]) -> str:
            if not value:
                return "❌ Not set"
            if hide_secrets and len(value) > 8:
                return f"✅ {value[:4]}...{value[-4:]}"
            return f"✅ {value}"
        
        print(f"\n📡 API Credentials:")
        print(f"  Reddit Client ID: {mask_secret(cls.REDDIT_CLIENT_ID)}")
        print(f"  Reddit Client Secret: {mask_secret(cls.REDDIT_CLIENT_SECRET)}")
        print(f"  Google KG API: {mask_secret(cls.GOOGLE_KG_API_KEY)}")
        print(f"  Anthropic API: {mask_secret(cls.ANTHROPIC_API_KEY)}")
        print(f"  OpenAI API: {mask_secret(cls.OPENAI_API_KEY)}")
        
        print(f"\n⚙️  Flask Settings:")
        print(f"  Environment: {cls.FLASK_ENV}")
        print(f"  Debug Mode: {cls.FLASK_DEBUG}")
        print(f"  Port: {cls.FLASK_PORT}")
        print(f"  Host: {cls.FLASK_HOST}")
        
        print(f"\n🔒 Security:")
        print(f"  N8N API Key: {mask_secret(cls.N8N_API_KEY)}")
        print(f"  CORS Origins: {cls.CORS_ORIGINS}")
        
        print(f"\n📊 Rate Limits:")
        print(f"  Reddit: {cls.RATE_LIMIT_REDDIT}/min")
        print(f"  Wikipedia: {cls.RATE_LIMIT_WIKIPEDIA}/min")
        print(f"  Reviews: {cls.RATE_LIMIT_REVIEWS}/min")
        
        print(f"\n🛠️  Development:")
        print(f"  Skip Reddit: {cls.SKIP_REDDIT}")
        print(f"  Skip Reviews: {cls.SKIP_REVIEWS}")
        print(f"  Skip Knowledge: {cls.SKIP_KNOWLEDGE}")
        print(f"  Use Mock Data: {cls.USE_MOCK_DATA}")
        
        print("="*50 + "\n")


# Create global config instance
config = Config()


# Validate on import (in development)
if not config.is_production():
    missing = config.validate()
    if missing:
        print(f"\n⚠️  Missing required environment variables: {', '.join(missing)}")
        print("Please check your .env file and config/.env.example\n")
