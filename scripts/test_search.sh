#!/bin/bash
#
# Bash wrapper for testing semantic search in Memories Bot
#
# Usage:
#   ./scripts/test_search.sh search "beach photos"
#   ./scripts/test_search.sh stats
#   ./scripts/test_search.sh similar 42
#   ./scripts/test_search.sh list --with-embeddings
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if running inside Docker or locally
if [ -f /.dockerenv ]; then
    # Inside Docker container
    PYTHON_CMD="python"
    CLI_SCRIPT="/app/scripts/cli_search.py"
else
    # Outside Docker - need to use docker compose exec
    PYTHON_CMD="docker compose -f docker-compose.local.yml exec backend python"
    CLI_SCRIPT="/app/scripts/cli_search.py"
fi

# Function to print usage
usage() {
    echo -e "${BLUE}Semantic Search Testing Tool${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 <command> [arguments]"
    echo ""
    echo "Commands:"
    echo "  search <query>              Search memories by semantic similarity"
    echo "  stats                       Show embedding statistics"
    echo "  similar <memory_id>         Find memories similar to a given one"
    echo "  list                        List memories (with optional filters)"
    echo "  test-queries <file>         Test multiple queries from file"
    echo "  backfill                    Generate embeddings for existing memories"
    echo ""
    echo "Examples:"
    echo "  $0 search \"beach sunset\""
    echo "  $0 search \"team dinner\" --event-id 1"
    echo "  $0 stats"
    echo "  $0 similar 42 --top-k 10"
    echo "  $0 list --with-embeddings"
    echo "  $0 backfill                 # Process all memories"
    echo "  $0 backfill --memory-id 1   # Process specific memory"
    echo "  $0 backfill --dry-run       # Preview what would be processed"
    echo ""
    echo "Options:"
    echo "  --event-id <id>           Filter by event ID"
    echo "  --top-k <n>               Number of results (default varies by command)"
    echo "  --threshold <0-1>         Minimum similarity threshold"
    echo "  --with-embeddings         Only show memories with embeddings"
    echo "  --without-embeddings      Only show memories without embeddings"
    echo ""
}

# Check if command provided
if [ $# -eq 0 ]; then
    usage
    exit 1
fi

# Check if Docker is needed and running
if [ ! -f /.dockerenv ]; then
    # Check if containers are running
    if ! docker compose -f "$PROJECT_ROOT/docker-compose.local.yml" ps | grep -q "backend.*Up"; then
        echo -e "${RED}Error: Backend container is not running${NC}"
        echo "Start it with: docker compose -f docker-compose.local.yml up -d"
        exit 1
    fi
fi

# Get command
COMMAND="$1"
shift

# Validate command
case "$COMMAND" in
    search|stats|similar|list|test-queries|backfill)
        # Valid commands
        ;;
    help|--help|-h)
        usage
        exit 0
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$COMMAND'${NC}"
        echo ""
        usage
        exit 1
        ;;
esac

# Build and run the Python CLI command
if [ -f /.dockerenv ]; then
    # Inside Docker
    $PYTHON_CMD $CLI_SCRIPT "$COMMAND" "$@"
else
    # Outside Docker
    docker compose -f "$PROJECT_ROOT/docker-compose.local.yml" exec -T backend python $CLI_SCRIPT "$COMMAND" "$@"
fi
