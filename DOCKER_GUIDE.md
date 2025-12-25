# 🐳 Complete Docker Guide - INPT RAG Assistant

## 🎯 Use Cases

### 1. **Run on Any PC** ✅
Deploy the complete application on any machine with Docker installed.

### 2. **Document Ingestion on Powerful PC** ✅
Process large document batches on a high-performance machine, then transfer the database.

### 3. **Production Deployment** ✅
Deploy with resource limits, health checks, and security hardening.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Clone Repository
```bash
git clone https://github.com/SouhailBourhim/ICT_BOT_V2.git
cd ICT_BOT_V2/docker
```

### Step 2: Start Services
```bash
./docker-run.sh
# Select option 1 (Development)
```

### Step 3: Access App
Open browser: **http://localhost:8501**

**That's it!** 🎉

---

## 📥 Document Ingestion Workflow

### Scenario: Process Documents on Powerful PC

#### On Powerful PC (for ingestion):

```bash
# 1. Clone repository
git clone https://github.com/SouhailBourhim/ICT_BOT_V2.git
cd ICT_BOT_V2

# 2. Add your documents
cp /path/to/your/documents/* data/documents/

# 3. Run ingestion
cd docker
docker-compose -f docker-compose.ingestion.yml up

# 4. Wait for completion (check logs)
docker-compose -f docker-compose.ingestion.yml logs -f ingestion

# 5. Package the database
cd ..
tar -czf database.tar.gz database/
```

#### Transfer to Another PC:

```bash
# 1. Copy database archive to target PC
scp database.tar.gz user@target-pc:/path/to/ICT_BOT_V2/

# 2. On target PC, extract database
cd /path/to/ICT_BOT_V2
tar -xzf database.tar.gz

# 3. Start the application
cd docker
docker-compose up -d

# 4. Access at http://localhost:8501
```

**Result**: Instant access to all processed documents! 🚀

---

## 📋 All Deployment Options

### Option 1: Development (Default)
**Best for**: Local development, testing

```bash
cd docker
docker-compose up -d
```

**Features**:
- Hot reload
- Debug logging
- Easy access to logs
- Volume mounts for live editing

**Access**: http://localhost:8501

---

### Option 2: Production
**Best for**: Production deployment, public access

```bash
cd docker
docker-compose -f docker-compose.prod.yml up -d
```

**Features**:
- Resource limits (CPU/Memory)
- Health checks
- Auto-restart
- Security hardening
- Read-only data mounts
- Optional Nginx reverse proxy

**Access**: http://localhost:8501 (or via Nginx on port 80)

---

### Option 3: Ingestion Only
**Best for**: Batch document processing

```bash
cd docker

# Add documents first
cp /path/to/docs/* ../data/documents/

# Run ingestion
docker-compose -f docker-compose.ingestion.yml up
```

**Features**:
- Optimized for batch processing
- Runs once and exits
- Minimal resource usage
- Portable database output

---

### Option 4: Custom Build
**Best for**: Custom configurations

```bash
# Build custom image
docker build -f docker/Dockerfile -t my-rag-app ..

# Run with custom settings
docker run -p 8501:8501 \
  -e CHUNK_SIZE=500 \
  -e BATCH_SIZE=64 \
  -v ./data:/app/data \
  -v ./database:/app/database \
  my-rag-app
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in docker directory:

```bash
# LLM Settings
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://ollama:11434

# Embedding Settings
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
BATCH_SIZE=32

# Chunking Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Retrieval Settings
TOP_K_RETRIEVAL=10
SEMANTIC_WEIGHT=0.7
BM25_WEIGHT=0.3

# Application Settings
LOG_LEVEL=INFO
LANGUAGE=fr
```

Then use it:
```bash
docker-compose --env-file .env up -d
```

---

## 📊 Performance Optimization

### For Faster Ingestion

```yaml
environment:
  - BATCH_SIZE=64        # Process more documents at once
  - CHUNK_SIZE=500       # Smaller chunks = faster processing
  - TOP_K_RETRIEVAL=5    # Fewer results = faster search
```

### For Better Quality

```yaml
environment:
  - CHUNK_SIZE=1500      # Larger chunks = more context
  - CHUNK_OVERLAP=300    # More overlap = better continuity
  - TOP_K_RETRIEVAL=15   # More results = better answers
  - SEMANTIC_WEIGHT=0.8  # Prioritize semantic understanding
```

### For Resource-Constrained Systems

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 2G
environment:
  - BATCH_SIZE=8
  - CHUNK_SIZE=500
```

---

## 🔄 Database Transfer Guide

### Export Database from PC A

```bash
# On PC A (after ingestion)
cd ICT_BOT_V2

# Stop services
cd docker && docker-compose down

# Package database
cd ..
tar -czf rag-database-$(date +%Y%m%d).tar.gz database/

# Optional: Include documents
tar -czf rag-complete-$(date +%Y%m%d).tar.gz database/ data/documents/
```

