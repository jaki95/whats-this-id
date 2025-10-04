#!/bin/bash

# Cookie Wipe Script for whats-this-id
# This script completely clears the browser cache directory

echo "🧹 Wiping browser cache completely..."
echo "Browser cache directory: $(pwd)/browser_cache"
echo ""

# Check if browser cache directory exists
if [ ! -d "browser_cache" ]; then
    echo "❌ Browser cache directory not found!"
    echo "Creating fresh browser cache directory..."
    mkdir -p browser_cache
    echo "✅ Fresh browser cache directory created"
    exit 0
fi

# Remove everything in the browser cache directory
echo "Removing all contents of browser cache directory..."
rm -rf browser_cache/*
echo "✅ All browser cache contents removed"

echo ""
echo "✅ Browser cache wipe completed!"
echo ""
echo "Next steps:"
echo "1. Run ./refresh_cookies.sh to refresh your cookies"
echo "2. Retry your search operation"
