# 🚀 Quick Start Guide - INPT RAG Assistant

## Prerequisites

- Python 3.11+ installed
- Ollama installed ([https://ollama.ai](https://ollama.ai))
- 8GB RAM minimum
- 10GB disk space

## Installation (5 minutes)

### 1. Setup Python Environment

```bash
# Navigate to project
cd inpt-rag-assistant

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip
```

### 2. Install Dependencies

```bash
# Install all packages
pip install -r requirements.txt

# Download NLTK data (for tokenization)
python3 -c "import nltk; nltk.download('punkt')"
```

### 3. Setup Ollama

```bash
# Start Ollama service (in a separate terminal)
ollama serve

# Pull required models (in another terminal)
ollama pull llama3.2:3b        # LLM for responses
ollama pull nomic-embed-text   # For embeddings (optional, uses sentence-transformers by default)
```

### 4. Initialize Database

```bash
# Create database structure
python3 scripts/setup_database.py
```

## Usage

### Step 1: Add Documents

Place your documents in the `data/documents/` folder:
```bash
# Example: Copy your PDFs, TXT, MD, or DOCX files
cp ~/my-courses/*.pdf data/documents/
```

### Step 2: Ingest Documents

```bash
# Ingest all documents
python3 scripts/ingest_documents.py data/documents --recursive

# Or ingest a single file
python3 scripts/ingest_documents.py data/documents/cours_iot.pdf

# Check stats
python3 scripts/ingest_documents.py --stats
```

### Step 3: Launch the App

```bash
# Start Streamlit app
streamlit run app/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## 🎯 First Test

1. **Upload a document** via the "📤 Upload Documents" page
2. **Go to Chat** page
3. **Ask a question** about your documents
4. **View Analytics** to see system stats

## Example Questions (French)

- "Qu'est-ce que l'Internet des Objets ?"
- "Comment fonctionne un capteur IoT ?"
- "Quels sont les protocoles de sécurité pour l'IoT ?"
- "Explique-moi le concept de cloud computing"

## 🐳 Docker Alternative

If you prefer Docker:

```bash
cd docker
docker-compose up -d
```

Access the app at `http://localhost:8501`

## Troubleshooting

### Issue: "Module not found"
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Ollama connection error"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### Issue: "ChromaDB error"
```bash
# Reset the database
python3 scripts/setup_database.py

# Re-ingest documents
python3 scripts/ingest_documents.py data/documents --reset --recursive
```

### Issue: "Out of memory"
```bash
# Reduce batch size in .env
BATCH_SIZE=8
CHUNK_SIZE=500
```

## Configuration

Edit `.env` file to customize:

```bash
# Copy example
cp .env.example .env

# Edit settings
nano .env
```

Key settings:
- `OLLAMA_MODEL`: Change LLM model (llama3.2:3b, mistral, etc.)
- `CHUNK_SIZE`: Adjust chunk size (default: 1000)
- `TOP_K_RETRIEVAL`: Number of documents to retrieve (default: 10)
- `SEMANTIC_WEIGHT`: Balance between semantic and keyword search (default: 0.7)

## Performance Tips

1. **Use GPU if available**: Ollama will automatically use GPU
2. **Adjust chunk size**: Smaller chunks = faster, larger = more context
3. **Tune retrieval**: Increase `TOP_K_RETRIEVAL` for better results
4. **Cache embeddings**: Embeddings are cached in ChromaDB

## Next Steps

- Add more documents to `data/documents/`
- Customize prompts in `src/llm/prompt_templates.py`
- Adjust search weights in `.env`
- Monitor performance in Analytics page

## Support

For issues or questions:
- Check `REVIEW_FIXES.md` for known issues
- Review logs in `logs/` directory
- Check ChromaDB status: `python3 scripts/ingest_documents.py --stats`

---

**Happy RAG-ing! 🎓**