### Import Database on PC B

```bash
# On PC B
cd ICT_BOT_V2

# Extract database
tar -xzf rag-database-20251207.tar.gz

# Verify
ls -lh database/chroma_db/

# Start services
cd docker && docker-compose up -d

# Verify ingestion
docker-compose exec rag-app python scripts/ingest_documents.py --stats
```

---

## 🐛 Troubleshooting

### Issue: "Port 8501 already in use"

```bash
# Option 1: Stop conflicting service
lsof -ti:8501 | xargs kill

# Option 2: Change port in docker-compose.yml
ports:
  - "8502:8501"
```

### Issue: "Ollama not responding"

```bash
# Check Ollama logs
docker-compose logs ollama

# Restart Ollama
docker-compose restart ollama

# Test connection
curl http://localhost:11434/api/tags
```

### Issue: "Out of memory"

```bash
# Check resource usage
docker stats

# Increase Docker memory (Docker Desktop)
# Settings > Resources > Memory > 8GB+

# Or use production config with limits
docker-compose -f docker-compose.prod.yml up -d
```

### Issue: "Database not found"

```bash
# Initialize database
docker-compose exec rag-app python scripts/setup_database.py

# Or reset everything
docker-compose down -v
docker-compose up -d
```

---

## 📦 Docker Images

### Pre-built Images (Coming Soon)

```bash
# Pull from Docker Hub
docker pull souhailbourhim/inpt-rag-app:latest

# Run
docker run -p 8501:8501 souhailbourhim/inpt-rag-app:latest
```

### Build Your Own

```bash
# App image
docker build -f docker/Dockerfile -t inpt-rag-app:latest .

# Ingestion image
docker build -f docker/Dockerfile.ingestion -t inpt-rag-ingestion:latest .

# Push to your registry
docker tag inpt-rag-app:latest your-registry/inpt-rag-app:latest
docker push your-registry/inpt-rag-app:latest
```

---

## 🌐 Cloud Deployment

### AWS ECS

```bash
# 1. Push image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
docker tag inpt-rag-app:latest your-account.dkr.ecr.us-east-1.amazonaws.com/inpt-rag-app:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/inpt-rag-app:latest

# 2. Create ECS task definition using docker-compose.prod.yml
# 3. Deploy to ECS cluster
```

### Google Cloud Run

```bash
# 1. Build and push
gcloud builds submit --tag gcr.io/your-project/inpt-rag-app

# 2. Deploy
gcloud run deploy inpt-rag-app \
  --image gcr.io/your-project/inpt-rag-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# 1. Push to ACR
az acr build --registry your-registry --image inpt-rag-app:latest .

# 2. Deploy
az container create \
  --resource-group your-rg \
  --name inpt-rag-app \
  --image your-registry.azurecr.io/inpt-rag-app:latest \
  --ports 8501
```

---

## 📝 Files Reference

```
docker/
├── Dockerfile                      # Main application image
├── Dockerfile.ingestion            # Ingestion-only image
├── docker-compose.yml              # Development setup
├── docker-compose.prod.yml         # Production setup
├── docker-compose.ingestion.yml    # Ingestion setup
├── entrypoint.sh                   # App startup script
├── entrypoint-ingestion.sh         # Ingestion startup script
├── docker-run.sh                   # Quick start script
├── .dockerignore                   # Files to exclude from build
├── nginx.conf                      # Nginx reverse proxy config
└── README.md                       # Detailed Docker documentation
```

---

## ✅ Checklist for Production

- [ ] Use `docker-compose.prod.yml`
- [ ] Set resource limits
- [ ] Enable health checks
- [ ] Use read-only volumes for data
- [ ] Set up Nginx reverse proxy
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Set up automated backups
- [ ] Test disaster recovery
- [ ] Document deployment process
- [ ] Set up CI/CD pipeline

---

## 🎓 Examples

### Example 1: Quick Test

```bash
cd docker
./docker-run.sh
# Select 1 (Development)
# Open http://localhost:8501
```

### Example 2: Process 1000 PDFs

```bash
# Copy PDFs
cp ~/research-papers/*.pdf ../data/documents/

# Run ingestion
docker-compose -f docker-compose.ingestion.yml up

# Check results
docker-compose -f docker-compose.ingestion.yml logs ingestion
```

### Example 3: Production with Nginx

```bash
# Start with Nginx
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d

# Access via Nginx
open http://localhost
```

---

## 🆘 Support

- **Docker Issues**: See `docker/README.md`
- **Application Issues**: See main `README.md`
- **GitHub Issues**: https://github.com/SouhailBourhim/ICT_BOT_V2/issues

---

**🐳 Docker makes deployment easy! Enjoy!**
