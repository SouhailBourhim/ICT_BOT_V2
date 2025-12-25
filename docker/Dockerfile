# Dockerfile for INPT RAG Assistant
FROM python:3.11-slim

# Metadata
LABEL maintainer="INPT Smart ICT"
LABEL description="Educational RAG Assistant for INPT"
LABEL version="2.0.0"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Working directory
WORKDIR /app

# Install system dependencies (optimized layer for caching)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies (optimized for caching)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data (separate layer for caching)
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"

# Create necessary directories with proper permissions
RUN mkdir -p data/documents data/processed data/conversations data/embeddings \
    database/chroma_db logs \
    && chmod -R 755 data database logs

# Copy source code (separate from dependencies for better caching)
COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/

# Copy configuration files
COPY .env.example .env.example

# Expose Streamlit port
EXPOSE 8501

# Health check for current application structure
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Copy and set up entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set proper entrypoint and command for current application
ENTRYPOINT ["/entrypoint.sh"]
CMD ["streamlit", "run", "app/chat.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]