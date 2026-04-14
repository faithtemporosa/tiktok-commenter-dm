#!/bin/bash
LOG_FILE="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/commenter_run.log"
OUTPUT_FILE="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/not_logged_in_browsers.txt"

echo "Tracking not-logged-in browsers..."
echo "Output: $OUTPUT_FILE"
echo ""
echo "Started tracking at $(date)" > "$OUTPUT_FILE"
echo "=========================" >> "$OUTPUT_FILE"

tail -f "$LOG_FILE" 2>/dev/null | while read line; do
    if echo "$line" | grep -qi "not logged in\|NOT LOGGED IN"; then
        # Extract browser name (tt followed by numbers)
        browser=$(echo "$line" | grep -oE 'tt[0-9]+' | head -1)
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        if [ -n "$browser" ]; then
            echo "$timestamp - $browser" >> "$OUTPUT_FILE"
            echo "Found: $browser (not logged in)"
        fi
    fi
done
