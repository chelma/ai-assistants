#!/usr/bin/env bash
#
# Initialize Alto workspace environment
#
# Usage:
#   scripts/init_workspace.sh [--sync]
#
# Options:
#   --sync    Optionally run 'alto up' to sync all repositories (default: skip)
#
# This script verifies that the Alto workspace is properly configured and
# optionally syncs all repositories to the latest state.

set -e

SYNC=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --sync)
      SYNC=true
      shift
      ;;
    *)
      echo "❌ Unknown option: $1"
      echo "Usage: $0 [--sync]"
      exit 1
      ;;
  esac
done

echo "🔍 Verifying Alto workspace setup..."
echo

# Check ALTO_WORKSPACE_REPO_ROOT is set
if [ -z "$ALTO_WORKSPACE_REPO_ROOT" ]; then
    echo "❌ ALTO_WORKSPACE_REPO_ROOT environment variable is not set"
    echo "   Please set it to your Alto workspace root directory"
    echo "   Example: export ALTO_WORKSPACE_REPO_ROOT=~/workspace/alto"
    exit 1
fi
echo "✅ ALTO_WORKSPACE_REPO_ROOT is set: $ALTO_WORKSPACE_REPO_ROOT"

# Check alto-workspace repository exists
ALTO_WORKSPACE_DIR="$ALTO_WORKSPACE_REPO_ROOT/alto-workspace"
if [ ! -d "$ALTO_WORKSPACE_DIR" ]; then
    echo "❌ alto-workspace repository not found at: $ALTO_WORKSPACE_DIR"
    echo "   Please clone the alto-workspace repository (git@github.com:scriptdash/alto-workspace.git)"
    exit 1
fi
echo "✅ alto-workspace repository found"

# Check PATH includes alto-workspace/bin
ALTO_BIN_DIR="$ALTO_WORKSPACE_DIR/bin"
if [[ ":$PATH:" != *":$ALTO_BIN_DIR:"* ]]; then
    echo "❌ $ALTO_BIN_DIR is not in PATH"
    echo "   Add this to your ~/.zshrc or ~/.bashrc:"
    echo "   export PATH=\"\$ALTO_WORKSPACE_REPO_ROOT/alto-workspace/bin:\$PATH\""
    exit 1
fi
echo "✅ alto-workspace/bin is in PATH"

# Check alto command is accessible
if ! command -v alto &> /dev/null; then
    echo "❌ 'alto' command not found"
    echo "   Make sure alto-workspace/bin is executable and in PATH"
    exit 1
fi
echo "✅ 'alto' command is accessible"

# Display alto version
ALTO_VERSION=$(alto --version 2>&1 || echo "unknown")
echo "   Version: $ALTO_VERSION"

# Optional sync
echo
if [ "$SYNC" = true ]; then
    echo "🔄 Running 'alto up' to sync all repositories..."
    echo "   ⚠️  This will rebase any branches that are behind origin/master"
    echo
    alto up
    echo "✅ Repository sync complete"
else
    echo "ℹ️  Skipping repository sync (use --sync flag to enable)"
    echo "   Note: 'alto up' will rebase any branches behind origin/master"
fi

echo
echo "✅ Alto workspace is ready!"
echo
echo "Next: Initialize a repository with scripts/init_repo.sh <repo-name>"
echo "      Example: scripts/init_repo.sh engine-partnerships"
