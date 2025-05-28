"""
Shared utilities for spider base classes

This module contains utility functions and constants used across
the different base spider classes.
"""

import re
from typing import List, Optional
from datetime import datetime
from urllib.parse import urlparse, urljoin


# Common user agents for rotation
USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    
    # Chrome on Mac
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    
    # Chrome on Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    
    # Firefox
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    
    # Safari
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    
    # Edge
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]


# Common news site URL patterns
NEWS_URL_PATTERNS = {
    'article': [
        r'/\d{4}/\d{2}/\d{2}/',  # Date-based URLs
        r'/article/',
        r'/articles/',
        r'/news/',
        r'/story/',
        r'/post/',
        r'/blog/',
        r'-\d+\.html$',  # Article ID patterns
        r'/p/[\w-]+',  # Permalink patterns
    ],
    'category': [
        r'/category/',
        r'/categories/',
        r'/section/',
        r'/sections/',
        r'/topic/',
        r'/tag/',
        r'/tags/',
    ],
    'archive': [
        r'/archive/',
        r'/archives/',
        r'/\d{4}/$',  # Year archives
        r'/\d{4}/\d{2}/$',  # Month archives
    ],
    'exclude': [
        r'/search',
        r'/login',
        r'/register',
        r'/signup',
        r'/signin',
        r'/logout',
        r'/admin',
        r'/wp-admin',
        r'/feed',
        r'/rss',
        r'/print/',
        r'\.pdf$',
        r'\.(jpg|jpeg|png|gif|webp|svg)$',
        r'\.(mp3|mp4|avi|mov)$',
        r'\.(zip|rar|gz|tar)$',
    ]
}


def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Parse a date string into a datetime object.
    
    Tries multiple common date formats used in news websites.
    
    Args:
        date_str: The date string to parse
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Clean the date string
    date_str = date_str.strip()
    
    # Common date formats in news sites
    date_formats = [
        '%Y-%m-%dT%H:%M:%S%z',  # ISO format with timezone
        '%Y-%m-%dT%H:%M:%SZ',   # ISO format with Z
        '%Y-%m-%dT%H:%M:%S',    # ISO format without timezone
        '%Y-%m-%d %H:%M:%S',    # Common database format
        '%Y-%m-%d',             # Simple date
        '%d/%m/%Y',             # European format
        '%m/%d/%Y',             # US format
        '%B %d, %Y',            # January 1, 2024
        '%b %d, %Y',            # Jan 1, 2024
        '%d %B %Y',             # 1 January 2024
        '%d %b %Y',             # 1 Jan 2024
        '%Y年%m月%d日',          # Asian format
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try dateutil parser as fallback
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except:
        pass
    
    return None


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ''
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove zero-width characters
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text.strip()


def extract_domain(url: str) -> str:
    """
    Extract the domain from a URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        The domain name
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ''


def is_valid_article_url(url: str, patterns: Optional[List[str]] = None) -> bool:
    """
    Check if a URL is likely to be an article.
    
    Args:
        url: The URL to check
        patterns: Optional list of additional patterns to check
        
    Returns:
        True if URL appears to be an article
    """
    if not url:
        return False
    
    # Check exclude patterns first
    for pattern in NEWS_URL_PATTERNS['exclude']:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    # Check article patterns
    all_patterns = NEWS_URL_PATTERNS['article']
    if patterns:
        all_patterns = all_patterns + patterns
    
    for pattern in all_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False


def normalize_url(url: str, base_url: str = None) -> str:
    """
    Normalize a URL by removing fragments, sorting query parameters, etc.
    
    Args:
        url: The URL to normalize
        base_url: Optional base URL for relative URLs
        
    Returns:
        Normalized URL
    """
    if base_url:
        url = urljoin(base_url, url)
    
    # Remove fragment
    if '#' in url:
        url = url.split('#')[0]
    
    # Remove trailing slash for consistency
    if url.endswith('/') and url.count('/') > 3:
        url = url.rstrip('/')
    
    # Remove common tracking parameters
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
    for param in tracking_params:
        url = re.sub(f'[?&]{param}=[^&]*', '', url)
    
    # Clean up multiple ? or &
    url = re.sub(r'[?&]+', '?', url, count=1)
    url = re.sub(r'[?&]+', '&', url)
    url = url.rstrip('?&')
    
    return url


def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Estimate reading time for an article.
    
    Args:
        text: The article text
        words_per_minute: Average reading speed
        
    Returns:
        Estimated reading time in minutes
    """
    if not text:
        return 0
    
    word_count = len(text.split())
    return max(1, round(word_count / words_per_minute))
