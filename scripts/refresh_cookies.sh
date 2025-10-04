#!/bin/bash

# Cookie Refresh Script for whats-this-id
# This script opens a Chromium-based browser with a temporary user data directory to refresh cookies

echo "Opening browser for cookie refresh..."
echo "Main browser cache directory: $(pwd)/browser_cache"
echo ""

# Create temporary directory for cookie refresh
TEMP_BROWSER_DIR="$(pwd)/browser_cache_temp"
echo "Using temporary directory: $TEMP_BROWSER_DIR"

# Clean up any existing temp directory
if [ -d "$TEMP_BROWSER_DIR" ]; then
    echo "Cleaning up previous temporary directory..."
    rm -rf "$TEMP_BROWSER_DIR"
fi

# Function to find and launch a Chromium-based browser
launch_browser() {
    local browser_cmd=""
    local browser_name=""
    
    # Try different browser commands in order of preference
    # First, try to find Playwright's Chromium (same as used by crawl4ai)
    playwright_chromium=$(find "/Users/$USER/Library/Caches/ms-playwright" -name "Chromium" -path "*/chrome-mac/Chromium.app/Contents/MacOS/Chromium" 2>/dev/null | head -1)
    if [ -n "$playwright_chromium" ] && [ -f "$playwright_chromium" ]; then
        browser_cmd="$playwright_chromium"
        browser_name="Chromium (Playwright - same as crawl4ai)"
    else
        echo "❌ No Chromium-based browser found!"
        exit 1
    fi
    
    echo "Using $browser_name for cookie refresh..."
    echo ""
    echo "Please:"
    echo "1. Navigate to https://www.1001tracklists.com"
    echo "2. Complete any authentication/captcha if required"
    echo "3. Navigate to https://www.google.com"
    echo "4. Close the browser when done"
    echo ""
    
    # Launch the browser with the temporary directory
    "$browser_cmd" --user-data-dir="$TEMP_BROWSER_DIR" --no-first-run
    
    echo "✅ Cookie refresh completed!"
    echo "Copying refreshed cookies to main browser cache..."
    
    # Copy the refreshed cookies back to the main browser cache directory
    if [ -d "$TEMP_BROWSER_DIR/Default" ]; then
        # Ensure the main directory exists
        mkdir -p "$(pwd)/browser_cache/Default"
        
        # Copy cookies and related files
        if [ -f "$TEMP_BROWSER_DIR/Default/Cookies" ]; then
            cp "$TEMP_BROWSER_DIR/Default/Cookies" "$(pwd)/browser_cache/Default/"
            echo "  - Copied Cookies database"
        fi
        
        if [ -f "$TEMP_BROWSER_DIR/Default/Cookies-journal" ]; then
            cp "$TEMP_BROWSER_DIR/Default/Cookies-journal" "$(pwd)/browser_cache/Default/"
            echo "  - Copied Cookies journal"
        fi
        
        if [ -d "$TEMP_BROWSER_DIR/Default/Session Storage" ]; then
            cp -r "$TEMP_BROWSER_DIR/Default/Session Storage" "$(pwd)/browser_cache/Default/"
            echo "  - Copied Session Storage"
        fi
        
        if [ -d "$TEMP_BROWSER_DIR/Default/Local Storage" ]; then
            cp -r "$TEMP_BROWSER_DIR/Default/Local Storage" "$(pwd)/browser_cache/Default/"
            echo "  - Copied Local Storage"
        fi
        
        if [ -f "$TEMP_BROWSER_DIR/Default/Web Data" ]; then
            cp "$TEMP_BROWSER_DIR/Default/Web Data" "$(pwd)/browser_cache/Default/"
            echo "  - Copied Web Data"
        fi
        
        if [ -f "$TEMP_BROWSER_DIR/Default/Web Data-journal" ]; then
            cp "$TEMP_BROWSER_DIR/Default/Web Data-journal" "$(pwd)/browser_cache/Default/"
            echo "  - Copied Web Data journal"
        fi
    fi
    
    # Clean up temporary directory
    echo "Cleaning up temporary directory..."
    rm -rf "$TEMP_BROWSER_DIR"
    
    echo "✅ Cookie refresh and copy completed!"
    echo "You can now retry your search operations."
}

# Launch the browser
launch_browser
