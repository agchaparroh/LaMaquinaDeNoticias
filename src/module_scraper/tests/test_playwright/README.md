# Playwright Tests

## Overview

Simple tests to verify Playwright middleware functionality works correctly.

## Running Tests

```bash
# Run all Playwright tests
python scripts/run_playwright_tests.py

# Run specific test file
python -m pytest tests/test_playwright/test_playwright_basic.py -v

# Run with coverage
python -m pytest tests/test_playwright/ --cov=scraper_core.middlewares.playwright_custom_middleware
```

## Test Coverage

The tests verify:

- ✅ **Empty content detection** - Pages requiring JavaScript are identified
- ✅ **Playwright error detection** - Timeout, browser, and resource errors
- ✅ **Retry mechanism** - Failed requests are retried with appropriate configuration
- ✅ **Fallback behavior** - Non-Playwright requests when all retries fail
- ✅ **Configuration** - Settings are properly applied
- ✅ **Passthrough** - Normal responses work unchanged

## Test Structure

- `test_playwright_basic.py` - Core functionality tests
- `run_playwright_tests.py` - Test runner script

## Notes

These tests focus on **practical verification** rather than exhaustive coverage. They ensure the middleware works correctly in real scenarios without over-engineering.
