# Playwright Technical Documentation

## Architecture Overview

The Playwright integration consists of:
- **PlaywrightCustomDownloaderMiddleware**: Main middleware handling error detection and retries
- **BaseArticleSpider Integration**: Automatic empty content detection in spider
- **Configuration System**: Environment-based settings management
- **Statistics Collection**: Performance monitoring and debugging

## Configuration Reference

### Environment Variables
```bash
# Retry Configuration
PLAYWRIGHT_MAX_RETRIES=2                    # Maximum retries for Playwright errors
PLAYWRIGHT_MAX_EMPTY_RETRIES=1              # Maximum retries for empty content

# Timing Configuration  
PLAYWRIGHT_TIMEOUT=30000                    # Browser operation timeout (ms)

# Behavior Configuration
PLAYWRIGHT_ENABLE_FALLBACK=True             # Enable fallback to regular requests
USE_PLAYWRIGHT_FOR_EMPTY_CONTENT=True       # Enable empty content detection
```

### Advanced Settings (settings.py)
```python
# Browser Configuration
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30000,
    "args": ["--no-sandbox", "--disable-dev-shm-usage"]  # For Docker
}

# Context Options (applied per request)
PLAYWRIGHT_CONTEXT_OPTIONS = {
    "ignore_https_errors": True,
    "java_script_enabled": True,
}
```

## Error Handling Strategies

### Error Types and Recovery

| Error Type | Detection | Recovery Strategy |
|------------|-----------|-------------------|
| **Timeout** | Status 524, "timeout" in response | Increase timeout, retry with same config |
| **Navigation** | Status 502/503/504 + playwright headers | Clean retry, reset browser context |
| **Browser Error** | "playwright error", "browser context" | Clean config, remove custom methods |
| **Resource Limit** | "out of memory", "resource exhausted" | Lighter config, domcontentloaded only |

### Retry Configuration Per Error
```python
# Timeout Error - Increase timeout for retry
new_meta['playwright_page_methods'] = [
    {'method': 'set_default_timeout', 'args': [60000]},  # 60 seconds
]

# Resource Limit - Use lighter configuration
new_meta['playwright_page_coroutines'] = [
    {'method': 'wait_for_load_state', 'args': ['domcontentloaded']}
]

# Browser Error - Clean slate
# Removes all custom playwright_page_methods and playwright_page_coroutines
```

## Content Detection Logic

### Empty Content Criteria
Content is considered empty when:
1. **Response body is empty** or only whitespace
2. **Text content < 100 characters** after HTML stripping
3. **Contains loading indicators**: "loading...", "please enable javascript"
4. **Contains JS requirement messages**: "javascript required", "this page requires javascript"

### Detection Implementation
```python
def _is_content_empty(self, response, spider) -> bool:
    # 1. Check completely empty
    if not response.body.strip():
        return True
    
    # 2. Extract text content
    text_content = response.xpath('//text()').getall()
    text_content = ' '.join(text_content).strip()
    
    # 3. Check minimum length
    if len(text_content) < 100:
        return True
    
    # 4. Check for indicators
    text_lower = text_content.lower()
    indicators = ['loading...', 'please enable javascript', ...]
    return any(indicator in text_lower for indicator in indicators)
```

## Statistics and Monitoring

### Available Metrics
- `playwright/empty_content_detections`: Pages detected as needing JavaScript
- `playwright/retries`: Total retry attempts
- `playwright/failures`: Failed Playwright operations  
- `playwright/successful_recoveries`: Successfully recovered pages

### Accessing Statistics
```python
# In spider_closed method
def spider_closed(self, spider):
    stats = self.crawler.stats
    recoveries = stats.get_value('playwright/successful_recoveries', 0)
    failures = stats.get_value('playwright/failures', 0)
    
    if recoveries > 0:
        success_rate = recoveries / (recoveries + failures) * 100
        self.logger.info(f"Playwright success rate: {success_rate:.1f}%")
```

## Performance Optimization

### Memory Management
- Browser contexts are automatically cleaned up
- Fallback requests remove all Playwright metadata
- Failed requests don't accumulate browser resources

### CPU Optimization
- Regular scraping attempts first (faster)
- Playwright only used when content detection triggers
- Configurable retry limits prevent resource exhaustion

### Network Optimization  
- Smart retry strategies reduce unnecessary requests
- Fallback mechanism ensures data collection continues
- Domain-specific delays can be configured separately

## Production Deployment

### Docker Configuration
```dockerfile
FROM python:3.9-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Set production environment
ENV PLAYWRIGHT_MAX_RETRIES=2
ENV PLAYWRIGHT_TIMEOUT=30000
ENV PLAYWRIGHT_ENABLE_FALLBACK=True
```

### Resource Monitoring
```python
# Monitor resource usage in production
import psutil

def log_resource_usage(self):
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent()
    
    self.logger.info(f"Memory usage: {memory.percent}%, CPU: {cpu}%")
    
    if memory.percent > 80:
        self.logger.warning("High memory usage detected")
```

## Integration Patterns

### Custom Error Handling
```python
class MySpider(BaseArticleSpider):
    def parse_article(self, response):
        # Check for Playwright fallback
        if response.meta.get('playwright_fallback'):
            reason = response.meta.get('playwright_fallback_reason')
            self.logger.warning(f"Using fallback for {response.url}: {reason}")
        
        # Continue with normal processing
        return super().parse_article(response)
```

### Site-Specific Configuration
```python
def make_request(self, url, callback):
    meta = {}
    
    # Force Playwright for known problematic sites
    if 'heavy-js-site.com' in url:
        meta['playwright'] = True
        meta['playwright_page_coroutines'] = [
            {'method': 'wait_for_timeout', 'args': [5000]}  # Extra wait
        ]
    
    return Request(url, meta=meta, callback=callback)
```

## Troubleshooting Guide

### Common Issues

**High Memory Usage**
```bash
# Solution: Reduce retries and concurrent requests
PLAYWRIGHT_MAX_RETRIES=1
CONCURRENT_REQUESTS=2
```

**Frequent Timeouts**
```bash
# Solution: Increase timeout, but limit retries
PLAYWRIGHT_TIMEOUT=45000
PLAYWRIGHT_MAX_RETRIES=1
```

**Too Many Fallbacks**
```bash
# Solution: Debug actual errors
PLAYWRIGHT_ENABLE_FALLBACK=False
LOG_LEVEL=DEBUG
```

### Debug Information
Enable detailed logging to diagnose issues:
```python
import logging
logging.getLogger('scraper_core.middlewares.playwright_custom_middleware').setLevel(logging.DEBUG)
```

This will show:
- When empty content is detected
- Which error recovery strategy is applied
- Why fallbacks are triggered
- Statistics on success/failure rates

## Security Considerations

- Playwright runs in headless mode by default
- Browser contexts are isolated per request
- No persistent browser data is stored
- SSL certificate errors can be configured to be ignored
- Network access can be restricted through Playwright context options

The implementation prioritizes reliability and resource efficiency while maintaining the security posture appropriate for production web scraping operations.
