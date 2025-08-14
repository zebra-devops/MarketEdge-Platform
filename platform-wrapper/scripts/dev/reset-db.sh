#!/bin/bash

echo "🗑️ Resetting database..."

# Stop and remove database container
docker-compose stop postgres
docker-compose rm -f postgres

# Remove database volume
docker volume rm platform-wrapper_postgres_data 2>/dev/null || true

# Start database again
docker-compose up -d postgres

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🗄️ Running database migrations..."
cd backend
source venv/bin/activate 2>/dev/null || true
alembic upgrade head

# Seed database
echo "🌱 Seeding database..."
python -c "from database.seeds.initial_data import seed_database; seed_database()"

cd ..

echo "✅ Database reset complete!"