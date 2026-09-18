"""
Input Validation Module
Validates and sanitizes user inputs
"""

import re
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import json


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class AuditRequestValidator:
    """Validates audit request parameters"""
    
    @staticmethod
    def validate_brand_name(brand_name: str) -> str:
        """
        Validate brand name
        
        Args:
            brand_name: Brand name to validate
            
        Returns:
            Sanitized brand name
            
        Raises:
            ValidationError: If brand name is invalid
        """
        if not brand_name or not isinstance(brand_name, str):
            raise ValidationError("Brand name is required and must be a string")
        
        brand_name = brand_name.strip()
        
        if len(brand_name) < 2:
            raise ValidationError("Brand name must be at least 2 characters")
        
        if len(brand_name) > 100:
            raise ValidationError("Brand name must be less than 100 characters")
        
        # Check for suspicious patterns (basic XSS prevention)
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
        brand_name_lower = brand_name.lower()
        if any(pattern in brand_name_lower for pattern in dangerous_patterns):
            raise ValidationError("Brand name contains invalid characters")
        
        return brand_name
    
    @staticmethod
    def validate_domain(domain: Optional[str]) -> Optional[str]:
        """
        Validate domain name
        
        Args:
            domain: Domain to validate
            
        Returns:
            Sanitized domain or None
            
        Raises:
            ValidationError: If domain is invalid
        """
        if not domain:
            return None
        
        if not isinstance(domain, str):
            raise ValidationError("Domain must be a string")
        
        domain = domain.strip().lower()
        
        # Remove protocol if present
        domain = re.sub(r'^https?://', '', domain)
        # Remove trailing slash
        domain = domain.rstrip('/')
        # Remove www. prefix
        domain = re.sub(r'^www\.', '', domain)
        
        # Basic domain validation
        domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$'
        if not re.match(domain_pattern, domain):
            raise ValidationError(f"Invalid domain format: {domain}")
        
        return domain
    
    @staticmethod
    def validate_industry(industry: Optional[str]) -> Optional[str]:
        """
        Validate industry name
        
        Args:
            industry: Industry to validate
            
        Returns:
            Sanitized industry or None
        """
        if not industry:
            return None
        
        if not isinstance(industry, str):
            raise ValidationError("Industry must be a string")
        
        industry = industry.strip()
        
        if len(industry) > 100:
            raise ValidationError("Industry name must be less than 100 characters")
        
        return industry
    
    @staticmethod
    def validate_competitors(competitors: Optional[List[str]]) -> List[str]:
        """
        Validate competitor list
        
        Args:
            competitors: List of competitor names
            
        Returns:
            Sanitized list of competitors
            
        Raises:
            ValidationError: If competitors list is invalid
        """
        if not competitors:
            return []
        
        if not isinstance(competitors, list):
            raise ValidationError("Competitors must be a list")
        
        if len(competitors) > 10:
            raise ValidationError("Maximum 10 competitors allowed")
        
        validated = []
        for comp in competitors:
            if not isinstance(comp, str):
                continue
            
            comp = comp.strip()
            if comp and len(comp) <= 100:
                validated.append(comp)
        
        return validated
    
    @staticmethod
    def validate_audit_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete audit request
        
        Args:
            data: Request data dictionary
            
        Returns:
            Validated and sanitized data
            
        Raises:
            ValidationError: If request is invalid
        """
        validated = {}
        
        # Required fields
        validated['brand_name'] = AuditRequestValidator.validate_brand_name(
            data.get('brand_name', '')
        )
        
        # Optional fields
        validated['domain'] = AuditRequestValidator.validate_domain(
            data.get('domain')
        )
        
        validated['industry'] = AuditRequestValidator.validate_industry(
            data.get('industry')
        )
        
        validated['competitors'] = AuditRequestValidator.validate_competitors(
            data.get('competitors', [])
        )
        
        # Additional optional parameters
        if 'days_back' in data:
            try:
                days_back = int(data['days_back'])
                if days_back < 1 or days_back > 365:
                    raise ValidationError("days_back must be between 1 and 365")
                validated['days_back'] = days_back
            except (ValueError, TypeError):
                raise ValidationError("days_back must be an integer")
        
        if 'limit' in data:
            try:
                limit = int(data['limit'])
                if limit < 1 or limit > 500:
                    raise ValidationError("limit must be between 1 and 500")
                validated['limit'] = limit
            except (ValueError, TypeError):
                raise ValidationError("limit must be an integer")
        
        return validated


class URLValidator:
    """Validates URLs"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if URL is valid
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitize URL
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not URLValidator.is_valid_url(url):
            raise ValidationError(f"Invalid URL: {url}")
        
        # Basic XSS prevention
        if 'javascript:' in url.lower():
            raise ValidationError("Invalid URL scheme")
        
        return url


class JSONValidator:
    """Validates JSON data"""
    
    @staticmethod
    def validate_json_string(json_string: str) -> Dict:
        """
        Validate and parse JSON string
        
        Args:
            json_string: JSON string to validate
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            ValidationError: If JSON is invalid
        """
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {str(e)}")
    
    @staticmethod
    def validate_json_keys(data: Dict, required_keys: List[str]) -> None:
        """
        Validate that required keys exist in JSON
        
        Args:
            data: Dictionary to validate
            required_keys: List of required keys
            
        Raises:
            ValidationError: If required keys are missing
        """
        missing = [key for key in required_keys if key not in data]
        if missing:
            raise ValidationError(f"Missing required keys: {', '.join(missing)}")


class SubredditValidator:
    """Validates subreddit names"""
    
    @staticmethod
    def validate_subreddit(subreddit: str) -> str:
        """
        Validate subreddit name
        
        Args:
            subreddit: Subreddit name to validate
            
        Returns:
            Sanitized subreddit name
            
        Raises:
            ValidationError: If subreddit name is invalid
        """
        if not subreddit or not isinstance(subreddit, str):
            raise ValidationError("Subreddit name is required")
        
        # Remove r/ prefix if present
        subreddit = re.sub(r'^r/', '', subreddit.strip())
        
        # Subreddit name rules: 3-21 chars, alphanumeric + underscore
        if not re.match(r'^[a-zA-Z0-9_]{3,21}$', subreddit):
            raise ValidationError(f"Invalid subreddit name: {subreddit}")
        
        return subreddit
    
    @staticmethod
    def validate_subreddit_list(subreddits: List[str]) -> List[str]:
        """
        Validate list of subreddit names
        
        Args:
            subreddits: List of subreddit names
            
        Returns:
            List of validated subreddit names
        """
        if not subreddits:
            return []
        
        validated = []
        for sub in subreddits:
            try:
                validated_sub = SubredditValidator.validate_subreddit(sub)
                validated.append(validated_sub)
            except ValidationError:
                # Skip invalid subreddits
                continue
        
        return validated


# Helper function for quick validation
def validate_audit_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Quick validation function for audit requests
    
    Args:
        data: Request data
        
    Returns:
        Validated data
        
    Raises:
        ValidationError: If validation fails
    """
    return AuditRequestValidator.validate_audit_request(data)
