#!/bin/bash
# setup.sh - Make all scripts executable and verify setup

echo "🔧 Setting up nginx_reverse_proxy..."

# Make scripts executable
chmod +x deploy.sh
chmod +x integration.sh  
chmod +x health-check.sh

echo "✅ Scripts are now executable"

# Verify files exist
files=("nginx.conf" "Dockerfile" "docker-compose.yml" "Makefile" "README.md")
echo "🔍 Verifying required files..."

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - MISSING"
    fi
done

echo ""
echo "🚀 nginx_reverse_proxy setup completed!"
echo ""
echo "📋 Quick commands:"
echo "  ./deploy.sh     # Deploy standalone"
echo "  make help       # See all available commands"
echo "  make deploy     # Deploy with make"
echo "  make test       # Run health checks"
echo ""
echo "📖 Documentation:"
echo "  README.md       # Full documentation"
echo "  QUICK_START.md  # 2-minute setup guide"
