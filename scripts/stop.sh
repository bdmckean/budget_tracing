#!/bin/bash

# Stop Langfuse Server
# Usage: ./scripts/stop.sh

set -e

echo "Stopping Langfuse server and PostgreSQL database..."
echo ""

# Check if docker-compose file exists
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found in current directory"
    echo "Please run this script from the budget_tracing root directory"
    exit 1
fi

# Stop containers (data persists in volumes)
docker-compose down

echo ""
echo "✓ Langfuse services stopped"
echo ""
echo "Note: Your data is preserved in Docker volumes"
echo ""
echo "To start again:"
echo "  ./scripts/start.sh"
echo ""
echo "To remove all data:"
echo "  docker-compose down -v"
echo ""
