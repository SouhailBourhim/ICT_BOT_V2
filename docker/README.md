# 🐳 Docker Deployment Guide - INPT RAG Assistant

Complete Docker setup for deploying the INPT RAG Assistant with all enhanced features including math rendering, analytics dashboard, and conversation management.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Document Ingestion](#document-ingestion)
5. [Configuration](#configuration)
6. [Enhanced Features](#enhanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Deployment Scripts](#deployment-scripts)

---

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB disk space

### Start the Application

```bash
# Clone the repository
git clone https://github.com/SouhailBourhim/ICT_BOT_V2.git
cd ICT_BOT_V2

# Start services using the deployment script
cd docker
./docker-run.sh

# Or start manually
docker-compose up -d

# Check logs
docker-compose logs -f

# Access the app
open http://localhost:8501
```

That's it! The app will be available at **http://localhost:8501** with all enhanced features including:
- 📊 **Analytics Dashboard** - View usage metrics and conversation analytics
- 🧮 **Math Rendering** - LaTeX and mathematical formula support
- 💬 **Enhanced Chat Interface** - Improved conversation management
- 📄 **Advanced Document Processing** - Support for multiple formats with contextual headers

---

## 💻 Development Setup

### Using docker-compose.yml (Default)

```bash
cd docker

# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f rag-app

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Services Included

1. **Ollama** (LLM Service)
   - Port: 11434
   - Models: Auto-downloaded on first run
   - Volume: Persistent model storage

2. **RAG App** (Streamlit)
   - Port: 8501
   - Entry Point: `app/chat.py` (updated from legacy streamlit_app.py)
   - Auto-reload on code changes
   - Mounted volumes for data
   - Enhanced features: Math rendering, Analytics, Conversation management

---

## 🏭 Production Deployment

### Using docker-compose.prod.yml

```bash
cd docker

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# With Nginx reverse proxy
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Production Features

- ✅ Resource limits (CPU/Memory)
- ✅ Health checks
- ✅ Auto-restart policies
- ✅ Read-only data mounts
- ✅ Security hardening
- ✅ Optional Nginx reverse proxy

---

## 📥 Document Ingestion

### Option 1: Using Ingestion Service

Perfect for batch processing on a powerful machine!

```bash
cd docker

# 1. Place your documents
mkdir -p ../data/documents
cp /path/to/your/docs/* ../data/documents/

# 2. Run ingestion
docker-compose -f docker-compose.ingestion.yml up

# 3. Check results
docker-compose -f docker-compose.ingestion.yml logs ingestion

# 4. Cleanup
docker-compose -f docker-compose.ingestion.yml down
```

### Option 2: Manual Ingestion in Running Container

```bash
# Copy documents to running container
docker cp /path/to/docs/. inpt-rag-app:/app/data/documents/

# Run ingestion inside container
docker exec inpt-rag-app python scripts/ingest_documents.py data/documents --recursive

# Check stats
docker exec inpt-rag-app python scripts/ingest_documents.py --stats
```

### Option 3: Build Ingestion Image Separately

```bash
# Build ingestion image
docker build -f docker/Dockerfile.ingestion -t inpt-rag-ingestion ..

# Run ingestion
docker run -v /path/to/docs:/app/data/documents:ro \
           -v ./database:/app/database \
           inpt-rag-ingestion

# With custom settings
docker run -e CHUNK_SIZE=500 \
           -e BATCH_SIZE=16 \
           -v /path/to/docs:/app/data/documents:ro \
           -v ./database:/app/database \
           inpt-rag-ingestion
```

---

## 🚀 Enhanced Features

The containerized application includes all the latest enhancements:

### 📊 Analytics Dashboard
Access comprehensive analytics at `/analytics` page:
- Conversation metrics and trends
- Document usage statistics
- User interaction patterns
- Performance monitoring

```bash
# Access analytics dashboard
open http://localhost:8501/analytics
```

### 🧮 Math Rendering
Full LaTeX and mathematical formula support:
- Real-time LaTeX rendering with KaTeX
- Mathematical expressions in conversations
- Formula display in document content
- Support for complex equations and symbols

### 💬 Enhanced Chat Interface
Improved conversation experience:
- Persistent conversation history
- Context-aware responses
- Enhanced message formatting
- Real-time typing indicators

### 📄 Advanced Document Processing
Enhanced document ingestion pipeline:
- Contextual header generation
- Improved chunking strategies
- Multi-format support (PDF, DOCX, TXT, MD)
- Metadata extraction and indexing

---

## ⚙️ Configuration

### Environment Variables

Edit `docker-compose.yml` or create `.env` file:

```bash
# Project Configuration
PROJECT_NAME="Assistant Éducatif RAG - INPT Smart ICT"
VERSION=1.0.0
LANGUAGE=fr

# LLM Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT=180
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384
BATCH_SIZE=32

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MIN_CHUNK_SIZE=100
SUPPORTED_FORMATS=[".pdf", ".txt", ".md", ".docx"]

# Retrieval Configuration
TOP_K_RETRIEVAL=7
SIMILARITY_THRESHOLD=0.4
SEMANTIC_WEIGHT=0.7
BM25_WEIGHT=0.3
RERANK_TOP_K=3

# Analytics & Features
ENABLE_TRACKING=true
ENABLE_METRICS=true
ENABLE_SPELLING_CORRECTION=true
ENABLE_QUERY_EXPANSION=true

# Conversation Management
MAX_CONVERSATION_HISTORY=6
CONTEXT_WINDOW_SIZE=4096

# Application Configuration
LOG_LEVEL=INFO
STREAMLIT_PAGE_TITLE="Assistant RAG - INPT Smart ICT"
STREAMLIT_PAGE_ICON=🎓
STREAMLIT_LAYOUT=wide
```

### Volume Mounts

```yaml
volumes:
  # Documents (read-only in production)
  - ../data/documents:/app/data/documents:ro
  
  # Database (persistent)
  - ../database:/app/database
  
  # Logs
  - ../logs:/app/logs
  
  # Ollama models (persistent)
  - ollama_data:/root/.ollama
```

---

## 🔧 Common Commands

### Container Management

```bash
# List running containers
docker-compose ps

# Restart a service
docker-compose restart rag-app

# View logs
docker-compose logs -f rag-app

# Execute command in container
docker-compose exec rag-app bash

# Check resource usage
docker stats
```

### Database Management

```bash
# Initialize database
docker-compose exec rag-app python scripts/setup_database.py

# Check database stats
docker-compose exec rag-app python scripts/ingest_documents.py --stats

# Reset database
docker-compose exec rag-app python scripts/ingest_documents.py data/documents --reset
```

### Ollama Management

```bash
# List available models
docker-compose exec ollama ollama list

# Pull a new model
docker-compose exec ollama ollama pull llama3.2:3b

# Remove a model
docker-compose exec ollama ollama rm llama3.2:1b

# Check Ollama status
curl http://localhost:11434/api/tags
```

---

## 🚀 Deployment Scripts

### Quick Deployment Script

Use the provided deployment script for easy setup:

```bash
cd docker
./docker-run.sh
```

The script provides options for:
1. **Development Mode** - Full development environment with hot reload
2. **Production Mode** - Optimized production deployment with resource limits
3. **Ingestion Only** - Document processing only
4. **Custom Build** - Build custom images with specific configurations

### Manual Deployment Commands

```bash
# Development deployment
docker-compose up -d

# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With Nginx reverse proxy
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d

# Document ingestion only
docker-compose -f docker-compose.ingestion.yml up
```

### Health Checks and Monitoring

```bash
# Check service health
docker-compose ps

# Monitor logs in real-time
docker-compose logs -f

# Check specific service logs
docker-compose logs -f rag-app
docker-compose logs -f ollama

# Monitor resource usage
docker stats

# Test application health
curl http://localhost:8501/_stcore/health
curl http://localhost:11434/api/tags
```

---

## 🐛 Troubleshooting

### App Won't Start

```bash
# Check logs for detailed error information
docker-compose logs rag-app

# Check if Ollama is ready
docker-compose logs ollama

# Verify configuration
docker-compose config

# Restart services in correct order
docker-compose restart ollama
sleep 10
docker-compose restart rag-app
```

### Ollama Connection Error

```bash
# Check Ollama health
curl http://localhost:11434/api/tags

# Verify Ollama is running in container
docker-compose exec ollama ollama list

# Check network connectivity
docker-compose exec rag-app ping ollama

# Restart Ollama service
docker-compose restart ollama

# Check Ollama model availability
docker-compose exec ollama ollama show qwen2.5:3b
```

### Enhanced Features Not Working

```bash
# Check if analytics page is accessible
curl http://localhost:8501/analytics

# Verify math rendering dependencies
docker-compose exec rag-app python -c "import streamlit; print('Streamlit version:', streamlit.__version__)"

# Check conversation persistence
ls -la data/conversations/

# Verify document processing pipeline
docker-compose exec rag-app python scripts/ingest_documents.py --stats
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Monitor memory usage specifically
docker-compose exec rag-app free -h

# Check disk space
docker-compose exec rag-app df -h

# Optimize for better performance
# Edit docker-compose.yml:
environment:
  - BATCH_SIZE=16        # Reduce if memory constrained
  - CHUNK_SIZE=800       # Smaller chunks for faster processing
  - TOP_K_RETRIEVAL=5    # Fewer results for faster response
  - CACHE_ENABLED=true   # Enable caching
```

### Database and Storage Issues

```bash
# Check ChromaDB status
docker-compose exec rag-app ls -la database/chroma_db/

# Verify volume mounts
docker-compose exec rag-app ls -la /app/data/
docker-compose exec rag-app ls -la /app/database/

# Reset database if corrupted
docker-compose down
docker volume rm docker_ollama_data  # Only if needed
rm -rf database/chroma_db/*
docker-compose up -d

# Reinitialize database
docker-compose exec rag-app python scripts/setup_database.py
```

### Container Build Issues

```bash
# Clean build (removes cache)
docker-compose build --no-cache

# Check Dockerfile syntax
docker build -f docker/Dockerfile --dry-run .

# Build with verbose output
docker-compose build --progress=plain

# Check for dependency conflicts
docker-compose exec rag-app pip check
```

### Network and Port Issues

```bash
# Check if ports are available
lsof -ti:8501 | xargs kill  # Kill process using port 8501
lsof -ti:11434 | xargs kill # Kill process using port 11434

# Use different ports if needed
# Edit docker-compose.yml:
ports:
  - "8502:8501"  # Use 8502 instead of 8501
  - "11435:11434" # Use 11435 instead of 11434

# Check Docker network
docker network ls
docker network inspect docker_default
```

### Configuration Validation

```bash
# Validate environment configuration
docker-compose exec rag-app python -c "
from src.config.settings import validate_environment_configuration
results = validate_environment_configuration()
print('Environment type:', results['environment_type'])
print('Is valid:', results['is_valid'])
for error in results['errors']:
    print('Error:', error)
for warning in results['warnings']:
    print('Warning:', warning)
"

# Check all environment variables
docker-compose exec rag-app env | grep -E "(OLLAMA|EMBEDDING|CHUNK|LOG)"
```

---

## 🆘 Common Issues and Solutions

### Issue: "ModuleNotFoundError" in Container

**Symptoms**: Application fails to start with missing Python modules
**Solution**:
```bash
# Rebuild container with no cache
docker-compose build --no-cache

# Check if all dependencies are installed
docker-compose exec rag-app pip list | grep -E "(streamlit|chromadb|sentence)"

# Verify requirements.txt is up to date
docker-compose exec rag-app pip check
```

### Issue: Analytics Dashboard Not Loading

**Symptoms**: `/analytics` page shows 404 or fails to load
**Solution**:
```bash
# Check if analytics module is available
docker-compose exec rag-app python -c "from app.pages.analytics import main; print('Analytics module OK')"

# Verify Streamlit configuration
docker-compose exec rag-app streamlit --version

# Check logs for specific errors
docker-compose logs rag-app | grep -i analytics
```

### Issue: Math Rendering Not Working

**Symptoms**: LaTeX formulas not displaying correctly
**Solution**:
```bash
# Check if math renderer is available
docker-compose exec rag-app python -c "from app.components.math_renderer import MathRenderer; print('Math renderer OK')"

# Verify browser JavaScript is enabled
# Check browser console for KaTeX errors

# Test math rendering directly
curl http://localhost:8501/_stcore/health
```

### Issue: Conversation History Not Persisting

**Symptoms**: Conversations lost after container restart
**Solution**:
```bash
# Check volume mounts
docker-compose exec rag-app ls -la /app/data/conversations/

# Verify conversation manager
docker-compose exec rag-app python -c "from src.conversation.manager import ConversationManager; print('Conversation manager OK')"

# Check file permissions
docker-compose exec rag-app ls -la /app/data/
```

### Issue: Document Processing Fails

**Symptoms**: Documents not being processed or indexed
**Solution**:
```bash
# Check document processing pipeline
docker-compose exec rag-app python -c "from src.document_processing.parser import DocumentParser; print('Parser OK')"

# Verify supported formats
docker-compose exec rag-app python -c "from src.config.settings import settings; print('Supported formats:', settings.SUPPORTED_FORMATS)"

# Test document ingestion
docker-compose exec rag-app python scripts/ingest_documents.py --help
```

### Issue: High Memory Usage

**Symptoms**: Container using excessive memory
**Solution**:
```bash
# Monitor memory usage
docker stats --no-stream

# Optimize configuration for lower memory
# Edit docker-compose.yml environment:
environment:
  - BATCH_SIZE=8          # Reduce batch size
  - CHUNK_SIZE=500        # Smaller chunks
  - TOP_K_RETRIEVAL=3     # Fewer results
  - CACHE_ENABLED=false   # Disable caching if needed

# Set memory limits in production
deploy:
  resources:
    limits:
      memory: 2G
```

### Issue: Slow Response Times

**Symptoms**: Application responds slowly to queries
**Solution**:
```bash
# Check Ollama model performance
docker-compose exec ollama ollama show qwen2.5:3b

# Optimize retrieval settings
environment:
  - TOP_K_RETRIEVAL=5     # Reduce results
  - SIMILARITY_THRESHOLD=0.5  # Higher threshold
  - CACHE_ENABLED=true    # Enable caching

# Monitor resource usage
docker stats
```

---

## 📊 Performance Tuning

### For Better Performance

```yaml
# In docker-compose.yml
services:
  rag-app:
    environment:
      - BATCH_SIZE=64           # Increase for faster ingestion
      - CHUNK_SIZE=800          # Smaller chunks = faster search
      - TOP_K_RETRIEVAL=5       # Fewer results = faster response
      - CACHE_ENABLED=true      # Enable caching
      - CACHE_TTL=7200          # Longer cache duration
      - MAX_WORKERS=6           # More parallel workers
      - RERANK_TOP_K=2          # Fewer reranked results
```

### For Better Quality

```yaml
services:
  rag-app:
    environment:
      - CHUNK_SIZE=1200         # Larger chunks = more context
      - CHUNK_OVERLAP=300       # More overlap = better continuity
      - TOP_K_RETRIEVAL=10      # More results = better answers
      - SEMANTIC_WEIGHT=0.8     # More semantic = better understanding
      - RERANK_TOP_K=5          # More reranked results
      - SIMILARITY_THRESHOLD=0.3 # Lower threshold = more results
```

### For Resource-Constrained Systems

```yaml
services:
  rag-app:
    environment:
      - BATCH_SIZE=16           # Smaller batches
      - CHUNK_SIZE=600          # Smaller chunks
      - TOP_K_RETRIEVAL=3       # Fewer results
      - MAX_WORKERS=2           # Fewer workers
      - CACHE_ENABLED=false     # Disable caching to save memory
      - ENABLE_TRACKING=false   # Disable analytics to save resources
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1.5G
```

---

## 🔒 Security Best Practices

### Production Checklist

- [ ] Use `docker-compose.prod.yml`
- [ ] Set read-only volumes for data
- [ ] Enable XSRF protection
- [ ] Use Nginx reverse proxy
- [ ] Set up SSL/TLS certificates
- [ ] Limit resource usage
- [ ] Enable health checks
- [ ] Use secrets for sensitive data
- [ ] Regular security updates

### Example with Secrets

```yaml
services:
  rag-app:
    secrets:
      - ollama_api_key
    environment:
      - OLLAMA_API_KEY_FILE=/run/secrets/ollama_api_key

secrets:
  ollama_api_key:
    file: ./secrets/ollama_api_key.txt
```

---

## 📦 Building Custom Images

### Build App Image

```bash
# Build
docker build -f docker/Dockerfile -t inpt-rag-app:latest ..

# Run
docker run -p 8501:8501 \
           -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
           inpt-rag-app:latest
```

### Build Ingestion Image

```bash
# Build
docker build -f docker/Dockerfile.ingestion -t inpt-rag-ingestion:latest ..

# Run
docker run -v /path/to/docs:/app/data/documents \
           -v ./database:/app/database \
           inpt-rag-ingestion:latest
```

---

## 🌐 Deploy to Cloud

### Docker Hub

```bash
# Tag image
docker tag inpt-rag-app:latest yourusername/inpt-rag-app:latest

# Push to Docker Hub
docker push yourusername/inpt-rag-app:latest

# Pull on another machine
docker pull yourusername/inpt-rag-app:latest
```

### AWS ECS / Azure Container Instances / Google Cloud Run

Use `docker-compose.prod.yml` as a base and adapt for your cloud provider.

---

## 📝 Files Overview

```
docker/
├── Dockerfile                      # Main app image (updated for app/chat.py)
├── Dockerfile.ingestion            # Ingestion-only image
├── docker-compose.yml              # Development setup (enhanced features)
├── docker-compose.prod.yml         # Production setup (with resource limits)
├── docker-compose.ingestion.yml    # Ingestion setup
├── docker-compose.dev.yml          # Development override (if exists)
├── entrypoint.sh                   # Enhanced app entrypoint with validation
├── entrypoint-ingestion.sh         # Ingestion entrypoint
├── docker-run.sh                   # Enhanced quick start script
├── .dockerignore                   # Files to exclude from build
├── nginx.conf                      # Nginx config (optional)
└── README.md                       # This comprehensive guide
```

### Key Updates in Current Version:
- ✅ **Updated Entry Point**: Now uses `app/chat.py` instead of legacy `streamlit_app.py`
- ✅ **Enhanced Features**: Full support for analytics, math rendering, conversation management
- ✅ **Improved Configuration**: Updated environment variables matching `settings.py`
- ✅ **Better Health Checks**: Comprehensive service monitoring and validation
- ✅ **Advanced Troubleshooting**: Detailed error resolution guides
- ✅ **Performance Optimization**: Tuned for both quality and speed

---

## 🔧 Advanced Troubleshooting Guide

### Diagnostic Commands

```bash
# Complete system health check
./docker-health-check.sh

# Or manual checks:
docker-compose ps                    # Service status
docker-compose logs --tail=50       # Recent logs
docker stats --no-stream           # Resource usage
curl -f http://localhost:8501/_stcore/health  # App health
curl -f http://localhost:11434/api/tags       # Ollama health
```

### Container Startup Issues

**Problem**: Container fails to start or exits immediately
```bash
# Check container logs
docker-compose logs rag-app

# Check for port conflicts
netstat -tulpn | grep -E "(8501|11434)"

# Verify Docker daemon
docker info

# Check disk space
df -h

# Rebuild with verbose output
docker-compose build --no-cache --progress=plain
```

### Service Communication Issues

**Problem**: RAG app cannot connect to Ollama
```bash
# Test network connectivity
docker-compose exec rag-app ping ollama

# Check Docker network
docker network ls
docker network inspect docker_default

# Verify service discovery
docker-compose exec rag-app nslookup ollama

# Check firewall rules (if applicable)
sudo ufw status
```

### Performance Degradation

**Problem**: Slow response times or high resource usage
```bash
# Monitor real-time performance
docker stats

# Check memory usage inside container
docker-compose exec rag-app free -h
docker-compose exec rag-app ps aux --sort=-%mem

# Analyze disk I/O
docker-compose exec rag-app iostat -x 1 5

# Check database performance
docker-compose exec rag-app python -c "
from src.storage.vector_store import VectorStore
store = VectorStore()
print('ChromaDB status:', store.get_collection_info())
"
```

### Data Persistence Issues

**Problem**: Data not persisting across container restarts
```bash
# Check volume mounts
docker-compose config | grep -A 5 volumes

# Verify volume permissions
docker-compose exec rag-app ls -la /app/data/
docker-compose exec rag-app ls -la /app/database/

# Check volume usage
docker volume ls
docker volume inspect docker_ollama_data

# Test write permissions
docker-compose exec rag-app touch /app/data/test_write
docker-compose exec rag-app rm /app/data/test_write
```

### Model and AI Issues

**Problem**: Ollama model not working or giving poor results
```bash
# Check available models
docker-compose exec ollama ollama list

# Verify model integrity
docker-compose exec ollama ollama show qwen2.5:3b

# Test model directly
docker-compose exec ollama ollama run qwen2.5:3b "Hello, how are you?"

# Check model performance
docker-compose exec rag-app python -c "
from src.llm.ollama_client import OllamaClient
client = OllamaClient()
response = client.generate('Test query')
print('Model response:', response)
"
```

### Configuration Validation

**Problem**: Application behaving unexpectedly due to configuration
```bash
# Validate all settings
docker-compose exec rag-app python -c "
from src.config.settings import settings, validate_environment_configuration
print('=== Configuration Validation ===')
results = validate_environment_configuration()
print(f'Environment: {results[\"environment_type\"]}')
print(f'Valid: {results[\"is_valid\"]}')
print(f'Docker: {results[\"is_docker\"]}')

if results['errors']:
    print('\\nErrors:')
    for error in results['errors']:
        print(f'  - {error}')

if results['warnings']:
    print('\\nWarnings:')
    for warning in results['warnings']:
        print(f'  - {warning}')

print('\\n=== Key Settings ===')
print(f'Ollama URL: {settings.OLLAMA_BASE_URL}')
print(f'Model: {settings.OLLAMA_MODEL}')
print(f'Embedding Model: {settings.EMBEDDING_MODEL}')
print(f'Chunk Size: {settings.CHUNK_SIZE}')
print(f'Top-K: {settings.TOP_K_RETRIEVAL}')
"

# Check environment variables
docker-compose exec rag-app env | sort | grep -E "(OLLAMA|EMBEDDING|CHUNK|PROJECT)"
```

### Database Recovery

**Problem**: ChromaDB corruption or data loss
```bash
# Backup current database
docker-compose exec rag-app tar -czf /tmp/chroma_backup.tar.gz -C /app/database chroma_db

# Reset ChromaDB
docker-compose down
rm -rf database/chroma_db/*
docker-compose up -d

# Reinitialize database
docker-compose exec rag-app python scripts/setup_database.py

# Re-ingest documents
docker-compose exec rag-app python scripts/ingest_documents.py data/documents --recursive

# Verify database integrity
docker-compose exec rag-app python -c "
from src.storage.vector_store import VectorStore
store = VectorStore()
collection = store.get_collection()
print(f'Documents in collection: {collection.count()}')
"
```

### Log Analysis

**Problem**: Need to analyze logs for issues
```bash
# Comprehensive log collection
mkdir -p troubleshooting_logs
docker-compose logs > troubleshooting_logs/docker-compose.log
docker-compose logs rag-app > troubleshooting_logs/rag-app.log
docker-compose logs ollama > troubleshooting_logs/ollama.log

# Search for specific errors
grep -i error troubleshooting_logs/*.log
grep -i "failed\|exception\|traceback" troubleshooting_logs/*.log

# Check application logs
docker-compose exec rag-app find /app/logs -name "*.log" -exec tail -n 50 {} \;

# Monitor logs in real-time
docker-compose logs -f --tail=100
```

### Emergency Recovery

**Problem**: Complete system failure or corruption
```bash
# Emergency reset (DESTRUCTIVE - will lose all data)
echo "⚠️  EMERGENCY RESET - THIS WILL DELETE ALL DATA"
read -p "Type 'RESET' to confirm: " confirm
if [ "$confirm" = "RESET" ]; then
    docker-compose down -v
    docker system prune -f
    docker volume prune -f
    rm -rf database/* data/conversations/* data/processed/* logs/*
    docker-compose up -d
    echo "✅ System reset complete"
else
    echo "❌ Reset cancelled"
fi
```

### Getting Help

When reporting issues, please include:

1. **System Information**:
   ```bash
   docker --version
   docker-compose --version
   uname -a
   ```

2. **Service Status**:
   ```bash
   docker-compose ps
   docker-compose config --services
   ```

3. **Recent Logs**:
   ```bash
   docker-compose logs --tail=100
   ```

4. **Configuration**:
   ```bash
   docker-compose exec rag-app python -c "from src.config.settings import settings; print(f'Model: {settings.OLLAMA_MODEL}, Chunk Size: {settings.CHUNK_SIZE}')"
   ```

5. **Resource Usage**:
   ```bash
   docker stats --no-stream
   ```

---

## 🆘 Getting Help

- **Documentation**: See main README.md
- **Issues**: https://github.com/SouhailBourhim/ICT_BOT_V2/issues
- **Logs**: `docker-compose logs -f`
- **Health**: `docker-compose ps`

---

**🎉 Happy Dockerizing!**
