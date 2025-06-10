# Module Connector Deployment Guide

## Overview

The Module Connector is a containerized service that bridges the `module_scraper` and `module_pipeline` components of "La Máquina de Noticias" system.

## Quick Start

### 1. Local Development with Docker Compose

```bash
# Clone the repository and navigate to module_connector
cd module_connector

# Copy environment template
cp .env.example .env

# Edit .env with your specific configuration
nano .env

# Start the services
docker-compose up --build

# View logs
docker-compose logs -f module-connector
```

### 2. Production Deployment

#### Build the Docker Image

```bash
docker build -t module-connector:latest .
```

#### Run with Docker

```bash
# Create data directories
mkdir -p ./data/{scrapy_output/pending,pipeline_input/{pending,completed,error}}

# Run the container
docker run -d \
  --name module-connector \
  --restart unless-stopped \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/app/logs \
  -e PIPELINE_API_URL=http://your-pipeline-url:8001 \
  -e SCRAPER_OUTPUT_DIR=/data/scrapy_output/pending \
  -e PIPELINE_PENDING_DIR=/data/pipeline_input/pending \
  -e PIPELINE_COMPLETED_DIR=/data/pipeline_input/completed \
  -e PIPELINE_ERROR_DIR=/data/pipeline_input/error \
  module-connector:latest
```

#### Run with Docker Compose (Recommended)

```bash
# Production configuration
docker-compose --profile production up -d
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SCRAPER_OUTPUT_DIR` | Directory where scraper outputs files | `/data/scrapy_output/pending` |
| `PIPELINE_PENDING_DIR` | Directory for pending files | `/data/pipeline_input/pending` |
| `PIPELINE_COMPLETED_DIR` | Directory for completed files | `/data/pipeline_input/completed` |
| `PIPELINE_ERROR_DIR` | Directory for error files | `/data/pipeline_input/error` |
| `PIPELINE_API_URL` | URL of the Pipeline API | `http://module-pipeline:8001` |
| `POLLING_INTERVAL` | Interval in seconds for directory polling | `5` |
| `MAX_RETRIES` | Maximum number of retries for API calls | `3` |
| `RETRY_BACKOFF` | Base delay in seconds between retries | `2.0` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `ENABLE_SENTRY` | Enable Sentry error reporting | `false` |
| `SENTRY_DSN` | Sentry DSN for error reporting | `` |

### Volume Mounts

The container requires the following volume mounts:

- `/data` - Main data directory containing all subdirectories
- `/app/logs` - Log files output directory (optional)

### Directory Structure

```
data/
├── scrapy_output/
│   └── pending/          # Input: Files from module_scraper
└── pipeline_input/
    ├── pending/          # Working: Files being processed
    ├── completed/        # Output: Successfully processed files
    └── error/           # Output: Failed files
```

## Monitoring

### Health Checks

The container includes a built-in health check that verifies directory accessibility:

```bash
# Check container health
docker ps

# Manual health check
docker exec module-connector python -c "import os; exit(0 if os.path.exists('/data/pipeline_input/pending') else 1)"
```

### Logs

```bash
# View real-time logs
docker logs -f module-connector

# View logs from file (if volume mounted)
tail -f ./logs/connector.log
```

### Metrics

Monitor these key metrics:

- Files processed per minute
- API success/failure rate
- Directory sizes
- Container restart count

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   ```bash
   # Fix directory permissions
   sudo chown -R 1000:1000 ./data ./logs
   ```

2. **Pipeline API Connection Failed**
   - Verify `PIPELINE_API_URL` is correct
   - Check network connectivity between containers
   - Ensure Pipeline API is running

3. **No Files Being Processed**
   - Check if files exist in `SCRAPER_OUTPUT_DIR`
   - Verify file permissions
   - Check logs for error messages

4. **High Memory Usage**
   - Monitor for large files
   - Check for stuck processing loops
   - Consider increasing `POLLING_INTERVAL`

### Debug Mode

Run with debug logging:

```bash
docker run -e LOG_LEVEL=DEBUG module-connector:latest
```

## Integration

### With Module Scraper

The Module Scraper should output `.json.gz` files to the directory mounted as `SCRAPER_OUTPUT_DIR`.

### With Module Pipeline

The Module Pipeline should expose a `/procesar` endpoint that accepts POST requests with article data.

Expected API contract:
- **Endpoint**: `POST /procesar`
- **Content-Type**: `application/json`
- **Body**: `{"articulo": {...}}`
- **Success Response**: `202 Accepted`
- **Error Responses**: `400 Bad Request`, `500 Internal Server Error`, `503 Service Unavailable`

## Development

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_models.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Demo

```bash
# Run demo script
python demo.py
```

## Security

- Container runs as non-root user
- No ports exposed (worker service)
- Environment variables for sensitive configuration
- Optional Sentry integration for error monitoring

## Maintenance

### Updates

```bash
# Pull latest image
docker pull module-connector:latest

# Restart with new image
docker-compose down
docker-compose up -d
```

### Backup

Important directories to backup:
- `./data/pipeline_input/completed/` - Successfully processed files
- `./logs/` - Historical logs
- `.env` - Configuration

### Cleanup

```bash
# Remove old log files (older than 30 days)
find ./logs -name "*.log*" -mtime +30 -delete

# Clean completed files (older than 90 days)
find ./data/pipeline_input/completed -name "*.json.gz" -mtime +90 -delete
```

## Support

For issues and questions:

1. Check the logs first: `docker logs module-connector`
2. Verify configuration: `docker exec module-connector env | grep -E "(PIPELINE|SCRAPER)"`
3. Test connectivity: `docker exec module-connector wget -O- http://module-pipeline:8001/health`

## License

[Add your license information here]
