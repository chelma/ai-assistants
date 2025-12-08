#!/usr/bin/env bash
#
# Initialize a specific Alto repository for development
#
# Usage:
#   scripts/init_repo.sh <repo-name>
#
# Arguments:
#   repo-name    Name of the repository (e.g., engine-partnerships, scriptdash)
#
# This script:
#   - Installs dependencies (bundle install)
#   - Generates protos (if bin/protos exists)
#   - Creates and migrates test database

set -e

# Check arguments
if [ $# -ne 1 ]; then
    echo "❌ Usage: $0 <repo-name>"
    echo "   Example: $0 engine-partnerships"
    exit 1
fi

REPO_NAME=$1

echo "🔧 Initializing repository: $REPO_NAME"
echo

# Check ALTO_WORKSPACE_REPO_ROOT is set
if [ -z "$ALTO_WORKSPACE_REPO_ROOT" ]; then
    echo "❌ ALTO_WORKSPACE_REPO_ROOT environment variable is not set"
    echo "   Run scripts/init_workspace.sh first"
    exit 1
fi

# Navigate to repository
REPO_DIR="$ALTO_WORKSPACE_REPO_ROOT/$REPO_NAME"
if [ ! -d "$REPO_DIR" ]; then
    echo "❌ Repository not found: $REPO_DIR"
    echo "   Available repositories:"
    ls -1 "$ALTO_WORKSPACE_REPO_ROOT" | grep -E "^(engine-|scriptdash)" | head -10
    exit 1
fi

cd "$REPO_DIR" || exit 1
echo "✅ Found repository at: $REPO_DIR"

# Install dependencies
echo
echo "📦 Installing dependencies (bundle install)..."
if bundle install; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    echo "   See claude/skills/better-boundaries/references/workspace-setup.md for troubleshooting"
    exit 1
fi

# Generate protos if bin/protos exists
echo
if [ -f "bin/protos" ]; then
    echo "🔨 Generating protos (bin/protos)..."
    if ./bin/protos; then
        echo "✅ Protos generated"

        # CRITICAL: Restore API file after generation (for engines)
        API_FILE="${REPO_NAME/engine-/}_api/lib/${REPO_NAME/engine-/}_api.rb"
        if [ -f "$API_FILE" ] && git ls-files --error-unmatch "$API_FILE" &>/dev/null; then
            echo "   Restoring $API_FILE from git..."
            git checkout "$API_FILE" 2>/dev/null || true
        fi
    else
        echo "⚠️  Proto generation had warnings (may be expected)"
    fi
else
    echo "ℹ️  No bin/protos found (skipping proto generation)"
fi

# Setup PostgreSQL test database
echo
echo "🗄️  Setting up test database..."

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running"
    echo "   Start PostgreSQL and try again"
    exit 1
fi
echo "✅ PostgreSQL is running"

# Create test database
echo "   Creating test database..."
if RAILS_ENV=test bin/rails db:create 2>&1 | grep -v "already exists"; then
    echo "✅ Test database created"
else
    echo "ℹ️  Test database already exists"
fi

# Run migrations
echo "   Running migrations..."
if bundle exec rails db:migrate RAILS_ENV=test 2>&1 | tail -5; then
    echo "✅ Migrations complete"
else
    echo "❌ Migrations failed"
    echo "   See claude/skills/better-boundaries/references/workspace-setup.md for troubleshooting"
    echo "   Or load the better-boundaries skill and ask for help"
    exit 1
fi

echo
echo "✅ Repository $REPO_NAME is ready for development!"
echo
echo "Next steps:"
echo "  - Run tests: cd $REPO_DIR && bundle exec rspec"
echo "  - Check types: cd $REPO_DIR && bundle exec srb tc"
echo "  - Or use: scripts/verify_repo.sh $REPO_NAME"
