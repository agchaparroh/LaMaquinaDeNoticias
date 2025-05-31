# Rate Limiting and Politeness Policies Documentation

## Overview

This document describes the implementation of rate limiting and politeness policies in the La Máquina de Noticias scraper. These mechanisms ensure respectful crawling behavior and compliance with website policies.

## Components

### 1. AutoThrottle Configuration

AutoThrottle automatically adjusts download delays based on server response times.

**Settings in `scraper_core/settings.py`:**

```python
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5      # Initial delay in seconds
AUTOTHROTTLE_MAX_DELAY = 60       # Maximum delay in seconds
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0  # Target concurrent requests per server
AUTOTHROTTLE_DEBUG = False        # Set to True for detailed logging
```

**How it works:**
- Starts with a 5-second delay between requests
- Adjusts delay based on server response latency
- Keeps concurrency around 1.0 requests per server
- Never exceeds 60-second delay

### 2. Robots.txt Compliance

The scraper respects robots.txt directives by default.

**Configuration:**
```python
ROBOTSTXT_OBEY = True  # Enabled by default
```

**Features:**
- Automatically fetches and parses robots.txt for each domain
- Blocks requests to disallowed paths
- Caches robots.txt files to reduce requests
- Logs blocked requests for monitoring

### 3. Domain-Specific Rate Limits

Custom rate limits can be configured per domain in `config/rate_limits/domain_config.py`.

**Structure:**
```python
DOMAIN_RATE_LIMITS = {
    'example.com': {
        'concurrency': 2,      # Max concurrent requests
        'delay': 3.0,         # Seconds between requests
        'randomize_delay': True  # Add 0.5x-1.5x randomization
    }
}
```

**Categories:**
- **Default**: 2 concurrent requests, 2-second delay
- **Conservative**: 1 concurrent request, 5-second delay (for sensitive sites)
- **Aggressive**: 4 concurrent requests, 1-second delay (for robust sites)

### 4. Rate Limit Monitoring Middleware

Custom middleware (`RateLimitMonitorMiddleware`) provides enhanced monitoring:

**Features:**
- Tracks request timing per domain
- Logs warnings for requests that are too fast
- Monitors AutoThrottle adjustments
- Tracks failures and blocked requests
- Provides detailed statistics

**Usage:**
Add to `DOWNLOADER_MIDDLEWARES` in settings:
```python
'scraper_core.middlewares.rate_limit_monitor.RateLimitMonitorMiddleware': 543
```

## Testing

### Running Tests

Use the provided test script to verify rate limiting:

```bash
# Test with default URLs
python scripts/test_rate_limiting.py

# Test specific domains
python scripts/test_rate_limiting.py --domains bbc.com cnn.com

# Show current configuration
python scripts/test_rate_limiting.py --show-config
```

### What to Check

1. **Delay Verification**: Ensure delays match configuration
2. **Robots.txt**: Verify blocked URLs are properly handled
3. **AutoThrottle**: Check if delays adjust based on response times
4. **Concurrency**: Verify concurrent request limits are respected

## Best Practices

### 1. Setting Appropriate Delays

- **News Sites**: 2-4 seconds (they expect crawlers)
- **Small Sites**: 5+ seconds (be extra polite)
- **APIs**: Follow their rate limit documentation
- **Default**: 2 seconds with randomization

### 2. Monitoring and Adjustment

```python
# Enable debug logging for development
AUTOTHROTTLE_DEBUG = True
LOG_LEVEL = 'DEBUG'

# Monitor statistics
stats.get_value('rate_limit/requests/domain.com')
stats.get_value('robots_txt/blocked_total')
```

### 3. Handling Rate Limit Errors

Common HTTP codes indicating rate limiting:
- 429: Too Many Requests
- 503: Service Unavailable (sometimes used for rate limiting)

These are automatically retried by Scrapy's retry middleware.

## Configuration Examples

### Example 1: Conservative Crawling

```python
# For sensitive or small sites
AUTOTHROTTLE_START_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
CONCURRENT_REQUESTS_PER_DOMAIN = 1
```

### Example 2: Faster Crawling (with permission)

```python
# For sites that can handle more traffic
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
CONCURRENT_REQUESTS_PER_DOMAIN = 4
```

### Example 3: Domain-Specific Override

```python
from config.rate_limits.domain_config import update_domain_rate_limit

# Add custom configuration
update_domain_rate_limit('example.com', {
    'concurrency': 1,
    'delay': 10.0,
    'randomize_delay': True
})
```

## Troubleshooting

### Issue: Requests Too Fast

**Symptoms**: 429 errors, IP bans, timeouts

**Solutions**:
1. Increase `DOWNLOAD_DELAY`
2. Reduce `CONCURRENT_REQUESTS_PER_DOMAIN`
3. Enable `AUTOTHROTTLE_DEBUG` to see adjustments
4. Add domain to conservative rate limits

### Issue: Crawling Too Slow

**Symptoms**: Low throughput, long crawl times

**Solutions**:
1. Check if AutoThrottle is over-compensating
2. Increase `CONCURRENT_REQUESTS`
3. Reduce `AUTOTHROTTLE_START_DELAY`
4. Check network latency

### Issue: Robots.txt Blocking

**Symptoms**: Many "Forbidden by robots.txt" messages

**Solutions**:
1. Respect the robots.txt rules
2. Contact site owner for permission
3. Check if you're using the correct User-Agent
4. Verify robots.txt is being parsed correctly

## Monitoring Commands

```bash
# Check current spider settings
scrapy settings --get DOWNLOAD_DELAY
scrapy settings --get CONCURRENT_REQUESTS_PER_DOMAIN

# Test specific URL
scrapy fetch --nolog https://example.com

# Run spider with debug logging
scrapy crawl spider_name -L DEBUG -s AUTOTHROTTLE_DEBUG=True
```

## Production Recommendations

1. **Start Conservative**: Begin with longer delays and adjust based on monitoring
2. **Monitor Continuously**: Track 429 errors and response times
3. **Respect Robots.txt**: Never disable unless you have explicit permission
4. **Use User-Agent**: Identify your bot properly
5. **Handle Errors Gracefully**: Implement exponential backoff for failures

## Compliance

This implementation ensures compliance with:
- Robots Exclusion Protocol (robots.txt)
- HTTP rate limiting standards
- Common web scraping etiquette
- Legal requirements for respectful crawling

Always check and comply with website terms of service before scraping.
