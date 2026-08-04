#!/bin/bash
# update-version.sh - Updates version in backend config.py and frontend package.json
# Called by semantic-release during the prepare phase

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Error: Version argument is required"
    echo "Usage: ./update-version.sh <version>"
    exit 1
fi

echo "Updating version to $VERSION..."

# Update backend config.py
BACKEND_CONFIG="mvp1-cashier/backend/app/core/config.py"
if [ -f "$BACKEND_CONFIG" ]; then
    # Replace APP_VERSION = "x.x.x" with new version
    sed -i "s/APP_VERSION: str = \"[^\"]*\"/APP_VERSION: str = \"$VERSION\"/" "$BACKEND_CONFIG"
    echo "✅ Updated $BACKEND_CONFIG"
else
    echo "⚠️  Warning: $BACKEND_CONFIG not found"
fi

# Update frontend package.json
FRONTEND_PACKAGE="mvp1-cashier/frontend/package.json"
if [ -f "$FRONTEND_PACKAGE" ]; then
    # Use node/npm to update version properly (handles JSON correctly)
    if command -v node &> /dev/null; then
        node -e "
            const fs = require('fs');
            const pkg = JSON.parse(fs.readFileSync('$FRONTEND_PACKAGE', 'utf8'));
            pkg.version = '$VERSION';
            fs.writeFileSync('$FRONTEND_PACKAGE', JSON.stringify(pkg, null, 2) + '\\n');
        "
    else
        # Fallback to sed if node not available
        sed -i 's/"version": "[^"]*"/"version": "'$VERSION'"/' "$FRONTEND_PACKAGE"
    fi
    echo "✅ Updated $FRONTEND_PACKAGE"
else
    echo "⚠️  Warning: $FRONTEND_PACKAGE not found"
fi

echo "✅ Version updated to $VERSION successfully!"
