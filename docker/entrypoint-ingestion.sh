#!/bin/bash
set -e

echo "📥 Document Ingestion Service - INPT RAG"
echo "========================================"

# Wait for Ollama if needed
if [ -n "$OLLAMA_BASE_URL" ]; then
    echo "⏳ Waiting for Ollama service..."
    max_retries=30
    counter=0
    
    while ! curl -s "$OLLAMA_BASE_URL/api/tags" > /dev/null; do
        counter=$((counter + 1))
        if [ $counter -gt $max_retries ]; then
            echo "⚠️  Ollama not available, continuing anyway..."
            break
        fi
        echo "  Attempt $counter/$max_retries..."
        sleep 2
    done
    
    if [ $counter -le $max_retries ]; then
        echo "✅ Ollama is ready!"
    fi
fi

# Check for documents
if [ -z "$(ls -A /app/data/documents 2>/dev/null)" ]; then
    echo "⚠️  No documents found in /app/data/documents"
    echo "💡 Mount your documents directory:"
    echo "   docker run -v /path/to/docs:/app/data/documents ..."
    exit 1
fi

# Count documents
doc_count=$(find /app/data/documents -type f \( -name "*.pdf" -o -name "*.txt" -o -name "*.md" -o -name "*.docx" \) | wc -l)
echo "📊 Found $doc_count documents to process"

# Initialize database if needed
if [ ! -d "/app/database/chroma_db" ] || [ -z "$(ls -A /app/database/chroma_db)" ]; then
    echo "🔧 Initializing database..."
    python scripts/setup_database.py || {
        echo "⚠️  Database initialization failed (non-blocking)"
    }
fi

echo ""
echo "🚀 Starting document ingestion..."
echo ""

# Execute the command
exec "$@"
