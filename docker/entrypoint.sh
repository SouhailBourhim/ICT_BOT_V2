#!/bin/bash
set -e

# Configuration and logging functions
log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_warn() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

log_success() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1"
}

# Validate required environment variables
validate_configuration() {
    log_info "🔍 Validating configuration..."
    
    local required_vars=(
        "OLLAMA_BASE_URL"
        "OLLAMA_MODEL"
        "PROJECT_NAME"
        "LOG_LEVEL"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        log_error "Please check your docker-compose.yml configuration"
        exit 1
    fi
    
    # Validate LOG_LEVEL
    local log_level_upper=$(echo "${LOG_LEVEL}" | tr '[:lower:]' '[:upper:]')
    case "$log_level_upper" in
        DEBUG|INFO|WARNING|ERROR|CRITICAL)
            log_success "Configuration validation passed"
            ;;
        *)
            log_warn "Invalid LOG_LEVEL '$LOG_LEVEL', defaulting to INFO"
            export LOG_LEVEL="INFO"
            ;;
    esac
}

# Enhanced Ollama service checking with exponential backoff
wait_for_ollama() {
    log_info "⏳ Waiting for Ollama service..."
    
    local max_retries=30
    local counter=0
    local backoff=1
    local max_backoff=8
    
    # Extract host and port from OLLAMA_BASE_URL
    local ollama_host=$(echo "$OLLAMA_BASE_URL" | sed 's|http://||' | sed 's|https://||' | cut -d':' -f1)
    local ollama_port=$(echo "$OLLAMA_BASE_URL" | sed 's|http://||' | sed 's|https://||' | cut -d':' -f2)
    
    # Default port if not specified
    if [ "$ollama_port" = "$ollama_host" ]; then
        ollama_port="11434"
    fi
    
    log_info "Checking Ollama at $ollama_host:$ollama_port"
    
    while ! curl -s --connect-timeout 5 --max-time 10 "$OLLAMA_BASE_URL/api/tags" > /dev/null; do
        counter=$((counter + 1))
        
        if [ $counter -gt $max_retries ]; then
            log_error "Failed to connect to Ollama after $max_retries attempts"
            log_error "Please ensure Ollama service is running and accessible at $OLLAMA_BASE_URL"
            exit 1
        fi
        
        log_info "Attempt $counter/$max_retries - Ollama not ready, waiting ${backoff}s..."
        sleep $backoff
        
        # Exponential backoff with maximum
        if [ $backoff -lt $max_backoff ]; then
            backoff=$((backoff * 2))
        fi
    done
    
    log_success "Ollama service is ready!"
}

# Comprehensive model management
manage_ollama_model() {
    log_info "🔍 Checking LLM model availability..."
    
    # Check if model exists
    local model_check_response
    model_check_response=$(curl -s "$OLLAMA_BASE_URL/api/tags" || echo "")
    
    if [ -z "$model_check_response" ]; then
        log_error "Failed to query Ollama models"
        exit 1
    fi
    
    if echo "$model_check_response" | grep -q "\"name\":\"$OLLAMA_MODEL\""; then
        log_success "Model $OLLAMA_MODEL is already available"
        return 0
    fi
    
    log_warn "Model $OLLAMA_MODEL not found"
    log_info "📥 Downloading model (this may take several minutes)..."
    
    # Start model download with progress monitoring
    local pull_response
    pull_response=$(curl -s -X POST "$OLLAMA_BASE_URL/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$OLLAMA_MODEL\"}" || echo "")
    
    if [ -z "$pull_response" ]; then
        log_error "Failed to initiate model download"
        exit 1
    fi
    
    # Wait for model to be available (with timeout)
    local model_wait_counter=0
    local model_max_wait=60  # 10 minutes with 10s intervals
    
    while [ $model_wait_counter -lt $model_max_wait ]; do
        model_check_response=$(curl -s "$OLLAMA_BASE_URL/api/tags" || echo "")
        
        if echo "$model_check_response" | grep -q "\"name\":\"$OLLAMA_MODEL\""; then
            log_success "Model $OLLAMA_MODEL downloaded successfully!"
            return 0
        fi
        
        model_wait_counter=$((model_wait_counter + 1))
        log_info "Waiting for model download... ($model_wait_counter/$model_max_wait)"
        sleep 10
    done
    
    log_error "Model download timeout - please check Ollama logs"
    exit 1
}

