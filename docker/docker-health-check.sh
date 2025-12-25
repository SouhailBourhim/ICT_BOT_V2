#!/bin/bash
# Docker Health Check Script for INPT RAG Assistant

set -e

echo "🏥 Docker Health Check - INPT RAG Assistant"
echo "============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in the docker directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Please run this script from the docker directory${NC}"
    exit 1
fi

echo "1. Checking Docker Services..."
echo "------------------------------"

# Check if services are running
docker-compose ps > /tmp/docker_ps.txt 2>&1
if grep -q "Up" /tmp/docker_ps.txt; then
    print_status 0 "Docker services are running"
else
    print_status 1 "Docker services are not running"
    echo "Run: docker-compose up -d"
    exit 1
fi

echo ""
echo "2. Testing Service Health..."
echo "----------------------------"

# Test Ollama health
echo -n "Testing Ollama API... "
if curl -s -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_status 0 "Ollama API responding"
else
    print_status 1 "Ollama API not responding"
fi

# Test Streamlit health
echo -n "Testing Streamlit app... "
if curl -s -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    print_status 0 "Streamlit app responding"
else
    print_status 1 "Streamlit app not responding"
fi

# Test analytics page
echo -n "Testing analytics dashboard... "
if curl -s -I http://localhost:8501/analytics | grep -q "200 OK"; then
    print_status 0 "Analytics dashboard accessible"
else
    print_status 1 "Analytics dashboard not accessible"
fi

echo ""
echo "3. Checking Configuration..."
echo "----------------------------"

# Check configuration
docker-compose exec -T rag-app python -c "
from src.config.settings import validate_environment_configuration
results = validate_environment_configuration()
print(f'Environment: {results[\"environment_type\"]}')
print(f'Valid: {results[\"is_valid\"]}')
if results['errors']:
    print('Errors found:')
    for error in results['errors']:
        print(f'  - {error}')
    exit(1)
if results['warnings']:
    print('Warnings:')
    for warning in results['warnings']:
        print(f'  - {warning}')
" 2>/dev/null && print_status 0 "Configuration valid" || print_status 1 "Configuration issues found"

echo ""
echo "4. Checking Resources..."
echo "------------------------"

# Check disk space
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    print_status 0 "Disk space OK ($DISK_USAGE% used)"
else
    print_warning "Disk space low ($DISK_USAGE% used)"
fi

# Check memory usage
MEMORY_USAGE=$(docker stats --no-stream --format "table {{.MemPerc}}" | grep -v MEM | head -1 | sed 's/%//')
if [ ! -z "$MEMORY_USAGE" ] && [ "$MEMORY_USAGE" -lt 90 ]; then
    print_status 0 "Memory usage OK ($MEMORY_USAGE%)"
else
    print_warning "High memory usage ($MEMORY_USAGE%)"
fi

echo ""
echo "5. Testing Enhanced Features..."
echo "-------------------------------"

# Test math renderer
docker-compose exec -T rag-app python -c "
try:
    from app.components.math_renderer import MathRenderer
    print('Math renderer: OK')
except ImportError as e:
    print(f'Math renderer: FAILED - {e}')
    exit(1)
" 2>/dev/null && print_status 0 "Math renderer available" || print_status 1 "Math renderer not available"

# Test conversation manager
docker-compose exec -T rag-app python -c "
try:
    from src.conversation.manager import ConversationManager
    print('Conversation manager: OK')
except ImportError as e:
    print(f'Conversation manager: FAILED - {e}')
    exit(1)
" 2>/dev/null && print_status 0 "Conversation manager available" || print_status 1 "Conversation manager not available"

# Test document processing
docker-compose exec -T rag-app python -c "
try:
    from src.document_processing.contextual_header_generator import ContextualHeaderGenerator
    print('Document processing: OK')
except ImportError as e:
    print(f'Document processing: FAILED - {e}')
    exit(1)
" 2>/dev/null && print_status 0 "Document processing available" || print_status 1 "Document processing not available"

echo ""
echo "6. Database Status..."
echo "--------------------"

# Check ChromaDB
CHROMA_COUNT=$(docker-compose exec -T rag-app python -c "
try:
    from src.storage.vector_store import VectorStore
    store = VectorStore()
    collection = store.get_collection()
    print(collection.count())
except Exception as e:
    print('0')
" 2>/dev/null)

if [ "$CHROMA_COUNT" -gt 0 ]; then
    print_status 0 "ChromaDB has $CHROMA_COUNT documents"
else
    print_warning "ChromaDB is empty - run document ingestion"
fi

# Check conversations
CONV_COUNT=$(docker-compose exec -T rag-app find /app/data/conversations -name "*.json" 2>/dev/null | wc -l)
if [ "$CONV_COUNT" -gt 0 ]; then
    print_status 0 "Found $CONV_COUNT conversation files"
else
    print_warning "No conversation history found"
fi

echo ""
echo "============================================="
echo "Health check complete!"
echo ""
echo "📱 Access the app: http://localhost:8501"
echo "📊 Analytics: http://localhost:8501/analytics"
echo "🔍 Logs: docker-compose logs -f"
echo "📈 Stats: docker stats"
echo ""

# Cleanup
rm -f /tmp/docker_ps.txt

exit 0