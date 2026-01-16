#!/bin/bash

# Start Langfuse Server
# Usage: ./scripts/start.sh

set -e

echo "Starting Langfuse server and PostgreSQL database..."
echo ""

# Check if docker-compose file exists
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found in current directory"
    echo "Please run this script from the budget_tracing root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "Please edit .env to add your actual NEXTAUTH_SECRET and SALT values"
    echo "(The pre-generated ones should work, but you can customize them)"
    echo ""
fi

# Start containers
docker-compose up -d

echo ""
echo "✓ Langfuse containers started!"
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if Langfuse is responding
echo ""
echo "Checking Langfuse health..."

for i in {1..30}; do
    if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
        echo "✓ Langfuse is ready!"
        break
    else
        echo "  Attempt $i/30: Waiting for Langfuse to start..."
        sleep 2
    fi
done

echo ""
echo "=================================================="
echo "Langfuse Server Started Successfully"
echo "=================================================="
echo ""
echo "Dashboard: http://localhost:3001"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3001 in your browser"
echo "2. Sign up with default credentials:"
echo "   Email: admin@budget.local"
echo "   Password: admin123"
echo "3. Create projects for budget_claude and budget_cursor"
echo "4. Generate API keys for each project"
echo "5. Add the keys to your .env file"
echo ""
echo "For detailed instructions, see README.md"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f langfuse"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
