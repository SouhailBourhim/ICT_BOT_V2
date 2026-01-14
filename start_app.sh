#!/bin/bash

# Startup script for INPT RAG Assistant
echo "🚀 Starting INPT RAG Assistant..."

# Activate virtual environment
source venv311/bin/activate

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import google.generativeai" 2>/dev/null; then
    echo "Installing Google Generative AI..."
    pip install google-generativeai
fi

# Test LLM providers
echo "🧪 Testing LLM providers..."
python3 test_llm_integration.py

# Start Streamlit app
echo "🌐 Starting Streamlit app..."
echo "Access the app at: http://localhost:8502"
streamlit run app/chat.py --server.port 8502