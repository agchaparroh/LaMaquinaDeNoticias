# Playwright Documentation Index

## 📖 Documentation Overview

This directory contains comprehensive documentation for Playwright integration in the scraper module.

## 📚 Available Guides

### 🚀 Getting Started
- **[Playwright Integration Guide](playwright_integration.md)** - Complete user guide with examples
- **[Quick Reference](playwright_quickref.md)** - Cheat sheet for common tasks

### 🔧 Technical Documentation  
- **[Technical Documentation](playwright_technical.md)** - Advanced configuration and architecture
- **[Test Documentation](../tests/test_playwright/README.md)** - Testing guidelines and examples

## 🎯 Choose Your Guide

| I want to... | Read this |
|--------------|-----------|
| **Get started quickly** | [Quick Reference](playwright_quickref.md) |
| **Understand how it works** | [Integration Guide](playwright_integration.md) |
| **Configure advanced settings** | [Technical Documentation](playwright_technical.md) |
| **Run tests** | [Test Documentation](../tests/test_playwright/README.md) |
| **Troubleshoot problems** | [Integration Guide](playwright_integration.md#troubleshooting) |

## ⚡ TL;DR

Playwright **automatically activates** when regular scraping finds empty content. No configuration needed.

```python
from scraper_core.spiders.base.base_article import BaseArticleSpider

class MySpider(BaseArticleSpider):
    name = 'my_spider'
    start_urls = ['https://js-heavy-site.com']
    # That's it! Playwright works automatically
```

## 🛠️ Key Features

- ✅ **Automatic activation** when content is empty
- ✅ **Error recovery** with intelligent retry strategies  
- ✅ **Fallback mechanism** ensures data is never lost
- ✅ **Resource management** with cleanup and timeouts
- ✅ **Statistics and monitoring** for performance tracking
- ✅ **Production-ready** with Docker support

## 📞 Need Help?

1. Check the **[Quick Reference](playwright_quickref.md)** for common issues
2. Enable `LOG_LEVEL=DEBUG` to see what Playwright is doing
3. Look at **statistics** in your spider logs for performance insights
4. Review **[troubleshooting section](playwright_integration.md#troubleshooting)** for specific problems

The Playwright integration is designed to **"just work"** with minimal configuration needed.
