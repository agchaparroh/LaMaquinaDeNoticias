# Playwright Quick Reference

## ⚡ Quick Start
```python
# Use BaseArticleSpider - Playwright works automatically
from scraper_core.spiders.base.base_article import BaseArticleSpider

class MySpider(BaseArticleSpider):
    name = 'my_spider'
    start_urls = ['https://example.com']
    # Done! No Playwright configuration needed
```

## 🔧 Environment Variables
```bash
# Optional tweaks in .env file
PLAYWRIGHT_MAX_RETRIES=2                 # Default: 2
PLAYWRIGHT_TIMEOUT=30000                 # Default: 30000 (30 seconds)
PLAYWRIGHT_ENABLE_FALLBACK=True          # Default: True
USE_PLAYWRIGHT_FOR_EMPTY_CONTENT=True    # Default: True
```

## 🎯 Force Playwright for Specific URL
```python
def parse_special(self, response):
    meta = {'playwright': True}
    yield Request(url, meta=meta, callback=self.parse_article)
```

## 📊 Check Statistics
Look for this in your spider logs:
```
Playwright statistics - Detections: 5, Retries: 3, Failures: 1, Recoveries: 4
```

## 🐛 Debug Issues
```python
# Enable debug logging
LOG_LEVEL = 'DEBUG'

# Look for these messages:
# "Empty content detected... Retrying with Playwright"
# "Playwright successfully recovered content"  
# "Playwright error detected... Retry X/Y"
```

## ⚠️ Common Problems

| Problem | Solution |
|---------|----------|
| "scrapy-playwright not available" | `pip install scrapy-playwright && playwright install chromium` |
| High memory usage | Reduce `PLAYWRIGHT_MAX_RETRIES=1` |
| Too slow | Set `USE_PLAYWRIGHT_FOR_EMPTY_CONTENT=False` |
| Many fallbacks | Check selectors or set `PLAYWRIGHT_ENABLE_FALLBACK=False` to see errors |

## ✅ It's Working When You See:
- Regular scraping happens first (fast)
- Empty pages automatically retry with Playwright
- Error pages get retried with different Playwright settings
- Final fallback to regular scraping if all fails
- Statistics show successful recoveries

**Remember**: Playwright only activates when needed. Most requests use regular, faster scraping.
