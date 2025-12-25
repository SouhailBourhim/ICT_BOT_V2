# 🐳 Docker Deployment Guide - INPT RAG Assistant

Complete Docker setup for deploying the INPT RAG Assistant on any machine.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Document Ingestion](#document-ingestion)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

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

# Start services
cd docker
docker-compose up -d

# Check logs
docker-compose logs -f

# Access the app
open http://localhost:8501
```

That's it! The app will be available at **http://localhost:8501**

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
   - Auto-reload on code changes
   - Mounted volumes for data

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

## ⚙️ Configuration

### Environment Variables

Edit `docker-compose.yml` or create `.env` file:

```bash
# LLM Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=120

# Embedding Configuration
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384
BATCH_SIZE=32

# Chunking Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MIN_CHUNK_SIZE=100

# Retrieval Configuration
TOP_K_RETRIEVAL=10
SIMILARITY_THRESHOLD=0.7
SEMANTIC_WEIGHT=0.7
BM25_WEIGHT=0.3

# Application Configuration
LOG_LEVEL=INFO
LANGUAGE=fr
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

## 🐛 Troubleshooting

### App Won't Start

```bash
# Check logs
docker-compose logs rag-app

# Check if Ollama is ready
docker-compose logs ollama

# Restart services
docker-compose restart
```

### Ollama Connection Error

```bash
# Check Ollama health
curl http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama

# Check network
docker-compose exec rag-app ping ollama
```

### Out of Memory

```bash
# Check resource usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > 8GB+

# Or use production config with limits
docker-compose -f docker-compose.prod.yml up
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Or manually
docker-compose exec rag-app rm -rf database/chroma_db/*
docker-compose exec rag-app python scripts/setup_database.py
```

### Port Already in Use

```bash
# Change ports in docker-compose.yml
ports:
  - "8502:8501"  # Use 8502 instead of 8501

# Or stop conflicting service
lsof -ti:8501 | xargs kill
```

---

## 📊 Performance Tuning

### For Better Performance

```yaml
# In docker-compose.yml
services:
  rag-app:
    environment:
      - BATCH_SIZE=64  # Increase for faster ingestion
      - CHUNK_SIZE=500  # Smaller chunks = faster search
      - TOP_K_RETRIEVAL=5  # Fewer results = faster response
```

### For Better Quality

```yaml
services:
  rag-app:
    environment:
      - CHUNK_SIZE=1500  # Larger chunks = more context
      - CHUNK_OVERLAP=300  # More overlap = better continuity
      - TOP_K_RETRIEVAL=15  # More results = better answers
      - SEMANTIC_WEIGHT=0.8  # More semantic = better understanding
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
├── Dockerfile                      # Main app image
├── Dockerfile.ingestion            # Ingestion-only image
├── docker-compose.yml              # Development setup
├── docker-compose.prod.yml         # Production setup
├── docker-compose.ingestion.yml    # Ingestion setup
├── entrypoint.sh                   # App entrypoint
├── entrypoint-ingestion.sh         # Ingestion entrypoint
├── .dockerignore                   # Files to exclude
├── nginx.conf                      # Nginx config (optional)
└── README.md                       # This file
```

---

## 🆘 Getting Help

- **Documentation**: See main README.md
- **Issues**: https://github.com/SouhailBourhim/ICT_BOT_V2/issues
- **Logs**: `docker-compose logs -f`
- **Health**: `docker-compose ps`

---

**🎉 Happy Dockerizing!**
