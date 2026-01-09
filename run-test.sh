#!/bin/bash

# Web Testing Agent - Quick Run Script
# Usage: ./run-test.sh "https://example.com" "Your test scenario"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./run-test.sh <URL> <SCENARIO>"
    echo ""
    echo "Example:"
    echo "  ./run-test.sh https://github.com \"Click on Explore and verify it loads\""
    echo ""
    echo "Or run with a file:"
    echo "  npm run dev test -- --file examples/example-google-search.json"
    exit 1
fi

URL="$1"
SCENARIO="$2"

echo "Running test..."
echo "URL: $URL"
echo "Scenario: $SCENARIO"
echo ""

npm run dev test -- --url "$URL" --scenario "$SCENARIO"
