#!/bin/bash
# Quick start script for Docker deployment

set -e

echo "🐳 INPT RAG Assistant - Docker Deployment"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Menu
echo "Select deployment mode:"
echo "1) Development (default)"
echo "2) Production"
echo "3) Document Ingestion Only"
echo "4) Stop All Services"
echo "5) Clean Everything (including volumes)"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting Development Environment..."
        docker-compose up -d
        echo ""
        echo "✅ Services started!"
        echo "📱 Access the app at: http://localhost:8501"
        echo "📊 View logs: docker-compose logs -f"
        ;;
    2)
        echo ""
        echo "🏭 Starting Production Environment..."
        docker-compose -f docker-compose.prod.yml up -d
        echo ""
        echo "✅ Services started!"
        echo "📱 Access the app at: http://localhost:8501"
        echo "📊 View logs: docker-compose -f docker-compose.prod.yml logs -f"
        ;;
    3)
        echo ""
        echo "📥 Starting Document Ingestion..."
        
        # Check if documents exist
        if [ -z "$(ls -A ../data/documents 2>/dev/null)" ]; then
            echo "⚠️  No documents found in ../data/documents"
            echo "Please add documents first!"
            exit 1
        fi
        
        docker-compose -f docker-compose.ingestion.yml up
        echo ""
        echo "✅ Ingestion complete!"
        ;;
    4)
        echo ""
        echo "🛑 Stopping all services..."
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
        docker-compose -f docker-compose.ingestion.yml down 2>/dev/null || true
        echo "✅ All services stopped!"
        ;;
    5)
        echo ""
        echo "🗑️  Cleaning everything (including volumes)..."
        read -p "Are you sure? This will delete all data! (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            docker-compose down -v 2>/dev/null || true
            docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
            docker-compose -f docker-compose.ingestion.yml down -v 2>/dev/null || true
            echo "✅ Everything cleaned!"
        else
            echo "❌ Cancelled"
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Done! 🎉"
