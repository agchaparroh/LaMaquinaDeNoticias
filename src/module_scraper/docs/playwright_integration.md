# Playwright Integration Guide

## Overview

The scraper automatically uses Playwright for JavaScript-heavy websites when regular scraping fails. **You don't need to configure anything** - it works out of the box.

## How It Works

1. **Regular scraping** happens first (faster)
2. If content is **empty or insufficient**, automatically retries with **Playwright**
3. If Playwright fails, falls back to **regular scraping**

## When Playwright Is Used

Playwright automatically activates when:
- ✅ Page content is empty or very short (< 100 characters)
- ✅ Page shows "Loading..." or "Please enable JavaScript"
- ✅ Playwright requests encounter errors (retries with different settings)

## Configuration

### Basic Settings (.env file)
```bash
# Optional - adjust if needed
PLAYWRIGHT_MAX_RETRIES=2                    # How many times to retry failed Playwright requests
PLAYWRIGHT_TIMEOUT=30000                    # Timeout in milliseconds (30 seconds)
PLAYWRIGHT_ENABLE_FALLBACK=True             # Use regular scraping if Playwright fails
USE_PLAYWRIGHT_FOR_EMPTY_CONTENT=True       # Enable automatic empty content detection
```

### Advanced Settings (settings.py)
```python
# Usually you don't need to change these
PLAYWRIGHT_BROWSER_TYPE = "chromium"        # Browser type (chromium/firefox/webkit)
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,                        # Run browser in background
    "timeout": 30 * 1000,                   # Browser launch timeout
}
```

## Usage Examples

### Automatic (Recommended)
```python
from scraper_core.spiders.base.base_article import BaseArticleSpider

class MySpider(BaseArticleSpider):
    name = 'my_spider'
    start_urls = ['https://js-heavy-site.com/articles']
    
    # That's it! Playwright activates automatically when needed
```

### Manual Control
```python
def parse_special_page(self, response):
    # Force Playwright for this specific page
    meta = {'playwright': True}
    yield scrapy.Request(url, meta=meta, callback=self.parse_article)
```

## Troubleshooting

### Common Issues

**Problem**: "scrapy-playwright not available"
```bash
# Solution: Install missing dependency
pip install scrapy-playwright
playwright install chromium
```

**Problem**: High memory usage
```bash
# Solution: Reduce retries and timeout
PLAYWRIGHT_MAX_RETRIES=1
PLAYWRIGHT_TIMEOUT=20000
```

**Problem**: Too many fallbacks
```bash
# Solution: Check your selectors or disable fallback to see actual errors
PLAYWRIGHT_ENABLE_FALLBACK=False
```

**Problem**: Slow scraping
```bash
# Solution: Playwright only runs when regular scraping fails, but you can disable it
USE_PLAYWRIGHT_FOR_EMPTY_CONTENT=False
```

### Debug Mode

To see what Playwright is doing:
```python
# In your spider settings
LOG_LEVEL = 'DEBUG'

# Look for these log messages:
# "Empty content detected... Retrying with Playwright"
# "Playwright successfully recovered content"
# "Playwright error detected... Retry X/Y"
```

## Statistics

Monitor Playwright performance in your spider logs:
```
Playwright statistics - Empty content detections: 5, Retries: 3, Failures: 1, Successful recoveries: 4
```

## Best Practices

### ✅ Do:
- Let Playwright activate automatically
- Monitor the statistics to optimize settings
- Use BaseArticleSpider for automatic integration
- Test with problematic sites during development

### ❌ Don't:
- Force Playwright for all requests (it's slower)
- Set very high retry counts (causes delays)
- Disable fallback in production (causes lost data)
- Ignore the statistics (they help optimize performance)

## Performance Tips

1. **Regular scraping first**: Most sites work without JavaScript
2. **Smart detection**: Only uses Playwright when actually needed
3. **Fallback strategy**: Never completely fails, always gets something
4. **Resource management**: Automatic cleanup and timeout handling

## Need Help?

Check the logs! Playwright middleware provides detailed information about:
- When and why it activated
- What errors occurred
- How many retries were attempted
- Final success/failure status

The middleware is designed to **"just work"** with minimal configuration needed.
