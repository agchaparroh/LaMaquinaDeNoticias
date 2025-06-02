# Module Connector

Bridge between module_scraper and module_pipeline for "La Máquina de Noticias".

## Overview

This module monitors a directory for new `.json.gz` files containing articles, validates them, and sends them to the Pipeline API for processing.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

3. **Run the connector:**
   ```bash
   cd src
   python main.py
   ```

## Configuration

All configuration is done via environment variables. See `.env.example` for all available options.

## Directory Structure

```
module_connector/
├── src/
│   ├── main.py              # Entry point
│   ├── models.py            # Data models  
│   └── config.py            # Configuration
├── logs/                    # Log files
├── docs/                    # Documentation
├── requirements.txt         # Dependencies
└── .env.example             # Environment template
```

## Status

🎉 **COMPLETE** - Module Connector fully implemented and ready for deployment.

### 📊 Implementation Summary:
- ✅ **Core functionality**: File monitoring, processing, and API integration
- ✅ **Robust error handling**: Retries, validation, and graceful failures
- ✅ **Complete logging**: Structured logging with loguru
- ✅ **Full test suite**: Unit, integration, and Docker tests
- ✅ **Docker deployment**: Production-ready containerization
- ✅ **Documentation**: Comprehensive deployment and usage guides

### 🚀 Quick Start:
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Run with Docker Compose
docker-compose up --build

# 3. Monitor logs
docker-compose logs -f module-connector
```

### 📁 Key Files:
- `src/main.py` - Main application entry point
- `src/models.py` - Pydantic data models
- `src/config.py` - Configuration management
- `Dockerfile` - Production container configuration
- `docker-compose.yml` - Multi-service deployment
- `DEPLOYMENT.md` - Complete deployment guide
