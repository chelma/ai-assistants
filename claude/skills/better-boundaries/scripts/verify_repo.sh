#!/usr/bin/env bash
#
# Verify a repository is working correctly
#
# Usage:
#   scripts/verify_repo.sh <repo-name> [options]
#
# Arguments:
#   repo-name    Name of the repository (e.g., engine-partnerships, scriptdash)
#
# Options:
#   --sorbet     Run Sorbet type checking only
#   --tests      Run RSpec tests only
#   --all        Run both Sorbet and tests (default if no option specified)
#
# Examples:
#   scripts/verify_repo.sh engine-partnerships
#   scripts/verify_repo.sh scriptdash --sorbet
#   scripts/verify_repo.sh engine-partnerships --tests

set -e

# Default to running everything
RUN_SORBET=false
RUN_TESTS=false

# Check arguments
if [ $# -eq 0 ]; then
    echo "❌ Usage: $0 <repo-name> [--sorbet|--tests|--all]"
    echo "   Example: $0 engine-partnerships --all"
    exit 1
fi

REPO_NAME=$1
shift

# Parse options
if [ $# -eq 0 ]; then
    # No options provided, default to all
    RUN_SORBET=true
    RUN_TESTS=true
else
    while [[ $# -gt 0 ]]; do
      case $1 in
        --sorbet)
          RUN_SORBET=true
          shift
          ;;
        --tests)
          RUN_TESTS=true
          shift
          ;;
        --all)
          RUN_SORBET=true
          RUN_TESTS=true
          shift
          ;;
        *)
          echo "❌ Unknown option: $1"
          echo "   Valid options: --sorbet, --tests, --all"
          exit 1
          ;;
      esac
    done
fi

echo "🔍 Verifying repository: $REPO_NAME"
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
    exit 1
fi

cd "$REPO_DIR" || exit 1
echo "✅ Found repository at: $REPO_DIR"
echo

# Track overall success
OVERALL_SUCCESS=true

# Run Sorbet type checking
if [ "$RUN_SORBET" = true ]; then
    echo "📝 Running Sorbet type checking..."
    if bundle exec srb tc; then
        echo "✅ Sorbet: No errors!"
    else
        echo "❌ Sorbet: Type errors found"
        echo "   This may indicate the repository isn't properly initialized."
        echo "   Try: scripts/init_repo.sh $REPO_NAME"
        OVERALL_SUCCESS=false
    fi
    echo
fi

# Run tests
if [ "$RUN_TESTS" = true ]; then
    echo "🧪 Running RSpec tests..."
    echo "   (This may take several minutes for large codebases)"
    echo

    # Capture test output
    if bundle exec rspec 2>&1 | tee /tmp/rspec_output_$$.txt | tail -30; then
        echo
        echo "✅ Tests: All passing!"
    else
        EXIT_CODE=$?
        echo
        echo "❌ Tests: Some failures detected"
        echo "   Full output available in: /tmp/rspec_output_$$.txt"
        echo "   For detailed troubleshooting: claude/skills/better-boundaries/references/workspace-setup.md"
        OVERALL_SUCCESS=false
    fi
    echo
fi

# Final summary
echo "=========================================="
if [ "$OVERALL_SUCCESS" = true ]; then
    echo "✅ Verification complete: All checks passed!"
    echo "=========================================="
    exit 0
else
    echo "❌ Verification complete: Some checks failed"
    echo "=========================================="
    exit 1
fi
