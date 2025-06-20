#!/bin/bash
set -e

ENV=${1:-production}
PORT=${2:-8080}

echo "Deploying dashboard-review-frontend to $ENV environment on port $PORT..."

# Stop existing container if running
docker stop dashboard-review-frontend 2>/dev/null || true
docker rm dashboard-review-frontend 2>/dev/null || true

# Run new container
docker run -d \
  --name dashboard-review-frontend \
  -p $PORT:80 \
  -e NODE_ENV=$ENV \
  dashboard-review-frontend:latest

echo "Deployment completed successfully! Application is running at http://localhost:$PORT"