# Enhanced directory initialization with proper error handling
initialize_directories() {
    log_info "📁 Initializing application directories..."
    
    # Use Python to initialize directories with proper error handling
    python3 -c "
import sys
import traceback
try:
    from src.config.settings import setup_directories, settings
    setup_directories()
    print(f'Directories initialized successfully in: {settings.BASE_DIR}')
except ImportError as e:
    print(f'Import error: {e}', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'Directory initialization failed: {e}', file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
" || {
        log_error "Failed to initialize directories using settings"
        log_info "Attempting manual directory creation..."
        
        # Fallback manual directory creation
        local directories=(
            "/app/data"
            "/app/data/documents"
            "/app/data/processed"
            "/app/data/conversations"
            "/app/data/embeddings"
            "/app/database"
            "/app/database/chroma_db"
            "/app/logs"
        )
        
        for dir in "${directories[@]}"; do
            if ! mkdir -p "$dir"; then
                log_error "Failed to create directory: $dir"
                exit 1
            fi
        done
        
        log_success "Manual directory creation completed"
    }
}

# Database and application state validation
validate_application_state() {
    log_info "🔍 Validating application state..."
    
    # Check ChromaDB directory
    if [ ! -d "/app/database/chroma_db" ]; then
        log_warn "ChromaDB directory not found, creating..."
        mkdir -p "/app/database/chroma_db"
    fi
    
    if [ -z "$(ls -A /app/database/chroma_db 2>/dev/null)" ]; then
        log_warn "ChromaDB database is empty"
        log_info "💡 To add documents, run:"
        log_info "   docker-compose exec rag-app python scripts/ingest_documents.py data/documents"
    else
        log_success "ChromaDB database found with existing data"
    fi
    
    # Check if required Python packages are available
    log_info "Validating Python dependencies..."
    python3 -c "
import sys
required_modules = [
    'streamlit', 'chromadb', 'sentence_transformers', 
    'pydantic', 'pydantic_settings', 'requests'
]
missing = []
for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    print(f'Missing required modules: {missing}', file=sys.stderr)
    sys.exit(1)
else:
    print('All required Python dependencies are available')
" || {
        log_error "Missing required Python dependencies"
        exit 1
    }
    
    log_success "Application state validation completed"
}

# Display comprehensive configuration information
display_configuration() {
    log_info "📊 System Configuration:"
    echo "  ┌─────────────────────────────────────────────────────────────"
    echo "  │ Project: ${PROJECT_NAME:-'INPT RAG Assistant'}"
    echo "  │ Version: ${VERSION:-'1.0.0'}"
    echo "  │ Language: ${LANGUAGE:-'fr'}"
    echo "  ├─────────────────────────────────────────────────────────────"
    echo "  │ LLM Model: $OLLAMA_MODEL"
    echo "  │ Ollama URL: $OLLAMA_BASE_URL"
    echo "  │ Streamlit Port: 8501"
    echo "  │ Log Level: $LOG_LEVEL"
    echo "  ├─────────────────────────────────────────────────────────────"
    echo "  │ Embedding Model: ${EMBEDDING_MODEL:-'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'}"
    echo "  │ Chunk Size: ${CHUNK_SIZE:-'1000'}"
    echo "  │ Top-K Retrieval: ${TOP_K_RETRIEVAL:-'7'}"
    echo "  │ Analytics: ${ENABLE_TRACKING:-'true'}"
    echo "  └─────────────────────────────────────────────────────────────"
}

# Graceful shutdown handler
cleanup() {
    log_info "🛑 Received shutdown signal, cleaning up..."
    # Add any cleanup tasks here
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main initialization sequence
main() {
    log_info "🚀 Starting INPT RAG Assistant initialization..."
    
    # Step 1: Validate configuration
    validate_configuration
    
    # Step 2: Wait for Ollama service
    wait_for_ollama
    
    # Step 3: Manage Ollama model
    manage_ollama_model
    
    # Step 4: Initialize directories
    initialize_directories
    
    # Step 5: Validate application state
    validate_application_state
    
    # Step 6: Display configuration
    display_configuration
    
    log_success "✅ System initialization completed successfully!"
    log_info "🚀 Starting application..."
    echo ""
    
    # Execute the main command
    exec "$@"
}

# Run main function
main "$@"