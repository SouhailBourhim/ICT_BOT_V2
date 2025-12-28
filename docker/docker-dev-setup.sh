#!/bin/bash
# Development Setup Script for INPT RAG Assistant

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 INPT RAG Assistant - Development Setup${NC}"
echo "=========================================="
echo ""

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Please run this script from the docker directory${NC}"
    exit 1
fi

echo "1. Setting up development environment..."
echo "--------------------------------------"

# Create development directories
print_info "Creating development directories..."
mkdir -p dev-models dev-config dev-logs
print_status 0 "Development directories created"

# Create development configuration
print_info "Creating development configuration..."
cat > dev-config/dev.env << EOF
# Development Environment Configuration
LOG_LEVEL=DEBUG
STREAMLIT_SERVER_RUNONFORK=true
STREAMLIT_BROWSER_GATHERSTATS=false
STREAMLIT_SERVER_FILEWATCH=true
STREAMLIT_SERVER_HEADLESS=false
STREAMLIT_GLOBAL_DEVELOPMENTMODE=true

# Development database settings
CHROMA_COLLECTION_NAME=inpt_smart_ict_docs_dev
SQLITE_DB_PATH=/app/database/metadata_dev.db

# Development performance settings
CACHE_ENABLED=false
ENABLE_TRACKING=false
ENABLE_METRICS=false

# Development debugging
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
EOF
print_status 0 "Development configuration created"

echo ""
echo "2. Building development Docker images..."
echo "---------------------------------------"

# Build development image
print_info "Building development Docker image..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --target development rag-app
print_status $? "Development image built"

echo ""
echo "3. Setting up development tools..."
echo "---------------------------------"

# Start development tools container
print_info "Starting development tools container..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools up -d dev-tools
print_status $? "Development tools container started"

echo ""
echo "4. Development environment ready!"
echo "--------------------------------"

echo -e "${GREEN}✅ Development setup complete!${NC}"
echo ""
echo "📋 Available development commands:"
echo "  • Start development stack:    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up"
echo "  • Start with tools:          docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools up"
echo "  • Start with DB admin:       docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile db-admin up"
echo "  • Run tests in container:    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec dev-tools pytest"
echo "  • Format code:               docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec dev-tools black ."
echo "  • Lint code:                 docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec dev-tools flake8 ."
echo ""
echo "🔗 Development URLs:"
echo "  • Main app:                  http://localhost:8501"
echo "  • Alternative port:          http://localhost:8502"
echo "  • Database admin:            http://localhost:8080 (if db-admin profile is used)"
echo "  • Debug port:                localhost:5678 (for debugpy)"
echo ""
echo "📁 Development volumes:"
echo "  • Source code:               Mounted for hot reload"
echo "  • Development models:        ./dev-models"
echo "  • Development config:        ./dev-config"
echo "  • Development logs:          ./dev-logs"
echo ""
echo "🐛 Debugging:"
echo "  • Attach debugger to port 5678"
echo "  • Use VS Code Python debugger with remote attach configuration"
echo "  • Logs available in ./dev-logs directory"
echo ""

exit 0