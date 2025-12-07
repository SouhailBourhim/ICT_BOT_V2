# ⚠️ Python 3.14 Compatibility Issue

## Problem
You're running **Python 3.14.0**, which is very new (released recently). ChromaDB and some of its dependencies (specifically Pydantic v1) are not yet compatible with Python 3.14.

**Error**: `pydantic.v1.errors.ConfigError: unable to infer type for attribute "chroma_server_nofile"`

## ✅ Solutions (Choose One)

### Solution 1: Use Python 3.12 (Recommended - 5 minutes)

Python 3.12 is stable and fully supported by all dependencies.

```bash
# Install Python 3.12
brew install python@3.12

# Navigate to project
cd inpt-rag-assistant

# Create new virtual environment with Python 3.12
python3.12 -m venv venv312

# Activate it
source venv312/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download NLTK data
python3.12 -c "import nltk; nltk.download('punkt')"

# Setup database
python3.12 scripts/setup_database.py

# Start Ollama (if not running)
ollama serve &

# Run the app
streamlit run app/streamlit_app.py
```

### Solution 2: Use Docker (Easiest - 2 minutes)

Docker uses Python 3.11 internally, avoiding the compatibility issue.

```bash
cd inpt-rag-assistant/docker

# Start everything
docker-compose up -d

# Check logs
docker-compose logs -f app

# Access the app
open http://localhost:8501
```

### Solution 3: Downgrade Python (Not Recommended)

You can downgrade your system Python, but this might affect other projects.

```bash
# Use pyenv to manage multiple Python versions
brew install pyenv

# Install Python 3.12
pyenv install 3.12.0

# Set it for this directory
cd inpt-rag-assistant
pyenv local 3.12.0

# Recreate venv
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Solution 4: Wait for ChromaDB Update

ChromaDB team is working on Python 3.14 support. Track progress:
- https://github.com/chroma-core/chroma/issues

## Current Status

✅ **Working**:
- Ollama installed and running
- Project structure complete
- Code reviewed and approved
- Documentation ready

❌ **Blocked**:
- ChromaDB import fails on Python 3.14
- Cannot start Streamlit app
- Cannot initialize database

## Recommended Action

**Use Solution 1 (Python 3.12)** - It's the most straightforward and will work immediately.

## After Fixing

Once you have Python 3.12 set up, run:

```bash
# Quick start
cd inpt-rag-assistant
source venv312/bin/activate

# Setup (first time only)
python scripts/setup_database.py

# Add some test documents
cp ~/Documents/*.pdf data/documents/

# Ingest documents
python scripts/ingest_documents.py data/documents --recursive

# Start app
streamlit run app/streamlit_app.py
```

The app will open at: **http://localhost:8501**

## Need Help?

If you encounter issues:
1. Check `logs/` directory for error logs
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Check Python version: `python --version` (should be 3.12.x)
4. Verify dependencies: `pip list | grep -E "(chromadb|streamlit|sentence)"`

---

**Note**: Python 3.14 is very new (released in October 2024). Most ML/AI libraries need time to catch up with new Python versions. Python 3.12 is the current stable choice for production ML applications.
