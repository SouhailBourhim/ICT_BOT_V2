# Dockerfile pour l'Assistant RAG INPT
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="INPT Smart ICT"
LABEL description="Assistant Éducatif RAG pour INPT"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Téléchargement des données NLTK
RUN python -c "import nltk; nltk.download('punkt', quiet=True)"

# Copie du code source
COPY . .

# Création d'un utilisateur non-root et des dossiers nécessaires
RUN groupadd --system app && \
    useradd --system --gid app --home-dir /app app && \
    mkdir -p data/documents data/conversations data/processed database/chroma_db logs && \
    chown -R app:app /app

# Port Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python scripts/healthcheck.py --timeout 3 || exit 1

# Script de démarrage
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["streamlit", "run", "app/chat.py", "--server.port=8501", "--server.address=0.0.0.0"]
