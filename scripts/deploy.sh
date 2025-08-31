#!/bin/bash

# ECOMSIMPLY Production Deployment Script
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting ECOMSIMPLY deployment for environment: $ENVIRONMENT"

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "❌ Error: .env file not found. Please copy .env.template to .env and fill in the values."
    exit 1
fi

# Load environment variables
source "$PROJECT_DIR/.env"

# Validate required environment variables
required_vars=("JWT_SECRET" "MONGO_ROOT_PASSWORD" "OPENAI_API_KEY" "STRIPE_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in .env file"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/ssl"
mkdir -p "$PROJECT_DIR/monitoring"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" down

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" pull

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d --build

# Wait for health checks
echo "⏳ Waiting for services to be healthy..."
timeout=300
counter=0

while [ $counter -lt $timeout ]; do
    if docker-compose -f "$PROJECT_DIR/docker-compose.yml" ps | grep -q "unhealthy"; then
        echo "⚠️ Some services are unhealthy, waiting..."
        sleep 10
        counter=$((counter + 10))
    else
        echo "✅ All services are healthy!"
        break
    fi
done

if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for services to be healthy"
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" logs
    exit 1
fi

# Run basic smoke test
echo "🧪 Running smoke tests..."
if curl -f http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
    exit 1
fi

if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Frontend health check passed"
else
    echo "❌ Frontend health check failed"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Service URLs:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8001"
echo "- API Health: http://localhost:8001/api/health"
echo "- Monitoring: http://localhost:3001 (Grafana)"
echo "- Metrics: http://localhost:9090 (Prometheus)"
echo ""
echo "📝 Next steps:"
echo "1. Configure your domain in nginx/sites/ecomsimply.conf"
echo "2. Add SSL certificates to ./ssl/ directory"
echo "3. Set up monitoring alerts in Grafana"
echo "4. Configure backup schedule"