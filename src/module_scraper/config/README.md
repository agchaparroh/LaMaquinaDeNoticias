# Configuration Guide - Module Scraper

## Overview

This directory contains all configuration files for the module_scraper project. The configurations are organized by purpose and environment to maintain clarity and security.

## Configuration Files

### Environment Configuration

#### `.env.test.example`
Template file showing the structure and required environment variables for testing. Copy this file to create your own `.env.test` file.

**Required Variables:**
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Database Configuration (for direct PostgreSQL access)
PGHOST=your-host
PGPORT=5432
PGDATABASE=your-database
PGUSER=your-username
PGPASSWORD=your-password

# Scraper Settings
LOG_LEVEL=INFO
SUPABASE_STORAGE_BUCKET=your-bucket-name
```

#### `.env.test`
**DO NOT COMMIT THIS FILE**
Actual environment variables for testing. Create this file by copying `.env.test.example` and filling in your actual values.

## Environment Setup

### For Development
```bash
# Copy the example file
cp config/.env.test.example config/.env.test

# Edit with your actual values
# Use a separate Supabase project for testing - NEVER use production credentials
```

### For Production
Environment variables should be set directly in the production environment or through your deployment system. Do not store production credentials in files.

## Security Notes

1. **Never commit actual credentials** to version control
2. **Use separate projects for testing** - never test against production data
3. **Rotate credentials regularly** especially if they may have been exposed
4. **Use minimal permissions** - grant only the permissions needed for each environment

## Configuration Loading

The scraper loads configuration in this order:
1. Environment variables (highest priority)
2. `config/.env.test` file (for testing)
3. `config/.env` file (for local development)
4. Default values in `scraper_core/settings.py`

## Troubleshooting

### Common Issues

1. **"Supabase URL and Key not found"**
   - Ensure `config/.env.test` exists and contains valid values
   - Check that environment variables are set correctly

2. **"Connection failed"**
   - Verify Supabase project is active
   - Check network connectivity
   - Validate credentials

3. **"Permission denied"**
   - Verify the API key has the required permissions
   - For testing, ensure the service role key is used for admin operations

### Debugging Configuration

Enable debug logging to see which configuration values are being used:
```bash
export LOG_LEVEL=DEBUG
```

## Related Documentation

- [Testing Documentation](../tests/docs/README_tests.md)
- [Supabase Integration](../docs/architecture/pipelines_documentation.md)
- [Project Structure](../STRUCTURE.md)
