"""
Domain-specific rate limiting configuration for La Máquina de Noticias scraper.

This module defines custom download delays and concurrency settings for specific
domains to ensure polite crawling and compliance with website policies.

Usage:
    Import DOMAIN_RATE_LIMITS in your Scrapy settings and assign to DOWNLOAD_SLOTS.
"""

from typing import Dict, Any

# Default configuration for unknown domains
DEFAULT_RATE_LIMIT = {
    'concurrency': 2,
    'delay': 2.0,
    'randomize_delay': True
}

# Conservative configuration for high-traffic or sensitive sites
CONSERVATIVE_RATE_LIMIT = {
    'concurrency': 1,
    'delay': 5.0,
    'randomize_delay': True
}

# Aggressive configuration for sites known to handle high traffic well
AGGRESSIVE_RATE_LIMIT = {
    'concurrency': 4,
    'delay': 1.0,
    'randomize_delay': True
}

# Domain-specific rate limiting configurations
DOMAIN_RATE_LIMITS: Dict[str, Dict[str, Any]] = {
    # Major international news sites
    'cnn.com': {
        'concurrency': 1,
        'delay': 3.0,
        'randomize_delay': True
    },
    'bbc.com': {
        'concurrency': 2,
        'delay': 2.5,
        'randomize_delay': True
    },
    'nytimes.com': {
        'concurrency': 1,
        'delay': 4.0,
        'randomize_delay': True
    },
    'theguardian.com': {
        'concurrency': 2,
        'delay': 2.0,
        'randomize_delay': True
    },
    'reuters.com': {
        'concurrency': 2,
        'delay': 2.5,
        'randomize_delay': True
    },
    
    # Spanish news sites
    'elpais.com': {
        'concurrency': 2,
        'delay': 2.5,
        'randomize_delay': True
    },
    'elmundo.es': {
        'concurrency': 2,
        'delay': 2.5,
        'randomize_delay': True
    },
    'lavanguardia.com': {
        'concurrency': 2,
        'delay': 3.0,
        'randomize_delay': True
    },
    'abc.es': {
        'concurrency': 2,
        'delay': 2.5,
        'randomize_delay': True
    },
    
    # Latin American news sites
    'clarin.com': {
        'concurrency': 2,
        'delay': 2.0,
        'randomize_delay': True
    },
    'lanacion.com.ar': {
        'concurrency': 2,
        'delay': 2.5,
        'randomize_delay': True
    },
    'eluniversal.com.mx': {
        'concurrency': 2,
        'delay': 2.5,
        'randomize_delay': True
    },
    'eltiempo.com': {
        'concurrency': 2,
        'delay': 2.0,
        'randomize_delay': True
    },
    
    # Tech news sites (usually handle traffic better)
    'techcrunch.com': {
        'concurrency': 3,
        'delay': 1.5,
        'randomize_delay': True
    },
    'theverge.com': {
        'concurrency': 3,
        'delay': 1.5,
        'randomize_delay': True
    },
    'arstechnica.com': {
        'concurrency': 3,
        'delay': 1.5,
        'randomize_delay': True
    },
    
    # Sites with strict rate limits
    'wsj.com': CONSERVATIVE_RATE_LIMIT,
    'ft.com': CONSERVATIVE_RATE_LIMIT,
    'economist.com': CONSERVATIVE_RATE_LIMIT,
    
    # Add more domain configurations as needed
}

def get_domain_rate_limit(domain: str) -> Dict[str, Any]:
    """
    Get rate limit configuration for a specific domain.
    
    Args:
        domain: The domain to get configuration for
        
    Returns:
        Dictionary with rate limit configuration
    """
    return DOMAIN_RATE_LIMITS.get(domain, DEFAULT_RATE_LIMIT)

def update_domain_rate_limit(domain: str, config: Dict[str, Any]) -> None:
    """
    Update or add rate limit configuration for a domain.
    
    Args:
        domain: The domain to configure
        config: Dictionary with rate limit settings
    """
    DOMAIN_RATE_LIMITS[domain] = config

def apply_rate_limit_category(domain: str, category: str) -> None:
    """
    Apply a predefined rate limit category to a domain.
    
    Args:
        domain: The domain to configure
        category: One of 'default', 'conservative', or 'aggressive'
    """
    categories = {
        'default': DEFAULT_RATE_LIMIT,
        'conservative': CONSERVATIVE_RATE_LIMIT,
        'aggressive': AGGRESSIVE_RATE_LIMIT
    }
    
    if category in categories:
        DOMAIN_RATE_LIMITS[domain] = categories[category]
    else:
        raise ValueError(f"Unknown category: {category}. Use 'default', 'conservative', or 'aggressive'")
