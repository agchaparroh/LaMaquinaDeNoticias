#!/bin/bash
set -e

echo "Building dashboard-review-frontend..."

# Build Docker image
docker build -t dashboard-review-frontend:latest .

echo "Build completed successfully!"