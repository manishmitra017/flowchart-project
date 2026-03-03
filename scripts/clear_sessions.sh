#!/usr/bin/env bash
#
# Clear all session and answer data for the flowchart agent.
# Run from the project root: ./scripts/clear_sessions.sh
#

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Clearing all flowchart agent sessions..."
echo ""

# 1. Remove answers database
ANSWERS_DB="$PROJECT_ROOT/flowchart_agent/database/answers.db"
if [ -f "$ANSWERS_DB" ]; then
    rm "$ANSWERS_DB"
    echo "  Removed: answers.db"
else
    echo "  Skipped: answers.db (not found)"
fi

# 2. Remove all ADK session databases (.adk/session.db scattered across subdirs)
COUNT=0
while IFS= read -r -d '' db_file; do
    rm "$db_file"
    # Also remove the parent .adk dir if it's now empty
    adk_dir="$(dirname "$db_file")"
    rmdir "$adk_dir" 2>/dev/null || true
    COUNT=$((COUNT + 1))
done < <(find "$PROJECT_ROOT" -path '*/.adk/session.db' -print0 2>/dev/null)

if [ "$COUNT" -gt 0 ]; then
    echo "  Removed: $COUNT ADK session database(s)"
else
    echo "  Skipped: No ADK session databases found"
fi

# 3. Remove ADK artifacts directory
ADK_ARTIFACTS="$PROJECT_ROOT/.adk/artifacts"
if [ -d "$ADK_ARTIFACTS" ]; then
    rm -rf "$ADK_ARTIFACTS"
    echo "  Removed: .adk/artifacts/"
else
    echo "  Skipped: .adk/artifacts/ (not found)"
fi

# 4. Clean Python cache in database module (stale _initialized flag)
PYCACHE="$PROJECT_ROOT/flowchart_agent/database/__pycache__"
if [ -d "$PYCACHE" ]; then
    rm -rf "$PYCACHE"
    echo "  Removed: database/__pycache__/"
fi

echo ""
echo "Done. All sessions cleared. Start fresh with: uv run adk web ."
