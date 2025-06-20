#!/bin/bash

# Script to run tests for dashboard review frontend module

echo "🧪 Running tests for Dashboard Review Frontend..."
echo "============================================"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run tests with coverage
echo ""
echo "🏃 Running test suite..."
npm run test:coverage

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed successfully!"
    echo ""
    echo "📊 Coverage report has been generated in ./coverage"
else
    echo ""
    echo "❌ Some tests failed. Please check the output above."
    exit 1
fi
