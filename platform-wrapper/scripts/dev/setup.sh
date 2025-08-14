#!/bin/bash

echo "🚀 Setting up Platform Wrapper development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Copy environment files
echo "📝 Setting up environment files..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env from example"
fi

if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.example frontend/.env.local
    echo "✅ Created frontend/.env.local from example"
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Install backend dependencies and run migrations
echo "🔧 Setting up backend..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
alembic upgrade head

# Seed database
echo "🌱 Seeding database..."
python -c "from database.seeds.initial_data import seed_database; seed_database()"

cd ..

# Install frontend dependencies
echo "🎨 Setting up frontend..."
cd frontend
npm install
cd ..

# Install shared package dependencies
echo "📦 Setting up shared package..."
cd shared
npm install
cd ..

echo "✅ Development environment setup complete!"
echo ""
echo "🎉 To start the development servers:"
echo "   Backend:  cd backend && uvicorn app.main:app --reload"
echo "   Frontend: cd frontend && npm run dev"
echo ""
echo "Or use Docker Compose:"
echo "   docker-compose up"