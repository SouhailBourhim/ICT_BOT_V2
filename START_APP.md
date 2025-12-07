# 🚨 Python 3.14 Compatibility Issue

## Issue
ChromaDB is not yet fully compatible with Python 3.14. The Pydantic v1 dependency causes errors.

## Quick Solutions

### Option 1: Use Python 3.11 or 3.12 (Recommended)
```bash
# Install Python 3.12 via Homebrew
brew install python@3.12

# Create new venv with Python 3.12
python3.12 -m venv venv312
source venv312/bin/activate
pip install -r requirements.txt

# Run the app
streamlit run app/streamlit_app.py
```

### Option 2: Use Docker (Easiest)
```bash
cd docker
docker-compose up
```
Access at: http://localhost:8501

### Option 3: Wait for ChromaDB Update
ChromaDB team is working on Python 3.14 support. Check:
https://github.com/chroma-core/chroma/issues

## Current Status
- ✅ Ollama: Running
- ✅ Dependencies: Mostly installed
- ❌ ChromaDB: Python 3.14 incompatibility
- ✅ Streamlit: Installed and ready

## Temporary Workaround
You can still test the UI without the database:
```bash
# Start just the UI (limited functionality)
source venv/bin/activate
streamlit run app/streamlit_app.py
```

The chat won't work without ChromaDB, but you can see the interface.
