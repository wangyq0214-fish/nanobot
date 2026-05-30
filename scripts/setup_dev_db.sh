#!/bin/bash
# Setup development database for nanobot
# Usage: ./scripts/setup_dev_db.sh

set -e

echo "Setting up development database..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Start PostgreSQL
echo "Starting PostgreSQL..."
docker-compose -f docker-compose.dev.yml up -d postgres

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Check if PostgreSQL is ready
until docker exec nanobot-postgres pg_isready -U nanobot -d nanobot > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

echo "✓ PostgreSQL is ready"

# Run database migration
echo "Running database migration..."
cd "$(dirname "$0")/.."
python -m nanobot.cli.commands migrate-db run

echo ""
echo "✓ Development database setup complete!"
echo ""
echo "Connection details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: nanobot"
echo "  User: nanobot"
echo "  Password: nanobot"
echo ""
echo "Connection URL: postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"
echo ""
echo "To start pgAdmin (optional):"
echo "  docker-compose -f docker-compose.dev.yml --profile admin up -d"
echo "  Open http://localhost:5050"
echo "  Email: admin@nanobot.local"
echo "  Password: admin"
