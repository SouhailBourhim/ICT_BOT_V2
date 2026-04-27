#!/bin/bash
set -e

echo "🚀 Démarrage de l'Assistant RAG INPT..."

OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
OLLAMA_URL="${OLLAMA_URL%/}"

# Attendre qu'Ollama soit disponible
echo "⏳ Attente du service Ollama..."
max_retries=30
counter=0

while ! curl -s "$OLLAMA_URL/api/tags" > /dev/null; do
    counter=$((counter + 1))
    if [ $counter -gt $max_retries ]; then
        echo "❌ Impossible de se connecter à Ollama ($OLLAMA_URL) après $max_retries tentatives"
        exit 1
    fi
    echo "  Tentative $counter/$max_retries..."
    sleep 2
done

echo "✅ Ollama est prêt!"

# Vérifier si le modèle est disponible
echo "🔍 Vérification du modèle LLM..."
if ! curl -s "$OLLAMA_URL/api/tags" | grep -q "$OLLAMA_MODEL"; then
    echo "⚠️  Modèle $OLLAMA_MODEL non trouvé"
    echo "📥 Téléchargement du modèle (cela peut prendre quelques minutes)..."
    
    # Télécharger le modèle
    curl -X POST "$OLLAMA_URL/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$OLLAMA_MODEL\"}" || {
        echo "❌ Échec du téléchargement du modèle"
        exit 1
    }
    
    echo "✅ Modèle téléchargé avec succès!"
else
    echo "✅ Modèle $OLLAMA_MODEL déjà disponible"
fi

# Initialiser les dossiers
echo "📁 Initialisation des dossiers..."
python -c "from src.config.settings import setup_directories; setup_directories()" || {
    echo "⚠️  Erreur lors de l'initialisation des dossiers (non bloquant)"
}

# Vérifier la base de données
if [ ! -d "/app/database/chroma_db" ] || [ -z "$(ls -A /app/database/chroma_db)" ]; then
    echo "⚠️  Base de données ChromaDB vide"
    echo "💡 Utilisez le script d'ingestion pour ajouter des documents:"
    echo "   docker-compose exec rag-app python scripts/ingest_documents.py data/documents"
fi

# Afficher les informations de configuration
echo ""
echo "📊 Configuration:"
echo "  - Modèle LLM: $OLLAMA_MODEL"
echo "  - URL Ollama: $OLLAMA_URL"
echo "  - Port Streamlit: 8501"
echo "  - Log level: $LOG_LEVEL"
echo ""
echo "✅ Système prêt! Lancement de l'application..."
echo ""

# Exécuter la commande
exec "$@"
